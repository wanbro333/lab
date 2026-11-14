from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .forms import ReceiptLineFormSet
from .models import Supplier, PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine
from .services import approve_purchase_order, post_receipt


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "contact_name", "phone", "is_active"]
    search_fields = ["code", "name", "contact_name", "phone"]
    list_filter = ["is_active"]


class DraftInlineMixin:
    """界面隐藏和服务端表单权限一起限制；并发由父级 Admin 加锁。"""
    def _editable(self, obj):
        return obj is None or obj.status == "draft"

    def has_add_permission(self, request, obj=None):
        return self._editable(obj) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return self._editable(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._editable(obj) and super().has_delete_permission(request, obj)


class PurchaseOrderLineInline(DraftInlineMixin, admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    fields = ["line_no", "item", "quantity", "unit_price", "amount_display", "remark"]
    readonly_fields = ["amount_display"]

    @admin.display(description="金额（元）")
    def amount_display(self, obj):
        return obj.amount if obj.pk else "保存后显示"


class DraftDocumentAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and (
            obj is None or obj.status == "draft"
        )

    def has_delete_permission(self, request, obj=None):
        # 单据保留供追溯。撤销/冲销要单独设计，不能靠删除历史实现。
        return False

    def run_service(self, request, queryset, service, label):
        # 每张单独立事务；失败不影响其他单据，消息逐张说明。
        for pk in queryset.order_by("pk").values_list("pk", flat=True):
            try:
                obj, changed = service(pk, request.user)
            except ValidationError as error:
                self.message_user(
                    request, f"ID {pk}：" + "；".join(error.messages),
                    level=messages.ERROR,
                )
            except PermissionDenied:
                self.message_user(request, "当前账号没有操作权限。", level=messages.ERROR)
            else:
                if changed:
                    self.log_change(request, obj, label)
                text = label if changed else "已处理，本次未重复记账"
                self.message_user(request, f"{obj.code}：{text}。")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(DraftDocumentAdmin):
    inlines = [PurchaseOrderLineInline]
    list_display = ["code", "supplier", "ordered_on", "expected_on", "status", "created_by"]
    search_fields = ["code", "supplier__name"]
    list_filter = ["status"]
    readonly_fields = [
        "created_by", "status", "approved_by", "approved_at", "created_at", "updated_at"
    ]
    actions = ["approve_selected"]

    def has_approve_permission(self, request):
        return request.user.has_perm("procurement.approve_purchaseorder") and (
            request.user.has_perm("procurement.change_purchaseorder")
        )

    @admin.action(description="批准所选采购单（单级审批）", permissions=["approve"])
    def approve_selected(self, request, queryset):
        self.run_service(request, queryset, approve_purchase_order, "已批准采购单")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST" and object_id is not None:
            with transaction.atomic():
                PurchaseOrder.objects.select_for_update().filter(
                    pk=unquote(object_id)
                ).first()
                return super().changeform_view(
                    request, object_id, form_url, extra_context
                )
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReceiptLineInline(DraftInlineMixin, admin.TabularInline):
    model = ReceiptLine
    formset = ReceiptLineFormSet
    extra = 1
    fields = [
        "line_no", "purchase_line", "location", "quantity",
        "manufacturer_batch_no", "manufactured_on", "expires_on", "remark",
    ]


@admin.register(Receipt)
class ReceiptAdmin(DraftDocumentAdmin):
    inlines = [ReceiptLineInline]
    list_display = ["code", "purchase_order", "received_on", "status", "received_by"]
    search_fields = ["code", "purchase_order__code"]
    list_filter = ["status", "received_on"]
    readonly_fields = [
        "received_by", "status", "posted_by", "posted_at", "created_at", "updated_at"
    ]
    actions = ["post_selected"]

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            # 建立明细后固定所属采购单，便于统一锁定该父单。
            fields.append("purchase_order")
        return fields

    def has_post_permission(self, request):
        return request.user.has_perm("procurement.post_receipt") and (
            request.user.has_perm("procurement.change_receipt")
        )

    @admin.action(description="确认所选收货单入库", permissions=["post"])
    def post_selected(self, request, queryset):
        self.run_service(request, queryset, post_receipt, "已确认入库")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST" and object_id is not None:
            with transaction.atomic():
                pk = unquote(object_id)
                order_id = Receipt.objects.filter(pk=pk).values_list(
                    "purchase_order_id", flat=True
                ).first()
                if order_id is not None:
                    PurchaseOrder.objects.select_for_update().get(pk=order_id)
                    Receipt.objects.select_for_update().get(pk=pk)
                return super().changeform_view(
                    request, object_id, form_url, extra_context
                )
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.received_by = request.user
        super().save_model(request, obj, form, change)
