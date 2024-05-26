from ipaddress import IPv4Network, IPv6Network

from cfnkit.datastructures import VpcParameters
from cfnkit.builders.discovery import get_builder_entry_point

from support import constants, helpers


def _get_vpc_parameters(ipv6: bool, private: bool):
    kwargs = {
        "name": "foo",
        "availability_zones": constants.VPC_AVAILABILITY_ZONES,
        "ipv4_prefix": IPv4Network(constants.VPC_IPV4_PREFIX),
    }

    if ipv6:
        kwargs["ipv6_prefix"] = IPv6Network(constants.VPC_IPV6_PREFIX)

    if private:
        return VpcParameters.get_public_private_vpc(**kwargs)
    return VpcParameters.get_public_vpc(**kwargs)


def _mkargs(name: str, ipv6: bool, private: bool):
    return {
        "kwargs": {
            "params": _get_vpc_parameters(ipv6, private),
        },
        "expect": helpers.load_test_vpc_template(name),
    }


TEST_MATRIX = {
    name: _mkargs(name, bool(idx & 1), bool(idx & 2))
    for idx, name in enumerate(
        (
            "public_v4",
            "public_dual",
            "private_v4",
            "private_dual",
        )
    )
}


@helpers.matrix_parametrize(TEST_MATRIX)
def test_vpc_template_builder(kwargs: dict, expect: dict):
    builder_entry_point = get_builder_entry_point("vpc")
    builder = builder_entry_point.construct(**kwargs)
    template = builder.build_template()
    helpers.assert_equivalent(template.to_dict(), expect)
