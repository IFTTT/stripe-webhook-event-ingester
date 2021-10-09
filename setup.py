import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cdk_stripe_webhook",
    version="1.0.0",
    description="A CDK based serverless application that creates a webhook API for Stripe events",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="IFTTT",
    package_dir={"": "functions"},
    packages=setuptools.find_packages(where="functions"),
    install_requires=[
        "aws-cdk.core==1.124.0",
        "aws_cdk.aws_apigatewayv2==1.124.0",
        "aws_cdk.aws_apigatewayv2_integrations==1.124.0",
        "aws_cdk.aws_apigatewayv2_authorizers==1.124.0",
        "aws_cdk.aws_iam==1.124.0",
        "aws_cdk.aws_logs==1.124.0",
        "aws_cdk.aws_sqs==1.124.0",
        "aws_cdk.aws_secretsmanager==1.124.0",
        "aws_cdk.aws_lambda==1.124.0",
        "aws_cdk.aws_lambda_event_sources==1.124.0",
        "aws_cdk.aws_lambda_python==1.124.0",
        "aws_xray_sdk==2.8.0",
        "stripe==2.60.0",
        "boto3==1.18.44",
        "boto3-stubs[essential, secretsmanager, events, sqs]==1.18.44",
        "black",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
    ],
)
