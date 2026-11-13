from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "实验室管理后台"
admin.site.site_title = "实验室管理"
admin.site.index_title = "基础数据维护"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
]
