import json
from troposphere import iam, eks, sqs, GetAtt, Sub, Ref, Parameter

from cfnkit import helpers


AUDIENCE = "sts.amazonaws.com"


def _get_ec2_trust_policy():
    return helpers.load_static_json("ec2_trust_policy")


def _get_eks_cluster_trust_policy():
    return helpers.load_static_json("eks_trust_policy")


def _get_eks_oidc_trust_policy(
    provider_name, namespace: str = "kube-system", service_account: str = "aws-node"
):
    policy = helpers.load_static_json("oidc_trust_policy")
    return Sub(
        json.dumps(policy),
        {
            "Provider": provider_name,
            "Namespace": namespace,
            "ServiceAccount": service_account,
        },
    )


def _get_ebs_csi_access_policy(role_name: str):
    return iam.Policy(
        PolicyName=f"{role_name}AccessPolicy",
        PolicyDocument=helpers.load_static_json("ebs_csi"),
    )


def _get_vpc_cni_access_policy(role_name: str):
    return iam.Policy(
        PolicyName=f"{role_name}AccessPolicy",
        PolicyDocument=helpers.load_static_json("vpc_cni"),
    )


def _get_lb_controller_access_policy(role_name):
    return iam.Policy(
        PolicyName=f"{role_name}AccessPolicy",
        PolicyDocument=helpers.load_static_json("aws_lb_controller"),
    )


def _get_external_secrets_access_policy(role_name):
    return iam.Policy(
        PolicyName=f"{role_name}AccessPolicy",
        PolicyDocument=Sub(
            json.dumps(helpers.load_static_json("external_secrets"))
        ),
    )


def _get_karpenter_access_policy(
    role_name, cluster: eks.Cluster, interrupt_queue: sqs.Queue, node_role: iam.Role
):
    policy = helpers.load_static_json("karpenter_controller")
    return iam.Policy(
        PolicyName=f"{role_name}AccessPolicy",
        PolicyDocument=Sub(
            json.dumps(policy),
            {
                "ClusterName": Ref(cluster),
                "QueueArn": GetAtt(interrupt_queue, "Arn"),
                "NodeRoleArn": GetAtt(node_role, "Arn"),
            },
        ),
    )


def get_managed_policy(name, description, policy):
    return iam.ManagedPolicy(
        name,
        Description=description,
        PolicyDocument=policy,
    )


def _get_role(role_name, trust_policy, *args, **kwargs):
    role_args = {
        "title": role_name,
        "AssumeRolePolicyDocument": trust_policy,
        **kwargs,
    }

    if args:
        role_args["Policies"] = list(args)

    return iam.Role(**role_args)


def get_eks_cluster_role(boundary) -> iam.Role:
    role_name = "EksClusterRole"

    return _get_role(
        role_name,
        _get_eks_cluster_trust_policy(),
        ManagedPolicyArns=["arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"],
        PermissionsBoundary=Ref(boundary),
    )


def get_cluster_oidc_provider(
    cluster: eks.Cluster, oidc_thumbprint: Parameter
) -> iam.OIDCProvider:
    return iam.OIDCProvider(
        title="EksClusterOidcProvider",
        ClientIdList=[AUDIENCE],
        ThumbprintList=[Ref(oidc_thumbprint)],
        Url=GetAtt(cluster, "OpenIdConnectIssuerUrl"),
    )


def get_ebs_csi_irsa(cluster: eks.Cluster, boundary) -> iam.Role:
    role_name = "EksEbsCsiServiceAccountRole"
    provider = helpers.strip_scheme(cluster)

    trust_policy = _get_eks_oidc_trust_policy(
        provider, service_account="ebs-csi-controller-sa"
    )

    return _get_role(
        role_name,
        trust_policy,
        _get_ebs_csi_access_policy(role_name),
        PermissionsBoundary=Ref(boundary),
    )


def get_vpc_cni_irsa(cluster: eks.Cluster, boundary) -> iam.Role:
    role_name = "EksVpcCniServiceAccountRole"
    provider = helpers.strip_scheme(cluster)

    return _get_role(
        role_name,
        _get_eks_oidc_trust_policy(provider),
        _get_vpc_cni_access_policy(role_name),
        PermissionsBoundary=Ref(boundary),
    )


def get_lb_controller_irsa(cluster: eks.Cluster, boundary) -> iam.Role:
    role_name = "EksAwsLbControllerServiceAccountRole"
    provider = helpers.strip_scheme(cluster)

    trust_policy = _get_eks_oidc_trust_policy(
        provider, service_account="aws-load-balancer-controller-service-account"
    )

    return _get_role(
        role_name,
        trust_policy,
        _get_lb_controller_access_policy(role_name),
        PermissionsBoundary=Ref(boundary),
    )


def get_karpenter_irsa(
    cluster: eks.Cluster,
    interrupt_queue: sqs.Queue,
    node_role: iam.Role,
    boundary,
    namespace: str = "kube-system",
) -> iam.Role:
    role_name = "EksKarpenterServiceAccountRole"
    provider = helpers.strip_scheme(cluster)

    trust_policy = _get_eks_oidc_trust_policy(
        provider, namespace, "karpenter-service-account"
    )

    access_policy = _get_karpenter_access_policy(
        role_name,
        cluster,
        interrupt_queue,
        node_role,
    )

    return _get_role(
        role_name,
        trust_policy,
        access_policy,
        PermissionsBoundary=Ref(boundary),
    )


def get_external_secrets_irsa(cluster: eks.Cluster, boundary) -> iam.Role:
    role_name = "EksExternalSecretsServiceAccountRole"
    provider = helpers.strip_scheme(cluster)

    trust_policy = _get_eks_oidc_trust_policy(
        provider, namespace="external-secrets", service_account="external-secrets-service-account"
    )

    return _get_role(
        role_name,
        trust_policy,
        _get_external_secrets_access_policy(role_name),
        PermissionsBoundary=Ref(boundary),
    )


def get_node_instance_role(boundary) -> iam.Role:
    role_name = "EksNodeEc2InstanceRole"

    return _get_role(
        role_name,
        _get_ec2_trust_policy(),
        _get_vpc_cni_access_policy(role_name),
        ManagedPolicyArns=[
            "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
            "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
            "arn:aws:iam::aws:policy/AmazonSSMManagedEC2InstanceDefaultPolicy",
        ],
        PermissionsBoundary=Ref(boundary),
    )


def get_spot_slr():
    return iam.ServiceLinkedRole(
        "EksKarpenterSpotSLR",
        AWSServiceName="spot.amazonaws.com",
        Description="EC2 Spot SLR for Karpenter",
    )


def get_instance_profile(name: str, role: iam.Role):
    profile_name = f"{name}InstanceProfile"
    return iam.InstanceProfile(profile_name, Roles=[Ref(role)])
