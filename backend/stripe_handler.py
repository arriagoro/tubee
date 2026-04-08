"""
stripe_handler.py — Stripe payment integration for Tubee
Handles checkout sessions, webhooks, subscriptions, and customer portal.
"""

import stripe
import os
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Price IDs
PRICE_IDS = {
    "starter": os.environ.get("STRIPE_STARTER_PRICE_ID", "price_1TJjT2DH4sbUuaKWhKwNKo82"),
    "pro": os.environ.get("STRIPE_PRO_PRICE_ID", "price_1TJjTzDH4sbUuaKWSwn69u09"),
}


def create_checkout_session(
    price_id: str,
    user_email: str,
    user_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe checkout session and return the URL."""
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"user_id": user_id, "supabase_user_id": user_id},
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str, webhook_secret: str) -> dict:
    """Verify and construct a Stripe webhook event."""
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    return event


def get_customer_subscription(customer_id: str) -> dict | None:
    """Get active subscription for a customer."""
    subs = stripe.Subscription.list(customer=customer_id, status="active", limit=1)
    if subs.data:
        return subs.data[0]
    return None


def create_portal_session(customer_id: str, return_url: str) -> str:
    """Create Stripe customer portal session for managing subscriptions."""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def get_price_id(plan: str) -> str | None:
    """Get Stripe price ID for a plan name."""
    return PRICE_IDS.get(plan)


def get_plan_from_price_id(price_id: str) -> str | None:
    """Reverse lookup: get plan name from price ID."""
    for plan, pid in PRICE_IDS.items():
        if pid == price_id:
            return plan
    return None
