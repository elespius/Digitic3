import os
from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import Q
from django_prices.models import MoneyField

from ..app.models import App
from ..core import TimePeriodType
from ..core.models import ModelWithMetadata
from ..core.permissions import GiftcardPermissions
from . import GiftCardExpiryType


class GiftCardQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=date),
            start_date__lte=date,
            is_active=True,
        )


class GiftCard(ModelWithMetadata):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )
    created_by_email = models.EmailField(null=True, blank=True)
    used_by_email = models.EmailField(null=True, blank=True)
    app = models.ForeignKey(
        App,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    expiry_date = models.DateField(null=True, blank=True)
    expiry_type = models.CharField(
        max_length=32,
        choices=GiftCardExpiryType.CHOICES,
        # to removed after updating GiftCard mutations
        default=GiftCardExpiryType.EXPIRY_DATE,
    )
    expiry_period_type = models.CharField(
        max_length=32, choices=TimePeriodType.CHOICES, null=True, blank=True
    )
    expiry_period = models.PositiveIntegerField(null=True, blank=True)

    tag = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_used_on = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField(
        default=date.today
    )  # DEPRECATED: to remove in Saleor 4.0
    product = models.ForeignKey(
        "product.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gift_cards",
    )

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        default=os.environ.get("DEFAULT_CURRENCY", "USD"),
    )

    initial_balance_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    initial_balance = MoneyField(
        amount_field="initial_balance_amount", currency_field="currency"
    )

    current_balance_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    current_balance = MoneyField(
        amount_field="current_balance_amount", currency_field="currency"
    )

    objects = models.Manager.from_queryset(GiftCardQueryset)()

    class Meta:
        ordering = ("code",)
        permissions = (
            (GiftcardPermissions.MANAGE_GIFT_CARD.codename, "Manage gift cards."),
        )

    @property
    def display_code(self):
        return "****%s" % self.code[-4:]
