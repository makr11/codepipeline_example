import aws_cdk as core
import aws_cdk.assertions as assertions

from codepipeline_example.codepipeline_example_stack import CodepipelineExampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in codepipeline_example/codepipeline_example_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CodepipelineExampleStack(app, "codepipeline-example")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
