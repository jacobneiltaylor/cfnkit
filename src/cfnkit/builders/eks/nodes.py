from troposphere import eks, iam, Ref, GetAtt, Parameter


MIN_SIZE = 1
MAX_SIZE = 3


def get_managed_node_group(
    cluster: eks.Cluster,
    nodegroup_name: Parameter,
    node_role: iam.Role,
    subnet_ids: Parameter,
    desired_capacity: Parameter,
    instance_types: Parameter,
    ami_type: Parameter,
):
    return eks.Nodegroup(
        title="EksClusterManagedNodeGroup",
        AmiType=Ref(ami_type),
        ClusterName=Ref(cluster),
        NodegroupName=Ref(nodegroup_name),
        NodeRole=GetAtt(node_role, "Arn"),
        Subnets=Ref(subnet_ids),
        InstanceTypes=Ref(instance_types),
        ScalingConfig=eks.ScalingConfig(
            DesiredSize=Ref(desired_capacity),
            MinSize=MIN_SIZE,
            MaxSize=MAX_SIZE,
        ),
    )
