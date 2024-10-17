from unittest.mock import patch

from django.test import override_settings

from .....checkout.actions import call_checkout_event
from .....core.models import EventDelivery
from .....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .....webhook.transport.asynchronous.transport import send_webhook_request_async
from .....webhook.transport.utils import WebhookResponse, prepare_deferred_payload_data
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE = """
mutation checkoutLanguageCodeUpdate($id: ID, $languageCode: LanguageCodeEnum!){
  checkoutLanguageCodeUpdate(id: $id, languageCode: $languageCode){
    checkout{
      id
      languageCode
    }
    errors{
      field
      message
      code
    }
  }
}
"""


def test_checkout_update_language_code(
    user_api_client,
    checkout_with_gift_card,
):
    language_code = "PL"
    checkout = checkout_with_gift_card
    previous_last_change = checkout.last_change
    variables = {"id": to_global_id_or_none(checkout), "languageCode": language_code}

    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    content = get_graphql_content(response)
    data = content["data"]["checkoutLanguageCodeUpdate"]
    assert not data["errors"]

    assert data["checkout"]["languageCode"] == language_code
    checkout.refresh_from_db()
    assert checkout.language_code == language_code.lower()
    assert checkout.last_change != previous_last_change


def test_with_active_problems_flow(api_client, checkout_with_problems):
    # given
    channel = checkout_with_problems.channel
    channel.use_legacy_error_flow_for_checkout = False
    channel.save(update_fields=["use_legacy_error_flow_for_checkout"])

    variables = {
        "id": to_global_id_or_none(checkout_with_problems),
        "languageCode": "PL",
    }

    # when
    response = api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE,
        variables,
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["checkoutLanguageCodeUpdate"]["errors"]


@patch(
    "saleor.graphql.checkout.mutations.checkout_language_code_update.call_checkout_event",
    wraps=call_checkout_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async",
    wraps=send_webhook_request_async.apply_async,
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_checkout_update_language_code_triggers_webhooks(
    mocked_send_webhook_using_scheme_method,
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_checkout_event,
    setup_checkout_webhooks,
    settings,
    user_api_client,
    checkout_with_gift_card,
):
    # given
    mocked_send_webhook_using_scheme_method.return_value = WebhookResponse(content="")
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_webhook,
        shipping_filter_webhook,
        checkout_updated_webhook,
    ) = setup_checkout_webhooks(WebhookEventAsyncType.CHECKOUT_UPDATED)

    language_code = "PL"
    checkout = checkout_with_gift_card
    variables = {"id": to_global_id_or_none(checkout), "languageCode": language_code}

    # when
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_UPDATE_LANGUAGE_CODE, variables
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["checkoutLanguageCodeUpdate"]["errors"]

    deferred_payload_data = prepare_deferred_payload_data(
        subscribable_object=checkout, requestor=user_api_client.user, request_time=None
    )

    assert wrapped_call_checkout_event.called
    assert mocked_send_webhook_request_async.call_count == 1
    assert (
        mocked_send_webhook_request_async.call_args.kwargs["kwargs"][
            "deferred_payload_data"
        ]
        == deferred_payload_data
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 3
    assert not EventDelivery.objects.exclude(
        webhook_id=checkout_updated_webhook.id
    ).exists()

    shipping_methods_call, filter_shipping_call, tax_delivery_call = (
        mocked_send_webhook_request_sync.mock_calls
    )
    shipping_methods_delivery = shipping_methods_call.args[0]
    assert shipping_methods_delivery.webhook_id == shipping_webhook.id
    assert (
        shipping_methods_delivery.event_type
        == WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT
    )
    assert shipping_methods_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    )
    assert filter_shipping_call.kwargs["timeout"] == settings.WEBHOOK_SYNC_TIMEOUT

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id
