from django import forms
from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "code",
            "name",
            "kind",
            "specification",
            "unit",
            "quantity",
            "location",
            "expires_on",
        ]

    def clean(self):
        data = super().clean()
        if data.get("kind") == Item.Kind.EQUIPMENT and data.get("expires_on"):
            self.add_error("expires_on", "器材暂不使用有效期字段，请清空后提交。")
        return data
