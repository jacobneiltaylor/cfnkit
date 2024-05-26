from troposphere import eks, iam, GetAtt, Ref, Parameter, Join

IPV4_SERVICE_PREFIX = "192.168.0.0/16"

ENABLED_LOGGING_TYPES = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler",
]

PUBLIC_ACCESS_PREFIXES = ["0.0.0.0/0"]

CLUSTER_TITLE = "EksCluster"


def _get_cluster_access_config():
    return eks.AccessConfig(
        AuthenticationMode="API_AND_CONFIG_MAP",
    )


def _get_k8s_network_config():
    return eks.KubernetesNetworkConfig(
        IpFamily="ipv4",
        ServiceIpv4Cidr=IPV4_SERVICE_PREFIX,
    )


def _get_logging():
    return eks.Logging(
        ClusterLogging=eks.ClusterLogging(
            EnabledTypes=[
                eks.LoggingTypeConfig(Type=log_type)
                for log_type in ENABLED_LOGGING_TYPES
            ]
        )
    )


def _get_resources_vpc_config(
    subnet_ids: Parameter,
    security_group_ids: Parameter,
):
    return eks.ResourcesVpcConfig(
        SecurityGroupIds=Ref(security_group_ids),
        SubnetIds=Ref(subnet_ids),
        EndpointPublicAccess=True,
        EndpointPrivateAccess=True,
        PublicAccessCidrs=PUBLIC_ACCESS_PREFIXES,
    )


def get_cluster(
    name: Parameter,
    version: Parameter,
    subnet_ids: Parameter,
    security_group_ids: Parameter,
    cluster_role: iam.Role,
) -> eks.Cluster:
    return eks.Cluster(
        title=CLUSTER_TITLE,
        Name=Join("", [Ref(name), CLUSTER_TITLE]),
        Version=Ref(version),
        RoleArn=GetAtt(cluster_role, "Arn"),
        AccessConfig=_get_cluster_access_config(),
        KubernetesNetworkConfig=_get_k8s_network_config(),
        Logging=_get_logging(),
        ResourcesVpcConfig=_get_resources_vpc_config(
            subnet_ids,
            security_group_ids,
        ),
    )
