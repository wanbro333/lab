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
