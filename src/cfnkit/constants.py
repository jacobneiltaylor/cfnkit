from enum import Enum, Flag, auto


class AddressFamily(Flag):
    INET4 = auto()
    INET6 = auto()


class IPv4DefaultRoute(Enum):
    NO_DEFAULT = auto()
    IGW = auto()
    NAT_GATEWAY = auto()


class IPv6DefaultRoute(Enum):
    NO_DEFAULT = auto()
    IGW = auto()
    EGRESS_ONLY_IGW = auto()


EKS_BOUNDARY_POLICIES = {
    "AwsLbController": "aws_lb_controller",
    "EksCluster": "eks_cluster",
    "EksNodeInstance": "eks_node",
    "AwsVpcCni": "vpc_cni",
    "AwsEbsCsi": "ebs_csi",
    "Karpenter": "karpenter",
    "ExternalSecrets": "external_secrets",
}

EKS_BOUNDARY_DESCS = {
    "AwsLbController": "AWS load balancer controller",
    "EksCluster": "EKS cluster",
    "EksNodeInstance": "EKS node instance",
    "AwsVpcCni": "AWS VPC CNI",
    "AwsEbsCsi": "AWS EBS CSI",
    "Karpenter": "Karpenter controller",
    "ExternalSecrets": "External Secrets Operator",
}
