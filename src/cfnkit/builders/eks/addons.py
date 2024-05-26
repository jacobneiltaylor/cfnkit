from troposphere import eks, iam, Parameter, Ref, GetAtt


def _get_addon(title: str, name: str, cluster: eks.Cluster, **kwargs):
    return eks.Addon(title=title, AddonName=name, ClusterName=Ref(cluster), **kwargs)


def get_ebs_csi_addon(
    cluster: eks.Cluster,
    service_account_role: iam.Role,
    version: Parameter,
):
    return _get_addon(
        "EksEbsCsiAddon",
        "aws-ebs-csi-driver",
        cluster,
        AddonVersion=Ref(version),
        ServiceAccountRoleArn=GetAtt(service_account_role, "Arn"),
    )


def get_vpc_cni_addon(
    cluster: eks.Cluster,
    service_account_role: iam.Role,
    version: Parameter,
):
    return _get_addon(
        "EksVpcCniAddon",
        "vpc-cni",
        cluster,
        AddonVersion=Ref(version),
        ServiceAccountRoleArn=GetAtt(service_account_role, "Arn"),
    )


def get_coredns_addon(
    cluster: eks.Cluster,
    version: Parameter,
):
    return _get_addon(
        "EksCoreDnsAddon",
        "coredns",
        cluster,
        AddonVersion=Ref(version),
    )


def get_kubeproxy_addon(
    cluster: eks.Cluster,
    version: Parameter,
):
    return _get_addon(
        "EksKubeProxyAddon",
        "kube-proxy",
        cluster,
        AddonVersion=Ref(version),
    )


def get_pod_identity_addon(
    cluster: eks.Cluster,
    version: Parameter,
):
    return _get_addon(
        "EksPodIdentityAddon",
        "eks-pod-identity-agent",
        cluster,
        AddonVersion=Ref(version),
    )
