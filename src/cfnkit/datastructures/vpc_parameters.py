from ipaddress import IPv4Network, IPv6Network
from dataclasses import dataclass
from itertools import islice

from cfnkit.constants import AddressFamily, IPv4DefaultRoute, IPv6DefaultRoute
from cfnkit.types import Prefix, PrefixList
from cfnkit.helpers import default, reduce_flags
from cfnkit.datastructures.subnet_parameters import SubnetParameters
from cfnkit.datastructures.subnet_group import SubnetGroup

DEFAULT_IPV4_PREFIX = IPv4Network("10.0.0.0/16")
IPV6_SUBNET_PREFIX_LENGTH = 64


def _prefixes():
    return {
        AddressFamily.INET4: [DEFAULT_IPV4_PREFIX],
    }


@dataclass
class VpcParameters:
    name: str
    prefixes: dict[AddressFamily, list[Prefix]] = default(_prefixes)
    subnets: list[SubnetParameters] = default(list)
    subnet_groups: list[SubnetGroup] = default(list)

    @staticmethod
    def get_subnet_prefixes(
        supernet: Prefix, prefix_length: int, count: int
    ) -> list[Prefix]:
        return list(islice(supernet.subnets(new_prefix=prefix_length), count))

    @staticmethod
    def _build_subnets(
        group: SubnetGroup,
        azs: list[str],
        ipv4_prefixes: list,
        ipv6_prefixes: list,
        is_ipv6_native: bool,
    ):
        def get_param_prefixes(idx: int):
            prefixes = {}

            if not is_ipv6_native:
                prefixes[AddressFamily.INET4] = ipv4_prefixes[idx]

            if len(ipv6_prefixes) > 0:
                prefixes[AddressFamily.INET6] = ipv6_prefixes[idx]

            return prefixes

        return [
            SubnetParameters(group.name, zone, get_param_prefixes(idx), idx)
            for idx, zone in enumerate(azs)
        ]

    @property
    def address_families(self) -> AddressFamily:
        return reduce_flags(self.prefixes.keys())

    @property
    def is_ipv6_enabled(self) -> bool:
        return AddressFamily.INET6 in self.address_families

    @classmethod
    def _get_vpc(
        cls,
        groups: list[SubnetGroup],
        availability_zones: list[str],
        ipv4_prefix: IPv4Network,
        ipv6_prefix: IPv6Network | None,
        ipv4_subnet_prefix_length,
    ):
        az_count = len(availability_zones)
        subnet_count = az_count * len(groups)
        is_ipv6_native = False

        if ipv4_prefix is None:
            is_ipv6_native = True
            ipv4_prefix = DEFAULT_IPV4_PREFIX  # VPC needs an IPv4 prefix regardless

        prefixes: PrefixList = {AddressFamily.INET4: [ipv4_prefix]}

        ipv4_subnet_prefixes = cls.get_subnet_prefixes(
            ipv4_prefix,
            ipv4_subnet_prefix_length,
            subnet_count,
        )

        ipv6_subnet_prefixes = []

        if ipv6_prefix is not None:
            prefixes[AddressFamily.INET6] = [ipv6_prefix]
            ipv6_subnet_prefixes = cls.get_subnet_prefixes(
                ipv6_prefix,
                IPV6_SUBNET_PREFIX_LENGTH,
                subnet_count,
            )

        subnets = []

        for idx, group in enumerate(groups):

            def get_group_prefixes(prefixes: list):
                start = idx * az_count
                end = (idx + 1) * az_count
                return prefixes[start:end]

            ipv4_group_prefixes = get_group_prefixes(ipv4_subnet_prefixes)
            ipv6_group_prefixes = []

            if ipv6_prefix is not None:
                ipv6_group_prefixes = get_group_prefixes(ipv6_subnet_prefixes)

            subnets += cls._build_subnets(
                group,
                availability_zones,
                ipv4_group_prefixes,
                ipv6_group_prefixes,
                is_ipv6_native,
            )

        return prefixes, subnets

    @classmethod
    def get_public_vpc(
        cls,
        name: str,
        availability_zones: list[str],
        ipv4_prefix: IPv4Network = DEFAULT_IPV4_PREFIX,
        ipv6_prefix: IPv6Network | None = None,
        ipv4_subnet_prefix_length: int = 24,
    ):
        public_subnets = SubnetGroup()

        if ipv6_prefix is not None:
            public_subnets.ipv6_default_route = IPv6DefaultRoute.IGW

        groups = [public_subnets]

        prefixes, subnets = cls._get_vpc(
            groups,
            availability_zones,
            ipv4_prefix,
            ipv6_prefix,
            ipv4_subnet_prefix_length,
        )

        return cls(name, prefixes, subnets, groups)

    @classmethod
    def get_public_private_vpc(
        cls,
        name: str,
        availability_zones: list[str],
        ipv4_prefix: IPv4Network = DEFAULT_IPV4_PREFIX,
        ipv6_prefix: IPv6Network | None = None,
        ipv4_subnet_prefix_length: int = 24,
    ):
        public_subnets = SubnetGroup(name="public", spawn_nat_gateways=True)
        private_subnets = SubnetGroup(
            name="private",
            is_public=False,
            ipv4_default_route=IPv4DefaultRoute.NAT_GATEWAY,
        )

        if ipv6_prefix is not None:
            public_subnets.ipv6_default_route = IPv6DefaultRoute.IGW
            private_subnets.ipv6_default_route = IPv6DefaultRoute.EGRESS_ONLY_IGW

        groups = [public_subnets, private_subnets]

        prefixes, subnets = cls._get_vpc(
            groups,
            availability_zones,
            ipv4_prefix,
            ipv6_prefix,
            ipv4_subnet_prefix_length,
        )

        return cls(name, prefixes, subnets, groups)
