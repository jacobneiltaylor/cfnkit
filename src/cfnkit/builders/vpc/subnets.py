from cfnkit import helpers
from cfnkit.datastructures import SubnetParameters, SubnetGroup
from cfnkit.constants import AddressFamily

from troposphere import ec2, Ref, Sub


def get_az_name_tag(typ: str, vpc: str, az: str, name: str):
    return helpers.get_name_tag(Sub(f"{typ}.${{AWS::Region}}.{vpc}.{az}.{name}"))


def get_subnet(
    vpc_name: str, params: SubnetParameters, group: SubnetGroup, vpc: ec2.VPC
):
    assert params.group_name == group.name

    kwargs = {
        "VpcId": Ref(vpc),
        "AvailabilityZone": params.availability_zone,
        "Tags": [
            get_az_name_tag("subnet", vpc_name, params.availability_zone, group.name),
            *helpers.get_tags(group.tags),
        ],
    }

    def get_prefix(addr_family):
        return params.prefixes[addr_family].compressed

    if params.is_ipv6_native:
        kwargs["Ipv6Native"] = True
    else:
        kwargs["CidrBlock"] = get_prefix(AddressFamily.INET4)

    if AddressFamily.INET6 in params.prefixes:
        kwargs["Ipv6CidrBlock"] = get_prefix(AddressFamily.INET6)

    if group.is_public:
        kwargs["MapPublicIpOnLaunch"] = True

    return ec2.Subnet(
        f"{vpc.title}{group.name.capitalize()}Subnet{params.index+1}", **kwargs
    )
