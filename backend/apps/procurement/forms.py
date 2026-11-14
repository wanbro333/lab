from decimal import Decimal

from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class ReceiptLineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors) or not self.instance.purchase_order_id:
            return

        totals = {}

        for form in self.forms:
            data = form.cleaned_data

            if not data or data.get("DELETE"):
                continue

            purchase_line = data["purchase_line"]
            location = data["location"]
            quantity = data["quantity"]

            if purchase_line.order_id != self.instance.purchase_order_id:
                raise ValidationError(
                    f"第 {data['line_no']} 行："
                    "采购明细不属于上方选择的采购单。"
                )

            if not location.is_active:
                raise ValidationError(
                    f"第 {data['line_no']} 行："
                    "该库位已停用，请重新选择。"
                )

            key = purchase_line.pk
            totals[key] = totals.get(key, Decimal("0")) + quantity

            if totals[key] > purchase_line.quantity:
                raise ValidationError(
                    f"采购第 {purchase_line.line_no} 行："
                    "本张收货单实收合计不能超过采购数量 "
                    f"{purchase_line.quantity}。"
                )