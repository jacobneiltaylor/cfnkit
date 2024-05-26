from ipaddress import IPv4Network, IPv6Network
from troposphere import ec2, Sub, Ref

from cfnkit import helpers


def get_regional_name_tag(typ: str, name: str):
    return helpers.get_name_tag(Sub(f"{typ}.${{AWS::Region}}.{name}"))


def get_vpc(name: str, ipv4_prefix: IPv4Network):
    return ec2.VPC(
        f"{name}Vpc",
        CidrBlock=ipv4_prefix.compressed,
        EnableDnsSupport=True,
        EnableDnsHostnames=True,
        Tags=[get_regional_name_tag("vpc", name)],
    )


def get_vpc_ipv6_prefix_block(vpc: ec2.VPC, ipv6_prefix: IPv6Network):
    return ec2.VPCCidrBlock(
        f"{vpc.title}Ipv6Prefix", VpcId=Ref(vpc), Ipv6CidrBlock=ipv6_prefix.compressed
    )


def get_igw(name: str):
    return ec2.InternetGateway(
        f"{name}InternetGateway", Tags=[get_regional_name_tag("igw", name)]
    )


def get_eigw(name: str, vpc: ec2.VPC):
    return ec2.EgressOnlyInternetGateway(
        f"{name}EgressOnlyInternetGateway",
        VpcId=Ref(vpc),
    )


def get_igw_attachment(name: str, vpc: ec2.VPC, igw: ec2.InternetGateway):
    return ec2.VPCGatewayAttachment(
        f"{name}InternetGatewayAttachment", InternetGatewayId=Ref(igw), VpcId=Ref(vpc)
    )
