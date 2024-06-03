from troposphere import eks, iam, Ref, GetAtt, Parameter


MIN_SIZE = 1
MAX_SIZE = 3


def _get_taints(taints: dict[str, str]):
    return [
        eks.Taint(
            Effect="NO_SCHEDULE",
            Key=key,
            Value=value,
        ) for key, value in taints.items()
    ]


def get_managed_node_group(
    cluster: eks.Cluster,
    nodegroup_name: Parameter,
    node_role: iam.Role,
    subnet_ids: Parameter,
    desired_capacity: Parameter,
    instance_types: Parameter,
    ami_type: Parameter,
    taints: dict[str, str], 
    labels: dict[str, str],
):
    kwargs = {
        "AmiType": Ref(ami_type),
        "ClusterName": Ref(cluster),
        "NodegroupName": Ref(nodegroup_name),
        "NodeRole": GetAtt(node_role, "Arn"),
        "Subnets": Ref(subnet_ids),
        "InstanceTypes": Ref(instance_types),
        "ScalingConfig": eks.ScalingConfig(
            DesiredSize=Ref(desired_capacity),
            MinSize=MIN_SIZE,
            MaxSize=MAX_SIZE,
        ),
    }
    
    if len(taints) > 0:
        kwargs["Taints"] = _get_taints(taints)
        
    if len(labels) > 0:
        kwargs["Labels"] = labels
    
    return eks.Nodegroup(title="EksClusterManagedNodeGroup", **kwargs)
