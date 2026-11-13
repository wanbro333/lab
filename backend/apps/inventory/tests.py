import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import Client, TestCase

from .models import Item


class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user(
            "admin", password="test-pass-only", is_staff=True
        )
        cls.member = get_user_model().objects.create_user(
            "member", password="test-pass-only"
        )
        Item.objects.create(
            code="EQ-001",
            name="示波器",
            kind="equipment",
            unit="台",
            quantity="2",
            location="A101",
        )
        Item.objects.create(
            code="MT-001", name="实验线", kind="material", unit="根", quantity="12.50"
        )

    def payload(self, **changes):
        return {
            "code": "MT-002",
            "name": "测试材料",
            "kind": "material",
            "unit": "米",
            "quantity": "1.25",
            **changes,
        }

    def post_item(self, payload):
        return self.client.post(
            "/api/inventory/items/",
            json.dumps(payload),
            content_type="application/json",
        )

    def test_health_checks_database(self):
        self.assertEqual(self.client.get("/api/health/").json()["status"], "ok")
        with patch(
            "apps.core.views.connection.cursor",
            side_effect=DatabaseError("secret connection info"),
        ):
            response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.content.decode())

    def test_inventory_requires_login(self):
        self.assertEqual(self.client.get("/api/inventory/items/").status_code, 401)

    def test_member_can_read_but_cannot_write(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get("/api/inventory/items/").json()["count"], 2)
        self.assertEqual(self.post_item(self.payload()).status_code, 403)
        self.assertEqual(Item.objects.count(), 2)

    def test_admin_creates_decimal_quantity(self):
        self.client.force_login(self.admin)
        response = self.post_item(self.payload(expires_on="2027-01-01"))
        self.assertEqual(response.status_code, 201)
        item = Item.objects.get(code="MT-002")
        self.assertEqual(str(item.quantity), "1.25")
        self.assertEqual(item.expires_on.isoformat(), "2027-01-01")

    def test_invalid_payloads_do_not_write(self):
        self.client.force_login(self.admin)
        for changes in [
            {"quantity": "-1"},
            {"quantity": "1.234"},
            {"code": "EQ-001"},
            {"name": ""},
            {"kind": "unknown"},
            {"expires_on": "not-a-date"},
            {"kind": "equipment", "expires_on": "2027-01-01"},
        ]:
            with self.subTest(changes=changes):
                self.assertEqual(
                    self.post_item(self.payload(**changes)).status_code, 400
                )
        self.assertEqual(Item.objects.count(), 2)

    def test_malformed_json(self):
        self.client.force_login(self.admin)
        for body in ["{bad", "[]", "null"]:
            self.assertEqual(
                self.client.post(
                    "/api/inventory/items/", body, content_type="application/json"
                ).status_code,
                400,
            )
        self.assertEqual(
            self.client.post("/api/inventory/items/", self.payload()).status_code, 400
        )

    def test_filter_search_and_pagination(self):
        self.client.force_login(self.member)
        self.assertEqual(
            self.client.get("/api/inventory/items/?kind=material").json()["count"], 1
        )
        self.assertEqual(
            self.client.get("/api/inventory/items/?q=A101").json()["results"][0][
                "code"
            ],
            "EQ-001",
        )
        self.assertEqual(
            self.client.get("/api/inventory/items/?q=不存在").json()["count"], 0
        )
        self.assertEqual(
            self.client.get("/api/inventory/items/?page=2").json()["results"], []
        )
        for suffix in ["page=0", "page=x", "kind=other"]:
            self.assertEqual(
                self.client.get(f"/api/inventory/items/?{suffix}").status_code, 400
            )

    def test_login_logout_with_real_csrf(self):
        browser = Client(enforce_csrf_checks=True)
        credentials = json.dumps({"username": "admin", "password": "test-pass-only"})
        self.assertEqual(
            browser.post(
                "/api/auth/login/", credentials, content_type="application/json"
            ).status_code,
            403,
        )
        token = browser.get("/api/auth/csrf/").json()["csrfToken"]
        result = browser.post(
            "/api/auth/login/",
            credentials,
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(browser.get("/api/auth/me/").json()["authenticated"])
        # Login rotates the CSRF token; the client must fetch a fresh token.
        token = browser.get("/api/auth/csrf/").json()["csrfToken"]
        self.assertEqual(
            browser.post(
                "/api/inventory/items/",
                json.dumps(self.payload()),
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(
            browser.post(
                "/api/inventory/items/",
                json.dumps(self.payload()),
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
            ).status_code,
            201,
        )
        self.assertEqual(
            browser.post(
                "/api/auth/logout/",
                "{}",
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
            ).status_code,
            200,
        )
        self.assertFalse(browser.get("/api/auth/me/").json()["authenticated"])

    def test_invalid_credentials_and_inactive_user(self):
        for payload in [
            {"username": "admin", "password": "wrong"},
            {"username": [], "password": "x"},
        ]:
            response = self.client.post(
                "/api/auth/login/", json.dumps(payload), content_type="application/json"
            )
            self.assertIn(response.status_code, [400, 401])
        self.member.is_active = False
        self.member.save()
        response = self.client.post(
            "/api/auth/login/",
            json.dumps({"username": "member", "password": "test-pass-only"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
