import json
from functools import wraps

from django.http import JsonResponse


def api_error(message, status=400, **extra):
    return JsonResponse({"message": message, **extra}, status=status)


def parse_json(request):
    if request.content_type != "application/json":
        raise ValueError("请求必须使用 application/json。")
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("请求正文不是有效的 JSON。") from None
    if not isinstance(data, dict):
        raise ValueError("请求正文必须是 JSON 对象。")
    return data


def authenticated(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return api_error("请先登录。", status=401)
        return view(request, *args, **kwargs)

    return wrapped


def csrf_failure(request, reason=""):
    return api_error("安全验证已失效，请刷新页面后重试。", status=403)
