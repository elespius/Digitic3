from django.db.models import Q
from ..order import Order
from ..product.models import Product
from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import ParseError
from rest_framework import status
from rest_framework.response import Response
from .serializers import OrderSerializer, ProductSerializer, GetWebhookRequestSerializer
from .authentication import WombatAuthentication


class OrderList(generics.ListAPIView):
    queryset = Order.objects.prefetch_related(
        'groups', 'groups__items', 'payments').select_related(
        'billing_address', 'shipping_address', 'user')
    serializer_class = OrderSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.prefetch_related('variants',
                                                'variants__stock',
                                                'images',
                                                'attributes')
    serializer_class = ProductSerializer


def get_serialized_data(request_serializer, queryset, serializer, wombat_name):
    if not request_serializer.is_valid():
        raise ParseError()
    request_id = request_serializer.data.get('request_id')
    query_filter = request_serializer.get_query_filter()
    data = queryset.filter(query_filter)
    serialized = serializer(data, many=True)
    response = {
        'request_id': request_id,
        wombat_name: serialized.data
    }
    return Response(data=response, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((WombatAuthentication,))
def get_orders_webhook(request):
    request_serializer = GetWebhookRequestSerializer(
        data=request.data, since_query_field='last_status_change')
    return get_serialized_data(request_serializer,
                               queryset=Order.objects.with_all_related(),
                               serializer=OrderSerializer,
                               wombat_name='orders')


@api_view(['POST'])
@authentication_classes((WombatAuthentication,))
def get_products_webhook(request):
    request_serializer = GetWebhookRequestSerializer(
        data=request.data, since_query_field='updated_at')
    return get_serialized_data(request_serializer,
                               queryset=Product.objects.with_all_related(),
                               serializer=ProductSerializer,
                               wombat_name='products')
