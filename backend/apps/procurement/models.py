from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class Supplier(models.Model):
    code = models.CharField("供应商编码", max_length=40, unique=True)
    name = models.CharField("供应商名称", max_length=150)
    contact_name = models.CharField("联系人", max_length=50, blank=True)
    phone = models.CharField("联系电话", max_length=32, blank=True)
    address = models.CharField("地址", max_length=255, blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "供应商"
        verbose_name_plural = "供应商"

    def __str__(self):
        return f"{self.code} · {self.name}"

class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        SUBMITTED = "submitted", "待审批"
        APPROVED = "approved", "已批准"
        REJECTED = "rejected", "已驳回"
        CANCELLED = "cancelled", "已取消"

    code = models.CharField("采购单号", max_length=40, unique=True)

    supplier = models.ForeignKey(
        "procurement.Supplier",
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        verbose_name="供应商",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
        verbose_name="制单人",
    )

    ordered_on = models.DateField("下单日期", default=timezone.localdate)
    expected_on = models.DateField("预计到货日期", null=True, blank=True)

    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="approved_purchase_orders",
        verbose_name="批准人",
    )
    approved_at = models.DateTimeField("批准时间", null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "采购单"
        verbose_name_plural = "采购单"
        permissions = [("approve_purchaseorder", "批准采购单")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(expected_on__isnull=True)
                    | models.Q(expected_on__gte=models.F("ordered_on"))
                ),
                name="purchase_expected_on_not_before_ordered_on",
            ),
        ]

    def __str__(self):
        return self.code

class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.PROTECT,
        related_name="lines",
        verbose_name="采购单",
    )

    item = models.ForeignKey(
        "inventory.Item",
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
        verbose_name="物品",
    )

    line_no = models.PositiveIntegerField(
        "行号",
        validators=[MinValueValidator(1)],
    )

    quantity = models.DecimalField(
        "采购数量",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    unit_price = models.DecimalField(
        "单价（元）",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["order_id", "line_no"]
        verbose_name = "采购明细"
        verbose_name_plural = "采购明细"
        constraints = [
            models.UniqueConstraint(
                fields=["order", "line_no"],
                name="unique_purchase_order_line_no",
            ),
            models.CheckConstraint(
                condition=models.Q(line_no__gte=1),
                name="purchase_line_no_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="purchase_line_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="purchase_line_unit_price_nonnegative",
            ),
        ]

    @property
    def amount(self):
        if self.quantity is None or self.unit_price is None:
            return None

        return (self.quantity * self.unit_price).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def __str__(self):
        return f"{self.order.code} / 第{self.line_no}行"

class Receipt(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        POSTED = "posted", "已入库"
        CANCELLED = "cancelled", "已取消"

    code = models.CharField("收货单号", max_length=40, unique=True)

    purchase_order = models.ForeignKey(
        "procurement.PurchaseOrder",
        on_delete=models.PROTECT,
        related_name="receipts",
        verbose_name="采购单",
    )

    received_on = models.DateField(
        "收货日期",
        default=timezone.localdate,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="registered_receipts",
        verbose_name="收货登记人",
    )

    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="posted_receipts",
        verbose_name="入库确认人",
    )
    posted_at = models.DateTimeField("入库确认时间", null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "收货单"
        verbose_name_plural = "收货单"
        permissions = [("post_receipt", "确认收货入库")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(status="posted", posted_by__isnull=False, posted_at__isnull=False)
                    | (~models.Q(status="posted") & models.Q(posted_by__isnull=True, posted_at__isnull=True))
                ),
                name="receipt_posting_audit_consistent",
            ),
        ]

    def __str__(self):
        return self.code

class ReceiptLine(models.Model):
    receipt = models.ForeignKey(
        "procurement.Receipt",
        on_delete=models.PROTECT,
        related_name="lines",
        verbose_name="收货单",
    )

    purchase_line = models.ForeignKey(
        "procurement.PurchaseOrderLine",
        on_delete=models.PROTECT,
        related_name="receipt_lines",
        verbose_name="采购明细",
    )

    location = models.ForeignKey(
        "inventory.StorageLocation",
        on_delete=models.PROTECT,
        related_name="receipt_lines",
        verbose_name="入库库位",
    )

    line_no = models.PositiveIntegerField(
        "行号",
        validators=[MinValueValidator(1)],
    )

    quantity = models.DecimalField(
        "本次实收数量",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    manufacturer_batch_no = models.CharField(
        "厂家批号",
        max_length=80,
        blank=True,
    )

    manufactured_on = models.DateField(
        "生产日期",
        null=True,
        blank=True,
    )

    expires_on = models.DateField(
        "有效期至",
        null=True,
        blank=True,
    )

    remark = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["receipt_id", "line_no"]
        verbose_name = "收货明细"
        verbose_name_plural = "收货明细"
        constraints = [
            models.UniqueConstraint(
                fields=["receipt", "line_no"],
                name="unique_receipt_line_no",
            ),
            models.CheckConstraint(
                condition=models.Q(line_no__gte=1),
                name="receipt_line_no_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="receipt_line_quantity_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(manufactured_on__isnull=True)
                    | models.Q(expires_on__isnull=True)
                    | models.Q(
                        expires_on__gte=models.F("manufactured_on")
                    )
                ),
                name="receipt_expiry_not_before_manufacture",
            ),
        ]

    def __str__(self):
        return f"{self.receipt.code} / 第{self.line_no}行"