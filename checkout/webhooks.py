from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from checkout.webhook_handlers import Stripe_Web_Hook_Handler

import stripe


@require_POST
@csrf_exempt
def webhook(request):
    """Listen for webhooks from Stripe"""
    # Setup webhooks
    web_hook_secret = settings.STRIPE_WH_SECRET
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Get webhook data and verify signature
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, web_hook_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(content=e, status=400)

    handler = Stripe_Web_Hook_Handler(request)
    event_map = {
        'payment_intent.succeeded': handler.on_payment_intent_succeeded,
        'payment_intent.payment_failed': handler.on_payment_intent_payment_failed,
    }

    event_type = event['type']

    event_handler = event_map.get(event_type, handler.handle_event)

    response = event_handler(event)
    return response
