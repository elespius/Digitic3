from django import forms
from django.utils.translation import ugettext_lazy as _
from saleor.userprofile.models import Address


class UserAddressesForm(forms.Form):
    address = forms.ModelChoiceField(queryset=Address.objects.all(),
                                     empty_label=_('Add new address'),
                                     widget=forms.RadioSelect)

    def __init__(self, queryset, *args, **kwargs):
        super(UserAddressesForm, self).__init__(*args, **kwargs)
        self.fields['address'].queryset = queryset


class CopyShippingAddressForm(forms.Form):

    billing_same_as_shipping = forms.BooleanField(
        initial=True, required=False, label=_('Change billing address'))


class DeliveryForm(forms.Form):

    method = forms.ChoiceField(label=_('Shipping method'),
                               widget=forms.RadioSelect)

    def __init__(self, delivery_choices, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        method_field = self.fields['method']
        method_field.choices = delivery_choices
        if len(delivery_choices) == 1:
            method_field.initial = delivery_choices[0][1]


class AnonymousEmailForm(forms.Form):

    email = forms.EmailField()
