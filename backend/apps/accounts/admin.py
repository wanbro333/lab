from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class LabUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("实验室资料", {"fields": ("display_name",)}),)
