from ...utils import get_graphql_content

SHIPPING_METHOD_CHANNEL_LISTING_MUTATION = """
mutation ShippingMethodChannelListingUpdate(
    $id: ID!, $input: ShippingMethodChannelListingInput!
) {
  shippingMethodChannelListingUpdate(id: $id, input: $input) {
    errors {
      field
      code
      message
    }
    shippingMethod {
        id
        channelListings {
            minimumOrderPrice {
                amount
            }
            maximumOrderPrice {
                amount
            }
            price {
                amount
            }
            channel {
                id
            }
        }
    }
  }
}
"""


def create_shipping_method_channel_listing(
    staff_api_client,
    shipping_method_id,
    channel_id,
    price,
    minimum_order_price,
    maximum_order_price,
):
    variables = {
        "id": shipping_method_id,
        "input": {
            "addChannels": [
                {
                    "channelId": channel_id,
                    "price": price,
                    "maximumOrderPrice": maximum_order_price,
                    "minimumOrderPrice": minimum_order_price,
                }
            ]
        },
    }

    response = staff_api_client.post_graphql(
        SHIPPING_METHOD_CHANNEL_LISTING_MUTATION, variables
    )
    content = get_graphql_content(response)

    assert content["data"]["shippingMethodChannelListingUpdate"]["errors"] == []

    data = content["data"]["shippingMethodChannelListingUpdate"]["shippingMethod"]
    assert data["id"] is not None

    return data
