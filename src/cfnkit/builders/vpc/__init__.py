from cfnkit.builders.builder import Builder
from cfnkit.datastructures import VpcParameters, SubnetParameters, SubnetGroup
from cfnkit.types import ParameterMap, Resources, ResourceMap, Outputs
from cfnkit.constants import AddressFamily, IPv6DefaultRoute, IPv4DefaultRoute
from cfnkit import helpers

from cfnkit.builders.vpc import vpc, subnets, routing, nat
from troposphere import ec2, GetAtt


class VpcTemplateBuilder(Builder):
    def __init__(self, params: VpcParameters) -> None:
        self.params = params

    @staticmethod
    def should_install_default_route(
        address_family: AddressFamily, params: SubnetParameters, group: SubnetGroup
    ):
        if address_family in params.address_families:
            match address_family:
                case AddressFamily.INET4:
                    return group.ipv4_default_route != IPv4DefaultRoute.NO_DEFAULT
                case AddressFamily.INET6:
                    return group.ipv6_default_route != IPv6DefaultRoute.NO_DEFAULT
        return False

    def get_resources(self, _: ParameterMap) -> Resources:
        yield (
            vpc_ := vpc.get_vpc(
                self.params.name,
                self.params.prefixes[AddressFamily.INET4][0],  # type: ignore
            )
        )

        yield (igw := vpc.get_igw(self.params.name))
        yield (gwattach := vpc.get_igw_attachment(self.params.name, vpc_, igw))
        eigw = None

        if self.params.is_ipv6_enabled:
            yield vpc.get_vpc_ipv6_prefix_block(
                vpc_,
                self.params.prefixes[AddressFamily.INET6][0],  # type: ignore
            )
            yield (eigw := vpc.get_eigw(self.params.name, vpc_))

        groups = {group.name: group for group in self.params.subnet_groups}

        subnets_: list[ec2.Subnet] = []
        natgws: dict[str, ec2.NatGateway] = {}

        for idx, params in enumerate(self.params.subnets):
            group = groups[params.group_name]
            yield (subnet := subnets.get_subnet(self.params.name, params, group, vpc_))
            subnets_.append(subnet)

            if group.spawn_nat_gateways:
                yield (eip := nat.get_eip_allocation(self.params.name, idx, gwattach))
                yield (
                    natgw := nat.get_nat_gateway(
                        self.params.name, idx, subnet, GetAtt(eip, "AllocationId")
                    )
                )
                natgws[params.availability_zone] = natgw

        for params, subnet in zip(self.params.subnets, subnets_):
            group = groups[params.group_name]

            yield (
                rtb := routing.get_route_table(
                    self.params.name, params, group, vpc_, subnet
                )
            )

            if self.should_install_default_route(AddressFamily.INET4, params, group):
                yield routing.get_ipv4_default_route(params, group, rtb, natgws, igw)

            if self.should_install_default_route(AddressFamily.INET6, params, group):
                yield routing.get_ipv6_default_route(params, group, rtb, eigw, igw)

            yield routing.get_route_table_association(rtb, subnet)

    def get_outputs(self, resources: ResourceMap) -> Outputs:
        for resource in resources.values():
            match resource.resource_type:
                case "AWS::EC2::Subnet":
                    yield helpers.get_subnet_output(resource)
                case "AWS::EC2::VPC":
                    yield helpers.get_vpc_output(resource)
