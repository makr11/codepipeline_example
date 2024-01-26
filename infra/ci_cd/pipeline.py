from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
)
from constructs import Construct

from pathlib import Path


class Pipeline(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_output = codepipeline.Artifact("SourceArtifact")
        synth_output = codepipeline.Artifact("SynthArtifact")

        pipeline = codepipeline.Pipeline(self, "Pipeline", pipeline_name="example-pipeline")

        source_stage = pipeline.add_stage(stage_name="Source")
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="ExampleSource",
            owner="makr11",
            repo="codepipeline_example",
            output=source_output,
            branch="master",
            connection_arn=f"arn:aws:codestar-connections:{self.region}:{self.account}:connection/749e103c-daf9-474c-84c4-b8355c055249"
        )
        source_stage.add_action(source_action)
        
        # ========= Service Build Actions =========
        build_stage = pipeline.add_stage(stage_name="Build")

        build_asset_role = iam.Role(
            self, "BuildAssetRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser"),
            ]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="BuildService",
            project=codebuild.PipelineProject(
                self, "Build",
                role=build_asset_role,
                project_name="build_asset",
                build_spec=codebuild.BuildSpec.from_source_filename("infra/ci_cd/buildspecs/build_asset.yml"),
                environment=codebuild.BuildEnvironment(
                    privileged=True,
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    compute_type=codebuild.ComputeType.SMALL,
                ),
            ),
            input=source_output,
            environment_variables={
                "ACCOUNT": codebuild.BuildEnvironmentVariable(value=self.account),
                "AWS_REGION": codebuild.BuildEnvironmentVariable(value=self.region),
                "ECR_REPOSITORY_NAME": codebuild.BuildEnvironmentVariable(value=f"cdk-hnb659fds-container-assets-{self.account}-{self.region}"),
                "FOLDER_PATH": codebuild.BuildEnvironmentVariable(value="service"),
            },
        )
        
        build_stage.add_action(build_action)

        synth_role = iam.Role(
                self, "CDKAssetsTransferRole",
                assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
                inline_policies={
                    "publish-assets": iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                actions=[
                                    "sts:AssumeRole",
                                ],
                                resources=[f"arn:aws:iam::{self.account}:role/cdk-hnb659fds-file-publishing-role-{self.account}-{self.region}"],
                                effect=iam.Effect.ALLOW,
                            ),
                        ],
                    ),
            }
        )

        build_infra_action = codepipeline_actions.CodeBuildAction(
            run_order=2,
            action_name="CDKSynth",
            project=codebuild.PipelineProject(
                self, "CDKSynthBuild",
                project_name="cdk-synth",
                role=synth_role,
                build_spec=codebuild.BuildSpec.from_source_filename("infra/ci_cd/buildspecs/synth.yml"),
                environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    compute_type=codebuild.ComputeType.SMALL
                ),
            ),
            input=source_output,
            outputs=[synth_output],
            environment_variables={
                "ACCOUNT": codebuild.BuildEnvironmentVariable(value=self.account),
                "AWS_REGION": codebuild.BuildEnvironmentVariable(value=self.region),
                "SERVICE_IMAGE_TAG": codebuild.BuildEnvironmentVariable(value=build_action.variable("IMAGE_TAG")),
            }
        )
        build_stage.add_action(build_infra_action)
        # ========= Service Build Actions =========

        # ========= Deploy Service =========
        deployment_stage = pipeline.add_stage(stage_name="DeployInfraTemplates")
        
        deployment_stage.add_action(
            codepipeline_actions.CloudFormationCreateUpdateStackAction(
                action_name="ExampleService",
                template_path=synth_output.at_path("ServiceStack.template.json"),
                stack_name="service-stack",
                admin_permissions=True,
                extra_inputs=[synth_output]
            ),
        )
