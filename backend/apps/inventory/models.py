from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.db import models


class Item(models.Model):
    class Kind(models.TextChoices):
        EQUIPMENT = "equipment", "器材"
        MATERIAL = "material", "材料"

    code = models.CharField("编号", max_length=40, unique=True)
    name = models.CharField("名称", max_length=100)
    kind = models.CharField("类型", max_length=16, choices=Kind.choices)
    specification = models.CharField("规格", max_length=120, blank=True)
    unit = models.CharField("单位", max_length=16)
    quantity = models.DecimalField(
        "初始数量", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    location = models.CharField("存放位置", max_length=120, blank=True)
    expires_on = models.DateField("有效期至", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "物品"
        verbose_name_plural = "物品"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0), name="item_quantity_nonnegative"
            )
        ]

    def __str__(self):
        return f"{self.code} · {self.name}"

class StorageLocation(models.Model):
    code = models.CharField("库位编码", max_length=40, unique=True)
    name = models.CharField("库位名称", max_length=100)
    remark = models.TextField("备注", blank=True)
    is_active = models.BooleanField("启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "库位"
        verbose_name_plural = "库位"

    def __str__(self):
        return f"{self.code} · {self.name}"


# 每条正式收货明细对应一个内部批次；余额仅由业务服务维护。
class StockBatch(models.Model):
    code = models.CharField("内部批次号", max_length=40, unique=True)
    item = models.ForeignKey(
        "inventory.Item", on_delete=models.PROTECT,
        related_name="stock_batches", verbose_name="物品",
    )
    location = models.ForeignKey(
        "inventory.StorageLocation", on_delete=models.PROTECT,
        related_name="stock_batches", verbose_name="库位",
    )
    receipt_line = models.OneToOneField(
        "procurement.ReceiptLine", on_delete=models.PROTECT,
        related_name="stock_batch", verbose_name="来源收货明细",
    )
    unit = models.CharField("计量单位快照", max_length=16)
    manufacturer_batch_no = models.CharField("厂家批号", max_length=80, blank=True)
    manufactured_on = models.DateField("生产日期", null=True, blank=True)
    expires_on = models.DateField("有效期至", null=True, blank=True)
    quantity = models.DecimalField(
        "当前在库数量", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "库存批次"
        verbose_name_plural = "库存批次"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name="stock_batch_quantity_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(manufactured_on__isnull=True)
                    | models.Q(expires_on__isnull=True)
                    | models.Q(expires_on__gte=models.F("manufactured_on"))
                ),
                name="stock_batch_expiry_valid",
            ),
        ]

    def __str__(self):
        return self.code


class StockMovement(models.Model):
    class Kind(models.TextChoices):
        RECEIPT = "receipt", "采购入库"

    batch = models.ForeignKey(
        "inventory.StockBatch", on_delete=models.PROTECT,
        related_name="movements", verbose_name="库存批次",
    )
    receipt_line = models.OneToOneField(
        "procurement.ReceiptLine", on_delete=models.PROTECT,
        related_name="stock_movement", verbose_name="来源收货明细",
    )
    kind = models.CharField(
        "变动类型", max_length=16, choices=Kind.choices, default=Kind.RECEIPT,
    )
    quantity_change = models.DecimalField(
        "变动数量", max_digits=10, decimal_places=2,
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="stock_movements", verbose_name="记账人",
    )
    posted_at = models.DateTimeField("记账时间", default=timezone.now)

    class Meta:
        ordering = ["-posted_at", "-id"]
        verbose_name = "库存流水"
        verbose_name_plural = "库存流水"
        constraints = [
            # 本阶段只开放采购入库。出库/归还须增加来源和新的约束。
            models.CheckConstraint(
                condition=models.Q(kind="receipt", quantity_change__gt=0),
                name="stock_movement_receipt_positive",
            ),
        ]

    def __str__(self):
        return f"{self.batch.code} / {self.quantity_change}"
