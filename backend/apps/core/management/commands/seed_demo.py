"""Explicit, idempotent development data. Never rewrites existing records."""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.inventory.models import Item


class Command(BaseCommand):
    help = "创建带 DEMO 前缀的示例物品；可选创建本地开发管理员。"

    def add_arguments(self, parser):
        parser.add_argument("--create-user", action="store_true")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("示例初始化仅允许在 DJANGO_DEBUG=true 的本地环境执行。")
        examples = [
            (
                "DEMO-E001",
                "数字示波器（示例）",
                "equipment",
                "100 MHz / 双通道",
                "台",
                "2",
                "A101 · 仪器柜 01",
            ),
            (
                "DEMO-E002",
                "直流稳压电源（示例）",
                "equipment",
                "0–30 V / 5 A",
                "台",
                "3",
                "A101 · 实验台 02",
            ),
            (
                "DEMO-M001",
                "杜邦线（示例）",
                "material",
                "20 cm / 公对母",
                "根",
                "120",
                "A102 · 材料柜 03",
            ),
            (
                "DEMO-M002",
                "实验记录本（示例）",
                "material",
                "A4 / 80 页",
                "本",
                "24",
                "A102 · 材料柜 01",
            ),
        ]
        for code, name, kind, specification, unit, quantity, location in examples:
            Item.objects.get_or_create(
                code=code,
                defaults=dict(
                    name=name,
                    kind=kind,
                    specification=specification,
                    unit=unit,
                    quantity=quantity,
                    location=location,
                ),
            )
        self.stdout.write(self.style.SUCCESS("示例物品已就绪，已有记录保持原值。"))
        if options["create_user"]:
            User = get_user_model()
            if User.objects.filter(username="lab_dev").exists():
                self.stdout.write("lab_dev 已存在，未重置密码。")
                return
            password = secrets.token_urlsafe(18)
            runtime = settings.ROOT_DIR / ".runtime"
            runtime.mkdir(exist_ok=True)
            credential_path = runtime / "dev-account.txt"
            credential_path.write_text(
                f"本地开发管理员（不要提交或分享此文件）\n用户名：lab_dev\n密码：{password}\n",
                encoding="utf-8",
            )
            User.objects.create_superuser(
                username="lab_dev", password=password, display_name="开发管理员"
            )
            self.stdout.write(
                self.style.SUCCESS(f"开发账号已创建，凭据保存在 {credential_path}")
            )
