import json
from typing import Any
from dataclasses import field
from functools import reduce

from troposphere import (
    iam,
    ec2,
    eks,
    sqs,
    events,
    Parameter,
    GetAtt,
    Output,
    Export,
    Sub,
    AWSObject,
    Select,
    Split,
    Ref,
    Tag,
)

from cfnkit.resources import get_package_file


def default(factory):
    return field(default_factory=factory)


def generate_parameters(parameter_def: dict[str, dict[str, Any]]):
    for title, kwargs in parameter_def.items():
        yield Parameter(title=title, **kwargs)


def get_export(title):
    return Export(Sub(f"${{AWS::StackName}}-{title}"))


def _get_output(title: str, desc: str, value: Any, export: bool):
    kwargs = {
        "title": title,
        "Description": desc,
        "Value": value,
    }

    if export:
        kwargs["Export"] = get_export(title)

    return Output(**kwargs)


def _get_arn_output(
    obj: AWSObject, desc: str, export=True, arn_cb=lambda x: GetAtt(x, "Arn")
):
    return _get_output(f"{obj.title}ArnOutput", desc, arn_cb(obj), export)


def _get_attr_output_factory(obj: AWSObject, desc_tpl: str):
    def factory(attr: str, name: str | None = None):
        if name is None:
            name = f"{obj.title}{attr}Output"
        return _get_output(
            name, desc_tpl.format(obj=obj, attr=attr), GetAtt(obj, attr), False
        )

    return factory


def get_ref_output(obj: AWSObject, description: str, export=True):
    return _get_output(f"{obj.title}RefOutput", description, Ref(obj), export)


def get_role_output(role: iam.Role):
    return _get_arn_output(role, f"ARN for IAM role {role.title}")


def get_oidc_provider_output(prov: iam.OIDCProvider):
    return _get_arn_output(prov, f"ARN for IAM OIDC provider {prov.title}")


def get_mng_output(mng: eks.Nodegroup):
    return _get_arn_output(mng, f"ARN for EKS Managed node group {mng.title}")


def get_instance_profile_output(profile: iam.InstanceProfile):
    return _get_arn_output(profile, f"ARN for instance profile {profile.title}")


def get_sqs_queue_outputs(queue: sqs.Queue):
    attr_output = _get_attr_output_factory(
        queue, "{attr} value for the SQS queue {obj.title}"
    )

    yield attr_output("Arn")
    yield attr_output("QueueName", "EksKarpenterInterruptQueueNameOutput")
    yield attr_output("QueueUrl", "EksKarpenterInterruptQueueUrlOutput")


def get_cluster_outputs(cluster: eks.Cluster):
    attr_output = _get_attr_output_factory(
        cluster, "{attr} value for the EKS cluster {obj.title}"
    )

    yield get_ref_output(cluster, f"API name of the EKS cluster {cluster.title}")
    yield _get_arn_output(cluster, f"ARN for the EKS cluster {cluster.title}")
    yield attr_output("Endpoint")
    yield attr_output("OpenIdConnectIssuerUrl")


def get_vpc_output(vpc: ec2.VPC):
    return get_ref_output(vpc, f"Unique identifier of the VPC {vpc.title}")


def get_subnet_output(subnet: ec2.Subnet):
    return get_ref_output(subnet, f"Unique identifier of the subnet {subnet.title}")


def get_static_resource(filename: str):
    return get_package_file("cfnkit.static", filename)


def load_static_json(name: str):
    resource = get_static_resource(f"{name}.json")
    with resource.open("r") as fd:
        return json.load(fd)


def strip_scheme(obj, attr="OpenIdConnectIssuerUrl"):
    uri = GetAtt(obj, attr)
    return Select(1, Split("//", uri))


def get_event_rule(
    title: str, detail: str, targets: list[events.Target], source="aws.ec2"
):
    return events.Rule(
        title,
        EventPattern={
            "source": [source],
            "detail-type": [detail],
        },
        Targets=targets,
    )


def reduce_flags(flags):
    return reduce(lambda a, b: a | b, flags)


def get_name_tag(value):
    return Tag("Name", value)


def get_tags(tags: dict[str, str]):
    for key, value in tags.items():
        yield Tag(key, value)


def _get_called_apis(actions: str | list[str]):
    def collector(actions):
        if isinstance(actions, str):
            actions = [actions]

        for action in actions:
            if ":" in action:
                yield action.split(":")[0]

    return set(collector(actions))


def generate_iam_boundary(*args):
    apis = set()

    for policy in args:
        if isinstance(policy, iam.Policy):
            policy = policy.PolicyDocument
        for stmt in policy["Statement"]:
            apis = apis.union(_get_called_apis(stmt["Action"]))

    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [f"{api}:*" for api in apis],
                "Resource": "*",
            }
        ],
    }


def merge_policies(*args):
    stmts = []

    for policy in args:
        stmts.extend(policy["Statement"])

    return {"Version": "2012-10-17", "Statement": stmts}
