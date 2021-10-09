#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from stacks.webhook import WebhookStack

app = cdk.App()

webhook_stack = WebhookStack(
    app,
    "CdkStripeWebhook",
    description="Creates a webhook API to receive Stripe events. Events are validated and sent to Event Bridge",
)

cdk.Tags.of(webhook_stack).add("Project", "StripeWebhook")

app.synth()
