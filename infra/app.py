#!/usr/bin/env python3
import aws_cdk as cdk

from ci_cd.pipeline import Pipeline
from service.infra import Service


app = cdk.App()

Pipeline(app, "PipelineStack")
Service(app, "ServiceStack")

app.synth()