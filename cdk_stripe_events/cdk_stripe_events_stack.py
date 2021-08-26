from aws_cdk import core as cdk
from aws_cdk import aws_apigateway
from aws_cdk import aws_apigatewayv2
from aws_cdk import aws_apigatewayv2_integrations
from aws_cdk import aws_logs
from aws_cdk import aws_secretsmanager
from aws_cdk import aws_lambda
from aws_cdk import aws_lambda_python
from aws_cdk import aws_iam


class CdkStripeEventsStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Location for the Stripe signing secret
        stripe_signing_secret = aws_secretsmanager.Secret(
            self,
            "StripeSigningSecret",
            description="Signing secret for authenticating Stripe webhook calls",
        )

        # The API used as the Stripe webhook
        webhook_api = aws_apigatewayv2.HttpApi(
            self,
            id="StripeWebhookApi",
            create_default_stage=False,
        )

        # Manually create the default stage to allow logging configuration
        default_stage = aws_apigatewayv2.CfnStage(
            self,
            "DefaultStage",
            api_id=webhook_api.api_id,
            stage_name="$default",
            auto_deploy=True,
        )
        cdk.Tags.of(default_stage).add("Project", "StripeWebhookIngestion")

        # Create a log group for API access logging
        stripe_log_group = aws_logs.LogGroup(
            self,
            "StripeWebhookLogGroup",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Setup the access log format
        default_stage.access_log_settings = {
            "destinationArn": stripe_log_group.log_group_arn,
            "format": aws_apigateway.AccessLogFormat.clf().to_string(),
        }

        # Lambda function to check signature and push to SQS
        stripe_webhook_ingester_function = aws_lambda_python.PythonFunction(
            self,
            "StripeWebhookIngester",
            description="Handles incoming Stripe webhook events by validating the signature and then pushing the event to the event bus",
            environment={
                "STRIPE_SIGNING_SECRET_ARN": stripe_signing_secret.secret_arn,
            },
            entry="functions/stripe_webhook_ingester",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            tracing=aws_lambda.Tracing.ACTIVE,
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

        # Integrate the root route with the Lambda function
        aws_apigatewayv2.HttpRoute(
            self,
            "RootRoute",
            http_api=webhook_api,
            route_key=aws_apigatewayv2.HttpRouteKey.with_(
                path="/", method=aws_apigatewayv2.HttpMethod.POST
            ),
            integration=aws_apigatewayv2_integrations.LambdaProxyIntegration(
                handler=stripe_webhook_ingester_function
            ),
        )
