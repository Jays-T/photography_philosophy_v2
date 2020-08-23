# Core logic of this code adapted from Code Institute Boutique Ado project

from django.http import HttpResponse

from .models import Order, OrderLineItem
from products.models import Product

import json
import time


class Stripe_Web_Hook_Handler:
    """To Handle Stripe Webhooks"""

    def __init__(self, request):
        self.request = request

    def handle_event(self, event):
        """
        Handle any generic or unexpected webhook event
        """
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200)

    def on_payment_intent_succeeded(self, event):
        """
        Handle Stripe payment_intent.succeeded webhook if successful
        """
        intent = event.data.object
        paymentid = intent.id
        bag = intent.metadata.bag
        save_info = intent.metadata.save_info

        billing_details = intent.charges.data[0].billing_details
        shipping_details = intent.shipping
        grand_total = round(intent.charges.data[0].amount / 100, 2)

        """Clean data in the shipping details"""
        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        """Set order to not_exists"""
        order_exists = False
        attempt = 1
        """Try 5 times to get the order details from the form"""
        while attempt <= 5:
            try:
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    email__iexact=billing_details.email,
                    phone_number__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    postcode__iexact=shipping_details.address.postal_code,
                    town_or_city__iexact=shipping_details.address.city,
                    street_address1__iexact=shipping_details.address.line1,
                    street_address2__iexact=shipping_details.address.line2,
                    county__iexact=shipping_details.address.state,
                    grand_total=grand_total,
                    original_bag=bag,
                    stripe_paymentid=paymentid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)
        """Add ^^ one second delay between attempts"""
        if order_exists:
            return HttpResponse(
                content=f'Webhook received: {event["type"]} | SUCCESS: Verified order already in database',
                status=200)
        else:
            """If can't find order, attempt to get order from data_cache"""
            order = None
            try:
                order = Order.objects.create(
                    full_name=shipping_details.name,
                    email=billing_details.email,
                    phone_number=shipping_details.phone,
                    country=shipping_details.address.country,
                    postcode=shipping_details.address.postal_code,
                    town_or_city=shipping_details.address.city,
                    street_address1=shipping_details.address.line1,
                    street_address2=shipping_details.address.line2,
                    county=shipping_details.address.state,
                    original_bag=bag,
                    stripe_paymentid=paymentid,
                )
                for item_id, item_data in json.loads(bag).items():
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_line_item = OrderLineItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_line_item.save()
                    else:
                        for size, quantity in item_data['items_by_size'].items():
                            order_line_item = OrderLineItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size,
                            )
                            order_line_item.save()
            except Exception as e:
                if order:
                    order.delete()
                    """If failed then delete order and send status 500 to Stripe"""
                return HttpResponse(
                    content=f'Webhook received: {event["type"]} | ERROR: {e}',
                    status=500)
        """If successful return 200 response"""
        return HttpResponse(
            content=f'Webhook received: {event["type"]} | SUCCESS: Created order in webhook',
            status=200)

    def on_payment_intent_payment_failed(self, event):
        """
        Handle Stripe payment_intent.payment_failed webhook if failed
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
