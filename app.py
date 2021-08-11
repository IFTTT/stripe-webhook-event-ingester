#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from cdk_stripe_events.cdk_stripe_events_stack import CdkStripeEventsStack

app = cdk.App()

stripe_events_stack = CdkStripeEventsStack(
    app,
    "CdkStripeEventsStack",
    description="Creates an API to access webhook events from Stripe. Events are validated with a signature check and pushed to an SQS queue.",
)

cdk.Tags.of(stripe_events_stack).add("Project", "StripeWebhookIngestion")

app.synth()
