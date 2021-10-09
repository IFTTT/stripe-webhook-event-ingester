import json
import datetime

import stripe
import boto3
import os
import logging

from aws_xray_sdk.core import patch_all
from aws_xray_sdk.core import xray_recorder

STRIPE_SIGNATURE_HEADER = "Stripe-Signature"

# ===========================================================================
# Setup various reusable objects outside the handler to improve performance
# ===========================================================================

# Logger can be reused
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Instrument libraries for AWS XRay
patch_all()

# Clients can be reused
secrets_client = boto3.client("secretsmanager")
eventbridge_client = boto3.client("events")

# Required environment variables
stripe_signing_secret_arn = os.environ["STRIPE_SIGNING_SECRET_ARN"]

# Secret can be reused
stripe_signing_secret = secrets_client.get_secret_value(
    SecretId=stripe_signing_secret_arn
)["SecretString"]


def handler(event, context):
    """Receives Stripe webhook events and validates them using the 'stripe-signature' header and
       the Stripe Signing Secret. Once validated, events are sent to the default event bus in
       EventBridge with "Source=stripe" and "DetailType=<Stripe Event>.type".

    Required Environment:
        STRIPE_SIGNING_SECRET_ARN = ARN for the Stripe Signing Secret in Secrets Manager

    Args:
        event (Dict): Stripe webhook event
        context (Dict): Ignored

    Returns:
        Dict: 200 if event was successfully processed; 500 otherwise
    """
    logger.info(f"Lambda event: {json.dumps(event)}")

    # ========================================================================
    # Required headers
    # ========================================================================
    if STRIPE_SIGNATURE_HEADER not in event["headers"]:
        logger.error(f"Stripe signature header {STRIPE_SIGNATURE_HEADER} not found")

        return {"statusCode": 500}

    # The Stripe signature is passed via a request header
    stripe_signature = str(event["headers"][STRIPE_SIGNATURE_HEADER])

    try:
        # Authenticate the message using the signature and signing secret
        authenticated_stripe_webhook_event = stripe.Webhook.construct_event(
            event["body"],
            stripe_signature,
            stripe_signing_secret,
        )
    except ValueError as e:
        logger.error(f"Could not validate event!\n{e}")
        return {"statusCode": 500}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature!\n{e}")
        return {"statusCode": 500}

    eventbridge_client.put_events(
        Entries=[
            {
                "Time": datetime.datetime.now(),
                "Source": "stripe",
                "DetailType": authenticated_stripe_webhook_event["type"],
                "Detail": json.dumps(authenticated_stripe_webhook_event),
            }
        ]
    )

    return {"statusCode": 200}
