from aws_cdk import core as cdk
from aws_cdk import aws_logs
from aws_cdk import aws_secretsmanager
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_python
from aws_cdk.aws_lambda_event_sources import ApiEventSource
from aws_cdk import aws_iam


class WebhookStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Location for the Stripe signing secret
        stripe_signing_secret = aws_secretsmanager.Secret(
            self,
            "StripeSigningSecret",
            description="Signing secret for authenticating Stripe webhook calls",
        )

        # This layer contains all library dependencies and common helpers for the Lambda Functions
        common_layer = aws_lambda_python.PythonLayerVersion(
            self,
            "CommonLayer",
            description="Layer containing library dependencies and common packages shared by functions in this stack",
            layer_version_name="current",
            entry="layers",
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
        )

        # Lambda function to check signature and push to SQS
        stripe_webhook_ingester_function = aws_lambda_python.PythonFunction(
            self,
            "StripeWebhookIngester",
            description="Handles incoming Stripe webhook events by validating the signature and then pushing the event to the event bus",
            environment={
                "STRIPE_SIGNING_SECRET_ARN": stripe_signing_secret.secret_arn,
            },
            entry="functions/stripe_webhook_ingester",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            layers=[common_layer],
            log_retention=aws_logs.RetentionDays.TWO_WEEKS,
            tracing=aws_lambda.Tracing.ACTIVE,
            events=[ApiEventSource(method="POST", path="/")],
        )

        # Give the function permissions
        stripe_webhook_ingester_function.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                effect=aws_iam.Effect.ALLOW,
                resources=[stripe_signing_secret.secret_arn],
            )
        )

        stripe_webhook_ingester_function.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["events:PutEvents"],
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
            )
        )
