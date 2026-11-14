from django.contrib import admin

from .forms import ItemForm
from .models import Item, StorageLocation, StockBatch, StockMovement


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ["code", "name", "kind", "quantity", "unit", "location"]
    list_filter = ["kind"]
    search_fields = ["code", "name", "location"]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.purchase_order_lines.exists():
            # 采购数量依赖该基本单位；已有采购时不允许后台改单位。
            return ["unit"]
        return []


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active"]
    search_fields = ["code", "name"]
    list_filter = ["is_active"]


class StockReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockBatch)
class StockBatchAdmin(StockReadOnlyAdmin):
    list_display = ["code", "item", "location", "quantity", "unit", "expires_on"]
    search_fields = ["code", "item__code", "item__name", "manufacturer_batch_no"]
    list_filter = ["location"]
    list_select_related = ["item", "location"]


@admin.register(StockMovement)
class StockMovementAdmin(StockReadOnlyAdmin):
    list_display = ["id", "batch", "kind", "quantity_change", "posted_by", "posted_at"]
    search_fields = ["batch__code", "receipt_line__receipt__code"]
    list_filter = ["kind"]
    list_select_related = ["batch", "posted_by"]
