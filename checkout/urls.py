from django.urls import path
from . import views
from .webhooks import webhook

urlpatterns = [
    path('', views.checkout, name='checkout'),
    path('checkout_success/<order_number>', views.checkout_success, name='checkout_success'),
    path('checkout_data_cache/', views.checkout_data_cache, name='checkout_data_cache'),
    path('wh/', webhook, name='webhook'),
]
