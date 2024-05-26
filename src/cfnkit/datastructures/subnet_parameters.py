from dataclasses import dataclass

from cfnkit.constants import AddressFamily
from cfnkit.types import Prefix
from cfnkit.helpers import default, reduce_flags


@dataclass
class SubnetParameters:
    group_name: str = "public"
    availability_zone: str = "us-east-1a"
    prefixes: dict[AddressFamily, Prefix] = default(list)
    index: int = 0

    @property
    def address_families(self) -> AddressFamily:
        return reduce_flags(self.prefixes.keys())

    @property
    def is_ipv6_native(self):
        return AddressFamily.INET4 not in self.address_families
