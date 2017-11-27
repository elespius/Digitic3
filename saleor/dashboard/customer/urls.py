from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.customer_list, name='customers'),
    url(r'^(?P<pk>[0-9]+)/$', views.customer_details, name='customer-details'),
    url(r'^(?P<pk>[0-9]+)/promote/$', views.customer_promote_to_staff,
        name='customer-promote'),
    url(r'^ajax/users/$', views.ajax_users_list, name='ajax-users-list')
]
