from decimal import Decimal
from itertools import chain, zip_longest
from typing import List
from unittest.mock import Mock, patch

import pytest

from ...checkout.calculations import checkout_line_total
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...discount.utils import fetch_active_discounts
from ...order import FulfillmentLineData, OrderLineData
from ...order.actions import create_refund_fulfillment
from ...order.interface import OrderPaymentAction
from ...order.models import Order
from ...plugins.manager import get_plugins_manager
from ..interface import PaymentLineData
from ..utils import (
    PARTIAL_PAYMENT_DIFFERENCE_LINE_ID,
    SHIPPING_PAYMENT_LINE_ID,
    create_payment_lines_information,
    create_refund_data,
)


@pytest.fixture
def manager():
    return get_plugins_manager()


@pytest.fixture
def create_refund_fulfillment_helper(payment_dummy, manager):
    def factory(
        order: Order,
        order_lines: List[OrderLineData] = None,
        fulfillment_lines: List[FulfillmentLineData] = None,
        include_shipping_costs: bool = False,
    ):
        with patch("saleor.order.actions.gateway.refund"):
            return create_refund_fulfillment(
                user=None,
                app=None,
                order=order,
                payments=[
                    OrderPaymentAction(
                        payment=payment_dummy, amount=order.total_gross_amount
                    )
                ],
                order_lines_to_refund=order_lines or [],
                fulfillment_lines_to_refund=fulfillment_lines or [],
                manager=manager,
                include_shipping_costs=include_shipping_costs,
            )

    return factory


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_order_lines(
    order_with_lines, include_shipping_costs, shipping_line_quantity
):
    # given
    order_lines = order_with_lines.lines.all()
    order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=2, variant=line.variant),
        OrderLineData(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order_with_lines,
        order_refund_lines,
        fulfillment_refund_lines,
        include_shipping_costs,
    )

    # then
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(order_lines, order_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_fulfillment_lines(
    fulfilled_order, include_shipping_costs, shipping_line_quantity
):
    # given
    fulfillment_lines = fulfilled_order.fulfillments.first().lines.all()
    order_refund_lines = []
    fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=2,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]

    # when
    refund_data = create_refund_data(
        fulfilled_order,
        order_refund_lines,
        fulfillment_refund_lines,
        include_shipping_costs,
    )

    # then
    assert refund_data == {
        **{
            line.order_line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(fulfillment_lines, fulfillment_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@pytest.mark.parametrize(
    ["include_shipping_costs", "shipping_line_quantity"], [(True, 0), (False, 1)]
)
def test_create_refund_data_shipping_only(
    order, include_shipping_costs, shipping_line_quantity
):
    # given
    order_refund_lines = []
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order, order_refund_lines, fulfillment_refund_lines, include_shipping_costs
    )

    # then
    assert refund_data == {SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity}


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_order_lines(
    _mocked_refund,
    order_with_lines,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    order_lines = order_with_lines.lines.all()
    previous_order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=1, variant=line.variant)
    ]
    create_refund_fulfillment_helper(
        order_with_lines,
        order_lines=previous_order_refund_lines,
        include_shipping_costs=previously_included_shipping_costs,
    )
    current_order_refund_lines = [
        OrderLineData(line=(line := order_lines[0]), quantity=1, variant=line.variant),
        OrderLineData(line=(line := order_lines[1]), quantity=1, variant=line.variant),
    ]
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order_with_lines,
        current_order_refund_lines,
        fulfillment_refund_lines,
        currently_included_shipping_costs,
    )

    # then
    order_refund_lines = [
        OrderLineData(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_order_refund_lines,
            current_order_refund_lines,
            fillvalue=Mock(spec=OrderLineData, quantity=0),
        )
    ]
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(order_lines, order_refund_lines)
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_fulfillment_lines(
    _mocked_refund,
    fulfilled_order,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    fulfillment_lines = list(
        chain.from_iterable(f.lines.all() for f in fulfilled_order.fulfillments.all())
    )
    previous_fulfillment_refund_lines = [
        FulfillmentLineData(line=fulfillment_lines[0], quantity=1)
    ]
    create_refund_fulfillment_helper(
        fulfilled_order,
        fulfillment_lines=previous_fulfillment_refund_lines,
        include_shipping_costs=previously_included_shipping_costs,
    )
    order_refund_lines = []
    current_fulfillment_refund_lines = [
        FulfillmentLineData(
            line=fulfillment_lines[0],
            quantity=1,
        ),
        FulfillmentLineData(
            line=fulfillment_lines[1],
            quantity=1,
        ),
    ]

    # when
    refund_data = create_refund_data(
        fulfilled_order,
        order_refund_lines,
        current_fulfillment_refund_lines,
        currently_included_shipping_costs,
    )

    # then
    fulfillment_refund_lines = [
        FulfillmentLineData(line=cl.line, quantity=pl.quantity + cl.quantity)
        for pl, cl in zip_longest(
            previous_fulfillment_refund_lines,
            current_fulfillment_refund_lines,
            fillvalue=Mock(spec=FulfillmentLineData, quantity=0),
        )
    ]
    assert refund_data == {
        **{
            line.variant_id: line.quantity - refund_line.quantity
            for line, refund_line in zip(
                fulfilled_order.lines.all(), fulfillment_refund_lines
            )
        },
        SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity,
    }


@patch("saleor.order.actions.gateway.refund")
@pytest.mark.parametrize(
    [
        "previously_included_shipping_costs",
        "currently_included_shipping_costs",
        "shipping_line_quantity",
    ],
    [
        (True, True, 0),
        (True, False, 0),
        (False, True, 0),
        (False, False, 1),
    ],
)
def test_create_refund_data_previously_refunded_shipping_only(
    _mocked_refund,
    order,
    create_refund_fulfillment_helper,
    previously_included_shipping_costs,
    currently_included_shipping_costs,
    shipping_line_quantity,
):
    # given
    create_refund_fulfillment_helper(
        order, include_shipping_costs=previously_included_shipping_costs
    )
    order_refund_lines = []
    fulfillment_refund_lines = []

    # when
    refund_data = create_refund_data(
        order,
        order_refund_lines,
        fulfillment_refund_lines,
        currently_included_shipping_costs,
    )

    # then
    assert refund_data == {SHIPPING_PAYMENT_LINE_ID: shipping_line_quantity}


def test_create_payment_lines_information_order(payment_dummy, manager):
    # when
    payment_lines = create_payment_lines_information(payment_dummy, manager)

    # then
    order = payment_dummy.order
    assert payment_lines == [
        PaymentLineData(
            gross=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            product_sku=line.product_sku,
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ] + [
        PaymentLineData(
            gross=order.shipping_price_gross_amount,
            variant_id=SHIPPING_PAYMENT_LINE_ID,
            product_name="Shipping",
            product_sku="Shipping",
            quantity=1,
        )
    ]


def test_create_payment_lines_order_partial_payment(payment_dummy, manager):
    # given
    payment_difference = Decimal("7.34")
    payment_dummy.partial = True
    payment_dummy.total -= payment_difference
    payment_dummy.captured_amount -= payment_difference

    # when
    payment_lines = create_payment_lines_information(
        payment_dummy,
        manager,
    )

    # then
    order = payment_dummy.order
    assert payment_lines == [
        PaymentLineData(
            gross=line.unit_price_gross_amount,
            variant_id=line.variant_id,
            product_name=f"{line.product_name}, {line.variant_name}",
            quantity=line.quantity,
        )
        for line in order.lines.all()
    ] + [
        PaymentLineData(
            gross=order.shipping_price_gross_amount,
            variant_id=SHIPPING_PAYMENT_LINE_ID,
            product_name="Shipping",
            quantity=1,
        ),
        PaymentLineData(
            gross=-payment_difference,
            variant_id=PARTIAL_PAYMENT_DIFFERENCE_LINE_ID,
            product_name="Partial payment difference",
            quantity=1,
        ),
    ]


def get_expected_payment_lines(checkout, manager):
    lines = fetch_checkout_lines(checkout)
    discounts = []
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    address = checkout.shipping_address
    expected_payment_lines = []

    for line_info in lines:
        total_price = checkout_line_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
            discounts=discounts,
        )
        unit_gross = manager.calculate_checkout_line_unit_price(
            total_price,
            line_info.line.quantity,
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        ).gross.amount
        quantity = line_info.line.quantity
        variant_id = line_info.variant.id
        product_name = f"{line_info.variant.product.name}, {line_info.variant.name}"
        product_sku = line_info.variant.sku
        expected_payment_lines.append(
            PaymentLineData(
                gross=unit_gross,
                variant_id=variant_id,
                product_name=product_name,
                product_sku=product_sku,
                quantity=quantity,
            )
        )

    shipping_gross = manager.calculate_checkout_shipping(
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    ).gross.amount
    expected_payment_lines.append(
        PaymentLineData(
            gross=shipping_gross,
            variant_id=SHIPPING_PAYMENT_LINE_ID,
            product_name="Shipping",
            product_sku="Shipping",
            quantity=1,
        )
    )

    return expected_payment_lines


@pytest.fixture
def payment_for_checkout(payment_dummy, checkout_with_items, manager):
    payment_dummy.order = None
    payment_dummy.checkout = checkout_with_items
    lines = fetch_checkout_lines(checkout_with_items)
    discounts = fetch_active_discounts()
    checkout_info = fetch_checkout_info(checkout_with_items, lines, discounts, manager)
    address = checkout_info.shipping_address or checkout_info.billing_address
    payment_dummy.total = manager.calculate_checkout_total(
        checkout_info, lines, address, discounts
    ).gross.amount
    return payment_dummy


def test_create_payment_lines_checkout(
    payment_for_checkout, checkout_with_items, manager
):
    # given
    payment_for_checkout.order = None
    payment_for_checkout.checkout = checkout_with_items

    # when
    payment_lines = create_payment_lines_information(payment_for_checkout, manager)

    # then
    assert payment_lines == get_expected_payment_lines(checkout_with_items, manager)


def test_create_payment_lines_checkout_partial_payment(
    payment_for_checkout, checkout_with_items, manager
):
    # given
    payment_difference = Decimal("7.34")
    payment_for_checkout.partial = True
    payment_for_checkout.total -= payment_difference
    payment_for_checkout.captured_amount -= payment_difference

    # when
    payment_lines = create_payment_lines_information(payment_for_checkout, manager)

    # then
    expected_payment_lines = get_expected_payment_lines(checkout_with_items, manager)
    expected_payment_lines.append(
        PaymentLineData(
            gross=-payment_difference,
            variant_id=PARTIAL_PAYMENT_DIFFERENCE_LINE_ID,
            product_name="Partial payment difference",
            quantity=1,
        )
    )
    assert payment_lines == expected_payment_lines
