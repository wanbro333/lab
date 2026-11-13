from django.contrib import admin
from .forms import ItemForm
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    form = ItemForm
    list_display = ["code", "name", "kind", "quantity", "unit", "location"]
    list_filter = ["kind"]
    search_fields = ["code", "name", "location"]
