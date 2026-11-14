"""采购批准和确认入库。写入入口统一锁定采购单父行。"""
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.inventory.models import Item, StockBatch, StockMovement, StorageLocation
from .models import PurchaseOrder, PurchaseOrderLine, Receipt, ReceiptLine


def _require_permission(actor, operation, model):
    if (
        not actor.is_authenticated or not actor.is_active or not actor.is_staff
        or not actor.has_perm(f"procurement.{operation}")
        or not actor.has_perm(f"procurement.change_{model}")
    ):
        raise PermissionDenied("当前账号没有执行此操作的权限。")


@transaction.atomic
def approve_purchase_order(order_id, actor):
    """本阶段管理员单级批准：返回 (采购单, 是否刚完成批准)。"""
    _require_permission(actor, "approve_purchaseorder", "purchaseorder")
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)
    if order.status == PurchaseOrder.Status.APPROVED:
        return order, False
    if order.status not in (
        PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.SUBMITTED,
    ):
        raise ValidationError("当前采购单状态不允许批准。")
    order.full_clean()
    lines = list(
        PurchaseOrderLine.objects.select_for_update()
        .filter(order=order).order_by("pk")
    )
    if not lines:
        raise ValidationError("空采购单不能批准，请先添加采购明细。")
    for line in lines:
        line.full_clean()
    order.status = PurchaseOrder.Status.APPROVED
    order.approved_by = actor
    order.approved_at = timezone.now()
    order.full_clean()
    order.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return order, True


@transaction.atomic
def post_receipt(receipt_id, actor):
    """全部入库或全部回滚；返回 (收货单, 是否刚完成入库)。"""
    _require_permission(actor, "post_receipt", "receipt")

    # 锁的顺序固定：采购单 -> 收货单 -> 明细 -> 库位。
    # 同一采购单的其他收货单也会争用这个父行锁。
    order_id = Receipt.objects.values_list("purchase_order_id", flat=True).get(
        pk=receipt_id
    )
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)
    receipt = Receipt.objects.select_for_update().get(pk=receipt_id)
    if receipt.purchase_order_id != order.pk:
        raise ValidationError("采购单关联已变化，请刷新后重试。")
    if receipt.status == Receipt.Status.POSTED:
        return receipt, False
    if receipt.status != Receipt.Status.DRAFT:
        raise ValidationError("只有收货草稿可以确认入库。")
    if order.status != PurchaseOrder.Status.APPROVED:
        raise ValidationError("请先批准对应采购单，再确认入库。")
    receipt.full_clean()

    lines = list(
        ReceiptLine.objects.select_for_update()
        .filter(receipt=receipt).order_by("pk")
    )
    if not lines:
        raise ValidationError("空收货单不能入库。")

    purchase_lines = {
        line.pk: line
        for line in PurchaseOrderLine.objects.select_for_update()
        .filter(order=order).order_by("pk")
    }
    locations = {
        loc.pk: loc
        for loc in StorageLocation.objects.select_for_update()
        .filter(pk__in={line.location_id for line in lines}).order_by("pk")
    }
    wanted = defaultdict(lambda: Decimal("0.00"))
    for line in lines:
        line.full_clean()
        if line.purchase_line_id not in purchase_lines:
            raise ValidationError(f"第 {line.line_no} 行采购明细不属于本采购单。")
        if not locations[line.location_id].is_active:
            raise ValidationError(f"第 {line.line_no} 行库位已停用。")
        if line.expires_on and line.expires_on < timezone.localdate():
            raise ValidationError(f"第 {line.line_no} 行已过有效期，不能入库。")
        wanted[line.purchase_line_id] += line.quantity

    # 只累计已经成功入库的收货单；草稿不占库存。
    received = {
        row["purchase_line_id"]: row["total"]
        for row in ReceiptLine.objects.filter(
            purchase_line_id__in=wanted,
            receipt__status=Receipt.Status.POSTED,
        ).values("purchase_line_id").annotate(total=Sum("quantity"))
    }
    for line_id, quantity in wanted.items():
        old_quantity = received.get(line_id, Decimal("0.00"))
        if old_quantity + quantity > purchase_lines[line_id].quantity:
            raise ValidationError(
                f"采购第 {purchase_lines[line_id].line_no} 行超量："
                f"已入库 {old_quantity}，本次 {quantity}，"
                f"采购 {purchase_lines[line_id].quantity}。"
            )

    # 校验全部通过后才开始记账；后续任一步失败都会回滚。
    posted_at = timezone.now()
    for line in lines:
        purchase_line = purchase_lines[line.purchase_line_id]
        item = Item.objects.get(pk=purchase_line.item_id)
        batch = StockBatch.objects.create(
            code=f"B{line.pk:010d}",
            item_id=purchase_line.item_id,
            location_id=line.location_id,
            receipt_line=line,
            unit=item.unit,
            manufacturer_batch_no=line.manufacturer_batch_no,
            manufactured_on=line.manufactured_on,
            expires_on=line.expires_on,
            quantity=line.quantity,
        )
        StockMovement.objects.create(
            batch=batch,
            receipt_line=line,
            kind=StockMovement.Kind.RECEIPT,
            quantity_change=line.quantity,
            posted_by=actor,
            posted_at=posted_at,
        )

    receipt.status = Receipt.Status.POSTED
    receipt.posted_by = actor
    receipt.posted_at = posted_at
    receipt.full_clean()
    receipt.save(update_fields=["status", "posted_by", "posted_at", "updated_at"])
    return receipt, True
