
# Stripe Webhook Event Ingester

![Architecture](/assets/architecture.png)

This is an AWS CDK-based project for ingesting Stripe webhook events into an SQS queue.

Stripe uses a message digest code to allow clients to verify the integrity of webhook events. Stripe signs event messages that allow the receiver to verify the message was signed using a shared secret.

See: https://stripe.com/docs/webhooks/signatures

## The pipeline

- An API endpoint that can be set as the Stripe webhook endpoint
- A Lambda function that receives incoming webhook events and verifies the signature
- Authenticated events are sent to the EventBridge on the `$default` bus

## Setup

- Create the virtual environment: `python3 -m venv .venv`
- Enable the virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Deploy the stack: `cdk deploy`
- Create a Stripe Webhook endpoint: https://dashboard.stripe.com/webhooks
    - Set the URL to the URL of the API endpoint
    - Note that you'll find the Stripe Signing Secret used in the next step on this page
- Update the Stripe Signing Secret in the Secrets Manager: https://console.aws.amazon.com/secretsmanager/home

## Design Notes

- Events can arrive from Stripe [out of order](https://stripe.com/docs/webhooks/best-practices#event-ordering)