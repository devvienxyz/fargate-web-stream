from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    core,
    aws_elasticloadbalancingv2 as elbv2,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class AppStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)  # VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=2)  # Create a new VPC

        # ECS Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Define Fargate Service
        task_definition = ecs.FargateTaskDefinition(self, "MyTaskDef")

        container = task_definition.add_container(
            "MyContainer",
            image=ecs.ContainerImage.from_registry(
                "amazon/amazon-ecs-sample"
            ),  # Example image
            memory_limit_mib=512,
        )

        container.add_port_mappings(ecs.PortMapping(container_port=80))

        # Fargate Service with Load Balancer
        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "MyFargateService",
            cluster=cluster,
            task_definition=task_definition,
            public_load_balancer=True,  # Set to False for internal LB
        )
        self.setup_api_gw_w_throttling()

    def setup_api_gw_w_throttling(self):
        self.api = apigateway.LambdaRestApi(
            self,
            "MyApi",
            handler=self.fargate_service.service.service_arn,  # Link to the Fargate service
            proxy=False,
        )

        self.api.add_resource("app")
        method = self.api.add_method(
            "GET",
            apigateway.Integration(
                type=apigateway.IntegrationType.AWS_PROXY,
                integration_http_method="POST",
                uri=self.fargate_service.service.service_arn,
            ),
            method_response={
                "status_code": "200",
            },
        )

        # Configure Throttling
        method.add_method_response(
            status_code="200",
            response_parameters={
                "method.response.header.Access-Control-Allow-Origin": True,
            },
        )

        self.api.deployment_stage = apigateway.Stage(
            self,
            "ProdStage",
            deployment=self.api.deployment,
            throttling_burst_limit=100,
            throttling_rate_limit=50,  # per second
        )

        self.fargate_service.service.grant_invoke(self.api.arn)

    def __app_config(self):
        conf_file = open("./config.json", "r")
        return conf_file.read()

    def create_shared_resources(self):
        repository_name = self.__app_config().get("repository_name")
        # Default is all AZs in the region
        self.vpc = ec2.Vpc(self, "SharedVpc", max_azs=2)
        self.cluster = ecs.Cluster(self, "SharedCluster", vpc=self.vpc)
        self.repository = ecr.Repository(
            self, repository_name, repository_name=repository_name
        )

    def provision_ecs_ecr(self):
        task_defn_id = self.__app_config().get("task_defn_id")
        fargate_service_id = self.__app_config().get("fargate_service_id")
        task_definition = ecs.FargateTaskDefinition(self, task_defn_id)
        container = task_definition.add_container(
            f"{task_defn_id}Container",
            image=ecs.ContainerImage.from_ecr_repository(self.repository),
            memory_limit_mib=512,
            port_mappings=[ecs.PortMapping(container_port=80)],
            environment={},
        )

        self.fargate_service = ecs.FargateService(
            self,
            fargate_service_id,
            cluster=self.cluster,
            task_definition=task_definition,
            desired_count=1,
            assign_public_ip=False,
        )

        # Grant the ECS task role permission to pull from ECR
        self.repository.grant_pull(task_definition.task_role)
