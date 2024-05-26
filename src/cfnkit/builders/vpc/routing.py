from troposphere import ec2, Sub, Ref

from cfnkit import helpers
from cfnkit.constants import IPv4DefaultRoute, IPv6DefaultRoute
from cfnkit.datastructures import SubnetGroup, SubnetParameters


def get_az_name_tag(typ: str, vpc: str, az: str, name: str):
    return helpers.get_name_tag(Sub(f"{typ}.${{AWS::Region}}.{vpc}.{az}.{name}"))


def get_route_table(
    vpc_name: str,
    params: SubnetParameters,
    group: SubnetGroup,
    vpc: ec2.VPC,
    subnet: ec2.Subnet,
):
    assert params.group_name == group.name

    return ec2.RouteTable(
        f"{subnet.title}RouteTable",
        VpcId=Ref(vpc),
        Tags=[
            get_az_name_tag(
                "rtb",
                vpc_name,
                params.availability_zone,
                group.name,
            )
        ],
    )


def get_route_table_association(rtb: ec2.RouteTable, subnet: ec2.Subnet):
    return ec2.SubnetRouteTableAssociation(
        f"{rtb.title}Association",
        RouteTableId=Ref(rtb),
        SubnetId=Ref(subnet),
    )


def get_ipv4_default_route(
    params: SubnetParameters,
    group: SubnetGroup,
    rtb: ec2.RouteTable,
    natgws: dict[str, ec2.NatGateway],
    igw: ec2.InternetGateway,
):
    assert params.group_name == group.name

    kwargs = {
        "RouteTableId": Ref(rtb),
        "DestinationCidrBlock": "0.0.0.0/0",
    }

    match group.ipv4_default_route:
        case IPv4DefaultRoute.IGW:
            kwargs["GatewayId"] = Ref(igw)
        case IPv4DefaultRoute.NAT_GATEWAY:
            natgw = natgws.get(params.availability_zone, list(natgws.values())[0])
            kwargs["NatGatewayId"] = Ref(natgw)

    return ec2.Route(f"{rtb.title}Ipv4DefaultRoute", **kwargs)


def get_ipv6_default_route(
    params: SubnetParameters,
    group: SubnetGroup,
    rtb: ec2.RouteTable,
    eigw: ec2.EgressOnlyInternetGateway,
    igw: ec2.InternetGateway,
):
    assert params.group_name == group.name

    kwargs = {
        "RouteTableId": Ref(rtb),
        "DestinationIpv6CidrBlock": "::/0",
    }

    match group.ipv6_default_route:
        case IPv6DefaultRoute.IGW:
            kwargs["GatewayId"] = Ref(igw)
        case IPv6DefaultRoute.EGRESS_ONLY_IGW:
            kwargs["EgressOnlyInternetGatewayId"] = Ref(eigw)

    return ec2.Route(f"{rtb.title}Ipv6DefaultRoute", **kwargs)
