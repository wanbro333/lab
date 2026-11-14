"""真实业务结果测试；并发用 TransactionTestCase + MySQL，不能用 SQLite 代替。"""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, connections, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from apps.inventory.models import Item, StorageLocation, StockBatch, StockMovement
from .models import Supplier, PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine
from .services import approve_purchase_order, post_receipt


class PostingFixtures:
    def setUp(self):
        self.sequence = 0
        self.actor = get_user_model().objects.create_user(
            username="posting-admin", is_staff=True, is_superuser=True,
        )
        self.supplier = Supplier.objects.create(code="S1", name="供应商")
        self.item = Item.objects.create(
            code="I1", name="材料", kind="material", unit="瓶", quantity=17,
        )
        self.location = StorageLocation.objects.create(code="L1", name="一号柜")

    def make_order(self, quantity="10.00", approved=True):
        self.sequence += 1
        order = PurchaseOrder.objects.create(
            code=f"PO-{self.sequence}", supplier=self.supplier, created_by=self.actor,
        )
        line = PurchaseOrderLine.objects.create(
            order=order, item=self.item, line_no=1,
            quantity=Decimal(quantity), unit_price=Decimal("25.50"),
        )
        if approved:
            approve_purchase_order(order.pk, self.actor)
            order.refresh_from_db()
        return order, line

    def make_receipt(self, order, purchase_line, quantities=("6.00",)):
        self.sequence += 1
        receipt = Receipt.objects.create(
            code=f"GR-{self.sequence}", purchase_order=order, received_by=self.actor,
        )
        for number, value in enumerate(quantities, 1):
            ReceiptLine.objects.create(
                receipt=receipt, purchase_line=purchase_line, location=self.location,
                line_no=number, quantity=Decimal(value),
                manufacturer_batch_no=f"LOT-{number}",
                manufactured_on=timezone.localdate(),
                expires_on=timezone.localdate() + timedelta(days=365),
            )
        return receipt

    def assert_no_posting(self, receipt):
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, Receipt.Status.DRAFT)
        self.assertIsNone(receipt.posted_by_id)
        self.assertIsNone(receipt.posted_at)
        self.assertFalse(StockBatch.objects.filter(receipt_line__receipt=receipt).exists())
        self.assertFalse(StockMovement.objects.filter(receipt_line__receipt=receipt).exists())


