from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.core.http import api_error, authenticated, parse_json
from .forms import ItemForm
from .models import Item


def serialize_item(item):
    return {
        "id": item.pk,
        "code": item.code,
        "name": item.name,
        "kind": item.kind,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": str(item.quantity),
        "location": item.location,
        "expires_on": item.expires_on.isoformat() if item.expires_on else None,
    }


@require_http_methods(["GET", "POST"])
@authenticated
def items(request):
    if request.method == "POST":
        if not request.user.is_staff:
            return api_error("当前账号可查看物品，新增需要管理员权限。", status=403)
        try:
            data = parse_json(request)
        except ValueError as error:
            return api_error(str(error))
        form = ItemForm(data)
        if not form.is_valid():
            return api_error("请检查输入内容。", errors=form.errors.get_json_data())
        try:
            with transaction.atomic():
                item = form.save()
        except IntegrityError:
            return api_error("编号已存在，请更换编号。", status=409)
        return JsonResponse(serialize_item(item), status=201)

    kind = request.GET.get("kind", "")
    if kind and kind not in Item.Kind.values:
        return api_error("类型应为 equipment 或 material。")
    try:
        page = int(request.GET.get("page", "1"))
        if page < 1:
            raise ValueError
    except ValueError:
        return api_error("页码必须为正整数。")
    query = request.GET.get("q", "").strip()[:100]
    records = Item.objects.all()
    if kind:
        records = records.filter(kind=kind)
    if query:
        records = records.filter(
            Q(name__icontains=query)
            | Q(code__icontains=query)
            | Q(location__icontains=query)
        )
    count = records.count()
    page_size = 20
    start = (page - 1) * page_size
    return JsonResponse(
        {
            "count": count,
            "page": page,
            "page_size": page_size,
            "results": [
                serialize_item(item) for item in records[start : start + page_size]
            ],
        }
    )
