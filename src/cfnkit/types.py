from typing import Generator, Any, Union
from ipaddress import IPv4Network, IPv6Network

from troposphere import AWSObject, Parameter, Output
from cfnkit.constants import AddressFamily

Prefix = Union[IPv4Network, IPv6Network]
PrefixList = dict[AddressFamily, list[Prefix]]

Parameters = Generator[Parameter, None, Any]
Resources = Generator[AWSObject, None, Any]
Outputs = Generator[Output, None, Any]

ParameterMap = dict[str, Parameter]
ResourceMap = dict[str, AWSObject]
