import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.error_codes import OrderErrorCode
from ...core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order


class DraftOrderDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a product to delete.")
        external_reference = graphene.String(
            required=False, description="External ID of a product to delete."
        )

    class Meta:
        description = "Deletes a draft order."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        if instance.status != OrderStatus.DRAFT:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to non-draft order.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_instance(info, **data)
        manager = load_plugin_manager(info.context)
        with traced_atomic_transaction():
            response = super().perform_mutation(_root, info, **data)
            cls.call_event(manager.draft_order_deleted, order)
        return response
