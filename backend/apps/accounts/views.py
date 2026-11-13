from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_GET, require_POST

from apps.core.http import api_error, parse_json


def user_data(user):
    if not user.is_authenticated:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "username": user.username,
            "display_name": user.display_name or user.username,
            "is_staff": user.is_staff,
        },
    }


@require_GET
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_GET
def me(request):
    return JsonResponse(user_data(request.user))


@require_POST
def sign_in(request):
    try:
        data = parse_json(request)
    except ValueError as error:
        return api_error(str(error))
    username, password = data.get("username"), data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return api_error("请填写用户名和密码。")
    if (
        not username.strip()
        or not password
        or len(username) > 150
        or len(password) > 1024
    ):
        return api_error("用户名或密码格式不正确。")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return api_error("用户名或密码错误，或账号已停用。", status=401)
    login(request, user)
    return JsonResponse(user_data(user))


@require_POST
def sign_out(request):
    logout(request)
    return JsonResponse({"message": "已退出登录。"})
