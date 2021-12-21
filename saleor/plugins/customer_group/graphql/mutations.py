from typing import DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError

from saleor.plugins.customer_group.graphql.errors import CustomerGroupError

from ....graphql.core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from .. import models
from .types import CustomerGroupType


class CustomerGroupInput(graphene.InputObjectType):
    is_active = graphene.Boolean(
        description="isActive flag to enable or diable customer group from mustations"
    )


class CustomerGroupCreateInput(CustomerGroupInput):
    name = graphene.String(description="Name of the customer group.", required=True)
    description = graphene.String(description="description of the customer group.")
    customers = graphene.List(
        graphene.ID,
        description="Customer IDs to add to the group",
        name="customers",
    )


class CustomerGroupCreate(ModelMutation):
    class Arguments:
        input = CustomerGroupCreateInput(
            required=True, description="Fields required to create customer group."
        )

    class Meta:
        description = "Creates new customer group."
        model = models.CustomerGroup
        error_type_class = CustomerGroupError

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data)
        return cleaned_input


class CustomerGroupUpdateInput(CustomerGroupInput):
    name = graphene.String(description="name of customer group")
    description = graphene.String(description="description of customer group")
    customers = graphene.List(
        graphene.ID,
        description="customers related to the customer group",
        name="customers",
        required=False,
    )


class CustomerGroupUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a customer group to update")
        input = CustomerGroupUpdateInput(
            description="Fields required to update a customer group", required=True
        )

    class Meta:
        description = "Update a customer group"
        model = models.CustomerGroup
        error_type_class = CustomerGroupError

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data)
        return cleaned_input


class CustomerGroupDeleteInput(graphene.InputObjectType):
    customer_group_id = graphene.ID(
        required=True,
        description="ID of customer group to delete the group",
    )


class CustomerGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of customrt group to delete")
        input = CustomerGroupDeleteInput(
            description="Fields required to delete a customer group"
        )

    class Meta:
        description = "delete the customer group"
        model = models.CustomerGroup
        error_type_class = CustomerGroupError

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated


ErrorType = DefaultDict[str, List[ValidationError]]


class BaseCustomerGroupListingMutation(BaseMutation):
    """Base CustomerGroup listing mutation with basic CustomerGroup ."""

    class Meta:
        abstract = True

    @classmethod
    def clean_channels(
        cls,
        info,
        input,
        errors: ErrorType,
        error_code,
        input_source="add_customer_groups",
    ) -> Dict:
        add_groups = input.get(input_source, [])
        add_groups_ids = [group["customer_group_id"] for group in add_groups]
        remove_groups_ids = input.get("remove_groups", [])

        if errors:
            return {}
        customer_groups_to_add: List["models.CustomerGroup"] = []
        if add_groups_ids:
            customer_groups_to_add = cls.get_nodes_or_error(  # type: ignore
                add_groups_ids, "customer_group_id", CustomerGroupType
            )

        cleaned_input = {input_source: [], "remove_groups": remove_groups_ids}

        for customer_group_listing, customer_group in zip(
            add_groups, customer_groups_to_add
        ):
            customer_group_listing["customer_group"] = customer_group
            cleaned_input[input_source].append(customer_group_listing)

        return cleaned_input


class CustomerGroupActivate(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroupType, description="Activated CustomerGroup."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the CustomerGroup to activate."
        )

    class Meta:
        description = "Activate a CustomerGroup."
        error_type_class = CustomerGroupError

    @classmethod
    def clean_customer_group_availability(cls, customer_group):
        if customer_group.is_active:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This customer group is already activated.",
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        customer_group = cls.get_node_or_error(
            info, data["id"], only_type=CustomerGroupType
        )
        cls.clean_customer_group_availability(customer_group)
        customer_group.is_active = True
        customer_group.save(update_fields=["is_active"])

        return CustomerGroupActivate(customer_group=customer_group)


class CustomerGroupDeactivate(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroupType, description="Deactivated customer_group."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the customer_group to deactivate."
        )

    class Meta:
        description = "Deactivate a customer_group."
        error_type_class = CustomerGroupError

    @classmethod
    def clean_customer_group_availability(cls, customer_group):
        if customer_group.is_active is False:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This customer_group is already deactivated.",
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        customer_group = cls.get_node_or_error(
            info, data["id"], only_type=CustomerGroupType
        )
        cls.clean_customer_group_availability(customer_group)
        customer_group.is_active = False
        customer_group.save(update_fields=["is_active"])

        return CustomerGroupDeactivate(customer_group=customer_group)