class PostingTests(PostingFixtures, TestCase):
    def test_normal_post_copies_source_and_preserves_legacy_quantity(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        result, changed = post_receipt(receipt.pk, self.actor)
        batch = StockBatch.objects.get()
        movement = StockMovement.objects.get()
        self.assertTrue(changed)
        self.assertEqual(result.status, Receipt.Status.POSTED)
        self.assertEqual(batch.quantity, Decimal("6.00"))
        self.assertEqual(batch.item_id, self.item.pk)
        self.assertEqual(batch.location_id, self.location.pk)
        self.assertEqual(batch.unit, "瓶")
        self.assertEqual(batch.manufacturer_batch_no, "LOT-1")
        self.assertEqual(movement.batch_id, batch.pk)
        self.assertEqual(movement.receipt_line_id, batch.receipt_line_id)
        self.assertEqual(movement.quantity_change, batch.quantity)
        self.assertEqual(movement.posted_by_id, self.actor.pk)
        self.assertEqual(movement.posted_at, result.posted_at)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("17.00"))

    def test_repeat_is_noop(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        first, _ = post_receipt(receipt.pk, self.actor)
        second, changed = post_receipt(receipt.pk, self.actor)
        self.assertFalse(changed)
        self.assertEqual(first.posted_at, second.posted_at)
        self.assertEqual(StockBatch.objects.count(), 1)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_split_batches_and_partial_receipts_reach_exact_limit(self):
        order, line = self.make_order()
        a = self.make_receipt(order, line, ("3", "3"))
        b = self.make_receipt(order, line, ("4",))
        post_receipt(a.pk, self.actor)
        post_receipt(b.pk, self.actor)
        self.assertEqual(StockBatch.objects.count(), 3)
        self.assertEqual(sum(b.quantity for b in StockBatch.objects.all()), Decimal("10"))

    def test_cross_receipt_overage_is_rejected(self):
        order, line = self.make_order()
        a = self.make_receipt(order, line, ("6",))
        b = self.make_receipt(order, line, ("5",))
        post_receipt(a.pk, self.actor)
        with self.assertRaises(ValidationError):
            post_receipt(b.pk, self.actor)
        self.assert_no_posting(b)
        self.assertEqual(StockBatch.objects.count(), 1)

    def test_same_receipt_multiple_rows_are_summed(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line, ("6", "6"))
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_other_drafts_do_not_consume_capacity(self):
        order, line = self.make_order()
        self.make_receipt(order, line, ("10",))
        receipt = self.make_receipt(order, line, ("6",))
        self.assertTrue(post_receipt(receipt.pk, self.actor)[1])

    def test_unapproved_order_is_rejected(self):
        order, line = self.make_order(approved=False)
        receipt = self.make_receipt(order, line)
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_empty_receipt_is_rejected(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line, ())
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_wrong_source_order_is_rejected_even_without_formset(self):
        order, _ = self.make_order()
        _, other_line = self.make_order()
        receipt = self.make_receipt(order, other_line)
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_inactive_location_is_rechecked(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        StorageLocation.objects.filter(pk=self.location.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_expired_material_is_rejected(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        ReceiptLine.objects.filter(receipt=receipt).update(
            manufactured_on=None, expires_on=timezone.localdate() - timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)

    def test_unauthorized_staff_cannot_approve_or_post(self):
        user = get_user_model().objects.create_user(username="staff-only", is_staff=True)
        order, line = self.make_order(approved=False)
        receipt = self.make_receipt(order, line)
        with self.assertRaises(PermissionDenied):
            approve_purchase_order(order.pk, user)
        with self.assertRaises(PermissionDenied):
            post_receipt(receipt.pk, user)
        self.assert_no_posting(receipt)

    def test_empty_order_cannot_be_approved(self):
        order = PurchaseOrder.objects.create(
            code="EMPTY", supplier=self.supplier, created_by=self.actor,
        )
        with self.assertRaises(ValidationError):
            approve_purchase_order(order.pk, self.actor)
        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.DRAFT)

    def test_approval_is_audited_and_repeat_is_noop(self):
        order, _ = self.make_order(approved=False)
        first, changed = approve_purchase_order(order.pk, self.actor)
        second, repeated = approve_purchase_order(order.pk, self.actor)
        self.assertTrue(changed)
        self.assertFalse(repeated)
        self.assertEqual(first.approved_by_id, self.actor.pk)
        self.assertEqual(first.approved_at, second.approved_at)

    def test_failure_after_first_movement_rolls_back_all_rows(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line, ("3", "3"))
        create = StockMovement.objects.create
        calls = []
        def fail_second(**kwargs):
            calls.append(kwargs)
            if len(calls) == 2:
                raise RuntimeError("模拟第二笔流水写入失败")
            return create(**kwargs)
        with patch("apps.procurement.services.StockMovement.objects.create", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                post_receipt(receipt.pk, self.actor)
        self.assert_no_posting(receipt)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_database_prevents_duplicate_source_batch(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        post_receipt(receipt.pk, self.actor)
        batch = StockBatch.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockBatch.objects.create(
                code="OTHER", item=self.item, location=self.location,
                receipt_line_id=batch.receipt_line_id, unit="瓶", quantity=1,
            )

    def test_database_prevents_duplicate_source_movement(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        post_receipt(receipt.pk, self.actor)
        movement = StockMovement.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockMovement.objects.create(
                batch_id=movement.batch_id, receipt_line_id=movement.receipt_line_id,
                quantity_change=6, posted_by=self.actor,
            )

    def test_admin_actions_finish_approval_and_posting(self):
        order, line = self.make_order(approved=False)
        receipt = self.make_receipt(order, line)
        client = Client(HTTP_HOST="localhost")
        client.force_login(self.actor)
        response = client.post("/admin/procurement/purchaseorder/", {
            "action": "approve_selected", "_selected_action": str(order.pk),
        })
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.APPROVED)
        response = client.post("/admin/procurement/receipt/", {
            "action": "post_selected", "_selected_action": str(receipt.pk),
        })
        self.assertEqual(response.status_code, 302)
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, Receipt.Status.POSTED)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_admin_rejects_stale_edit_of_posted_receipt(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        post_receipt(receipt.pk, self.actor)
        client = Client(HTTP_HOST="localhost")
        client.force_login(self.actor)
        response = client.post(f"/admin/procurement/receipt/{receipt.pk}/change/", {
            "code": "FORGED", "status": "draft", "_save": "Save",
        })
        self.assertEqual(response.status_code, 403)
        receipt.refresh_from_db()
        self.assertNotEqual(receipt.code, "FORGED")
        self.assertEqual(receipt.status, Receipt.Status.POSTED)

    def test_admin_locks_approved_order_and_stock_records(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        post_receipt(receipt.pk, self.actor)
        client = Client(HTTP_HOST="localhost")
        client.force_login(self.actor)
        for path in [
            f"/admin/procurement/purchaseorder/{order.pk}/change/",
            f"/admin/inventory/stockbatch/{StockBatch.objects.get().pk}/change/",
            "/admin/inventory/stockmovement/add/",
        ]:
            self.assertEqual(client.post(path, {"_save": "Save"}).status_code, 403)

    def test_admin_receipt_formset_rejects_wrong_source_and_overage(self):
        order, line = self.make_order()
        _, other_line = self.make_order()
        client = Client(HTTP_HOST="localhost")
        client.force_login(self.actor)
        data = {
            "code": "FORM-R", "purchase_order": str(order.pk),
            "received_on": timezone.localdate().isoformat(), "remark": "",
            "lines-TOTAL_FORMS": "2", "lines-INITIAL_FORMS": "0",
            "lines-MIN_NUM_FORMS": "0", "lines-MAX_NUM_FORMS": "1000",
            "_save": "Save",
        }
        for i in range(2):
            data.update({
                f"lines-{i}-line_no": str(i + 1),
                f"lines-{i}-purchase_line": str(line.pk),
                f"lines-{i}-location": str(self.location.pk),
                f"lines-{i}-quantity": "3.00",
                f"lines-{i}-manufacturer_batch_no": "",
                f"lines-{i}-manufactured_on": "",
                f"lines-{i}-expires_on": "", f"lines-{i}-remark": "",
            })
        wrong = dict(data)
        wrong["lines-0-purchase_line"] = str(other_line.pk)
        self.assertEqual(client.post("/admin/procurement/receipt/add/", wrong).status_code, 200)
        self.assertFalse(Receipt.objects.filter(code="FORM-R").exists())
        over = dict(data)
        over["lines-0-quantity"] = "6"
        over["lines-1-quantity"] = "6"
        self.assertEqual(client.post("/admin/procurement/receipt/add/", over).status_code, 200)
        self.assertFalse(Receipt.objects.filter(code="FORM-R").exists())
        self.assertEqual(client.post("/admin/procurement/receipt/add/", data).status_code, 302)
        self.assertEqual(Receipt.objects.get(code="FORM-R").lines.count(), 2)


@skipUnless(connection.vendor == "mysql", "SQLite 不支持有效的行锁，必须使用真实 MySQL。")
class PostingConcurrencyTests(PostingFixtures, TransactionTestCase):
    reset_sequences = True

    def run_concurrent(self, receipt_ids):
        gate = Barrier(len(receipt_ids))
        actor_id = self.actor.pk
        def run(receipt_id):
            connections.close_all()
            try:
                actor = get_user_model().objects.get(pk=actor_id)
                gate.wait(timeout=10)
                try:
                    return ("ok", post_receipt(receipt_id, actor)[1])
                except ValidationError:
                    return ("rejected", False)
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=len(receipt_ids)) as pool:
            futures = [pool.submit(run, pk) for pk in receipt_ids]
            return [future.result(timeout=20) for future in futures]

    def test_two_receipts_cannot_both_exceed_purchase_limit(self):
        order, line = self.make_order()
        a = self.make_receipt(order, line, ("6",))
        b = self.make_receipt(order, line, ("6",))
        results = self.run_concurrent([a.pk, b.pk])
        self.assertCountEqual(results, [("ok", True), ("rejected", False)])
        self.assertEqual(StockBatch.objects.count(), 1)
        self.assertEqual(StockMovement.objects.count(), 1)
        self.assertEqual(Receipt.objects.filter(status="posted").count(), 1)

    def test_same_receipt_posts_once_under_concurrency(self):
        order, line = self.make_order()
        receipt = self.make_receipt(order, line)
        results = self.run_concurrent([receipt.pk, receipt.pk])
        self.assertCountEqual(results, [("ok", True), ("ok", False)])
        self.assertEqual(StockBatch.objects.count(), 1)
        self.assertEqual(StockMovement.objects.count(), 1)
