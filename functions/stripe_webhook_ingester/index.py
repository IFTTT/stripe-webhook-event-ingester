import json
import stripe
import boto3
import botocore
import os
import logging

STRIPE_SIGNATURE_HEADER = "stripe-signature"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secrets_client = boto3.client("secretsmanager")
sqs_client = boto3.client("sqs")


def handler(event, context):
    logger.info(f"Lambda event: {json.dumps(event)}")

    # Required environment variable
    stripe_signing_secret_arn = os.getenv("STRIPE_SIGNING_SECRET_ARN")
    if not stripe_signing_secret_arn:
        logger.error(
            f"Unable to get Stripe signing secret from environment: STRIPE_SIGNING_SECRET_ARN"
        )

        return {"statusCode": 500}

    # Required environment variable
    stripe_event_queue_url = os.getenv("STRIPE_EVENT_QUEUE_URL")
    if not stripe_event_queue_url:
        logger.error(
            f"Unable to get Stripe event queue url from environment: STRIPE_EVENT_QUEUE_URL"
        )

        return {"statusCode": 500}

    # Required secret
    try:
        stripe_signing_secret = secrets_client.get_secret_value(
            SecretId=stripe_signing_secret_arn
        )["SecretString"]
    except botocore.exceptions.ClientError as e:
        logger.error(
            f"Unable to get Stripe signing secret from Secrets Manager: {stripe_signing_secret_arn}"
        )

        return {"statusCode": 500}

    # Required header
    if STRIPE_SIGNATURE_HEADER not in event["headers"]:
        logger.error(f"Stripe signature header {STRIPE_SIGNATURE_HEADER} not found")

        return {"statusCode": 400}

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
        return {"statusCode": 400}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature!\n{e}")
        return {"statusCode": 400}

    # Push the message to the SQS queue
    sqs_client.send_message(
        QueueUrl=stripe_event_queue_url,
        MessageBody=json.dumps(authenticated_stripe_webhook_event),
    )

    return {"statusCode": 200}
