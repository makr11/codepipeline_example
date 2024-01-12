# S3 bucket without public access which has a trigger on PUT and REMOVE events to invoke lambda function
# defined with AWS CDK
import os

from aws_cdk import (
    Stack,
    aws_lambda as lmb,
    aws_logs as logs,
    aws_ecr as ecr,
)

from constructs import Construct


class Service(Stack):
    def __init__(self, scope: Construct, _id):
        super().__init__(scope, _id)

        ecr_repo = ecr.Repository.from_repository_name(self, "DocProcessorRepo", repository_name=f"cdk-hnb659fds-container-assets-{self.account}-{self.region}")

        lmb.DockerImageFunction(
            self, "Service",
            function_name=f"service-example",
            log_retention=logs.RetentionDays.ONE_MONTH,
            code=lmb.DockerImageCode.from_ecr(repository=ecr_repo, tag_or_digest=os.getenv("SERVICE_IMAGE_TAG"))
        )
