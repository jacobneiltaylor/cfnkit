from dataclasses import dataclass

from cfnkit.constants import IPv4DefaultRoute, IPv6DefaultRoute
from cfnkit.helpers import default


@dataclass
class SubnetGroup:
    name: str = "public"
    is_public: bool = True
    ipv4_default_route: IPv4DefaultRoute = IPv4DefaultRoute.IGW
    ipv6_default_route: IPv6DefaultRoute = IPv6DefaultRoute.NO_DEFAULT
    spawn_nat_gateways: bool = False
    tags: dict[str, str] = default(dict)
