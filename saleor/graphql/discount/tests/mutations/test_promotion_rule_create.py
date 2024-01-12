from decimal import Decimal
from unittest.mock import ANY, patch

import graphene
from django.test import override_settings

from .....discount import PromotionEvents
from .....discount.error_codes import PromotionRuleCreateErrorCode
from .....discount.models import PromotionEvent
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardTypeEnum, RewardValueTypeEnum

PROMOTION_RULE_CREATE_MUTATION = """
    mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
        promotionRuleCreate(input: $input) {
            promotionRule {
                id
                name
                description
                promotion {
                    id
                    events {
                        ... on PromotionEventInterface {
                            type
                        }
                        ... on PromotionRuleEventInterface {
                            ruleId
                    }
                }
                }
                channels {
                    id
                }
                rewardValueType
                rewardValue
                cataloguePredicate
                orderPredicate
            }
            errors {
                field
                code
                message
                rulesLimit
                exceedBy
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_promotion_rule_create_by_staff_user(
    update_discounted_prices_task_mock,
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
            {
                "productPredicate": {
                    "ids": [graphene.Node.to_global_id("Product", product.id)]
                }
            },
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    update_discounted_prices_task_mock.assert_called_once_with([product.id])
    rule = promotion.rules.last()
    promotion_rule_created_mock.assert_called_once_with(rule)


@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_promotion_rule_create_by_app(
    update_discounted_prices_task_mock,
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_CREATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    update_discounted_prices_task_mock.assert_called_once_with(
        [category.products.first().id]
    )


@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_promotion_rule_create_by_customer(
    update_discounted_prices_task_mock,
    api_client,
    description_json,
    channel_USD,
    category,
    collection,
    promotion,
):
    # given
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)
    assert_no_permission(response)
    update_discounted_prices_task_mock.assert_not_called()


def test_promotion_rule_create_missing_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 2
    assert {
        "code": PromotionRuleCreateErrorCode.REQUIRED.name,
        "field": "cataloguePredicate",
        "message": ANY,
    } in errors
    assert {
        "code": PromotionRuleCreateErrorCode.REQUIRED.name,
        "field": "orderPredicate",
        "message": ANY,
    } in errors
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_multiple_errors(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert len(errors) == 2
    expected_errors = [
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValue",
            "message": ANY,
        },
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors

    assert promotion.rules.count() == rules_count


def test_promotion_rule_invalid_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                },
                "AND": [
                    {
                        "productPredicate": {
                            "ids": [graphene.Node.to_global_id("Product", product.id)]
                        }
                    }
                ],
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_invalid_order_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_PLN,
    promotion_without_rules,
):
    # given
    promotion = promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    order_predicate = {
        "OR": [
            {
                "discountedObjectPredicate": {
                    "baseSubtotalPrice": {"range": {"gte": 100}}
                },
                "AND": [
                    {
                        "discountedObjectPredicate": {
                            "baseSubtotalPrice": {"range": {"lte": 500}}
                        }
                    }
                ],
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "orderPredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_invalid_price_precision(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10.12345")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID_PRECISION.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_fixed_reward_value_multiple_currencies(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_fixed_reward_no_channels(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.MISSING_CHANNELS.name
    assert errors[0]["field"] == "channels"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_percentage_value_above_100(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("110")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_promotion_rule_create_clears_old_sale_id(
    update_discounted_prices_task_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    promotion_converted_from_sale,
):
    # given
    promotion = promotion_converted_from_sale
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    assert promotion.old_sale_id
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            }
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    update_discounted_prices_task_mock.assert_called_once_with([product.id])

    promotion.refresh_from_db()
    assert promotion.old_sale_id is None


def test_promotion_rule_create_events(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    variant,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
        ]
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "name": "test promotion rule",
            "promotion": promotion_id,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }
    event_count = PromotionEvent.objects.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    assert not data["errors"]

    events = data["promotionRule"]["promotion"]["events"]
    assert len(events) == 1
    assert PromotionEvent.objects.count() == event_count + 1
    assert PromotionEvents.RULE_CREATED.upper() == events[0]["type"]

    assert events[0]["ruleId"] == data["promotionRule"]["id"]


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
@patch("saleor.product.tasks.update_discounted_prices_task.delay")
def test_promotion_rule_create_serializable_decimal_in_predicate(
    update_discounted_prices_task_mock,
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    catalogue_predicate = {
        "productPredicate": {"minimalPrice": {"range": {"gte": "25"}}}
    }
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "promotion": promotion_id,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    assert not data["errors"]
    assert data["promotionRule"]["cataloguePredicate"] == catalogue_predicate


def test_promotion_rule_create_multiple_predicates(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 2
    assert {
        "code": PromotionRuleCreateErrorCode.MIXED_PREDICATES.name,
        "field": "cataloguePredicate",
        "message": ANY,
    } in errors
    assert {
        "code": PromotionRuleCreateErrorCode.MIXED_PREDICATES.name,
        "field": "orderPredicate",
        "message": ANY,
    } in errors
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_mixed_predicates_order(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    promotion,
):
    # given
    assert promotion.rules.first().catalogue_predicate
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MIXED_PROMOTION_PREDICATES.name
    )
    assert errors[0]["field"] == "orderPredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_mixed_predicates_catalogue(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    promotion_with_order_rule,
):
    # given
    promotion = promotion_with_order_rule
    assert promotion.rules.first().order_predicate
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MIXED_PROMOTION_PREDICATES.name
    )
    assert errors[0]["field"] == "cataloguePredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    promotion_without_rules,
):
    # given
    promotion = promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100}}}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_reward_type_with_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.INVALID.name
    assert errors[0]["field"] == "rewardType"
    assert promotion.rules.count() == rules_count


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
@patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_promotion_rule_create_order_predicate(
    update_products_discounted_prices_for_promotion_task_mock,
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    promotion_without_rules,
):
    # given
    promotion = promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }

    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert rule_data["channels"][0]["id"] == channel_id
    assert rule_data["orderPredicate"] == order_predicate
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1
    rule = promotion.rules.last()
    promotion_rule_created_mock.assert_called_once_with(rule)


def test_promotion_rule_create_mixed_currencies_for_price_based_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    promotion_without_rules,
):
    # given
    promotion = promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]

    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "orderPredicate": order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert (
        errors[0]["code"]
        == PromotionRuleCreateErrorCode.MULTIPLE_CURRENCIES_NOT_ALLOWED.name
    )
    assert errors[0]["field"] == "channels"
    assert promotion.rules.count() == rules_count


@override_settings(CHECKOUT_AND_ORDER_RULES_LIMIT=1)
def test_promotion_rule_create_exceeds_rules_number_limit(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    promotion_without_rules,
):
    # given
    promotion = promotion_without_rules
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.PERCENTAGE.name
    reward_type = RewardTypeEnum.SUBTOTAL_DISCOUNT.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    checkout_and_order_predicate = {
        "discountedObjectPredicate": {"subtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.pk)

    promotion.rules.create(
        name="existing promotion rule",
        promotion=promotion,
        checkout_and_order_predicate=checkout_and_order_predicate,
        reward_value_type=reward_value_type,
        reward_value=reward_value,
        reward_type=reward_type,
    )

    rules_count = promotion.rules.count()
    assert rules_count == 1

    variables = {
        "input": {
            "promotion": promotion_id,
            "channels": [channel_id],
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "rewardType": reward_type,
            "checkoutAndOrderPredicate": checkout_and_order_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.RULES_NUMBER_LIMIT.name
    assert errors[0]["field"] == "checkoutAndOrderPredicate"
    assert errors[0]["rulesLimit"] == 1
    assert errors[0]["exceedBy"] == 1
    assert promotion.rules.count() == rules_count
