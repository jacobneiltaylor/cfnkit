from troposphere import ec2, Ref, GetAtt


def get_eip_allocation(name: str, idx: int, attachment: ec2.VPCGatewayAttachment):
    return ec2.EIP(
        f"{name}NatEIP{idx}",
        DependsOn=attachment.title,
        Domain="vpc",
    )


def get_nat_gateway(
    name: str, idx: int, subnet: ec2.Subnet, allocation_id: str | GetAtt
):
    return ec2.NatGateway(
        f"{name}NatGateway{idx}",
        AllocationId=allocation_id,
        SubnetId=Ref(subnet),
    )
