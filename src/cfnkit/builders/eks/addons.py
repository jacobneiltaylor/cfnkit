import json
from typing import Optional
from cfnkit.types import StringPair

from troposphere import eks, iam, Parameter, Ref, GetAtt


def _get_addon(title: str, name: str, cluster: eks.Cluster, **kwargs):
    return eks.Addon(title=title, AddonName=name, ClusterName=Ref(cluster), **kwargs)


def _get_config_values(
    toleration: Optional[StringPair] = None, 
    affinity: Optional[StringPair] = None
):
    config = {}
    
    if affinity is not None:
        label_key, label_value = affinity
        config["affinity"] = {
            "nodeAffinity": {
                "preferredDuringSchedulingIgnoredDuringExecution": [
                    {
                        "weight": 1,
                        "preference": {
                            "matchExpressions": [
                                {
                                    "key": label_key,
                                    "operator": "In",
                                    "values": [
                                        label_value,
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }    

    if toleration is not None:
        taint_key, taint_value = toleration
        config["tolerations"] = [
            {
                "key": taint_key,
                "value": taint_value,
                "operator": "Equal",
                "effect": "NoSchedule"
            }
        ]
        
    return config


def get_ebs_csi_addon(
    cluster: eks.Cluster,
    service_account_role: iam.Role,
    version: Parameter,
    toleration: Optional[StringPair] = None, 
    affinity: Optional[StringPair] = None,
):
    config = _get_config_values(toleration, affinity)
    kwargs = {
        "AddonVersion": Ref(version),
        "ServiceAccountRoleArn": GetAtt(service_account_role, "Arn"),
    }
    
    if len(config) > 0:
        kwargs["ConfigurationValues"] = json.dumps({
            "controller": config,
        })
    
    return _get_addon("EksEbsCsiAddon", "aws-ebs-csi-driver", cluster, **kwargs)


def get_vpc_cni_addon(
    cluster: eks.Cluster,
    service_account_role: iam.Role,
    version: Parameter,
    toleration: Optional[StringPair] = None, 
):
    config = _get_config_values(toleration)
    kwargs = {
        "AddonVersion": Ref(version),
        "ServiceAccountRoleArn": GetAtt(service_account_role, "Arn"),
    }
    
    if len(config) > 0:
        kwargs["ConfigurationValues"] = json.dumps(config)
        
    
    return _get_addon("EksVpcCniAddon", "vpc-cni", cluster, **kwargs)


def get_coredns_addon(
    cluster: eks.Cluster,
    version: Parameter,
    toleration: Optional[StringPair] = None,
    affinity: Optional[StringPair] = None,
):
    config = _get_config_values(toleration, affinity)
    kwargs = {"AddonVersion": Ref(version)}

    if len(config) > 0:
        kwargs["ConfigurationValues"] = json.dumps(config)

    return _get_addon("EksCoreDnsAddon", "coredns", cluster, **kwargs)


def get_kubeproxy_addon(
    cluster: eks.Cluster,
    version: Parameter,
):
    return _get_addon(
        "EksKubeProxyAddon",
        "kube-proxy",
        cluster,
        AddonVersion=Ref(version),
    )


def get_pod_identity_addon(
    cluster: eks.Cluster,
    version: Parameter,
    toleration: Optional[StringPair] = None,
):
    config = _get_config_values(toleration)
    kwargs = {"AddonVersion": Ref(version)}
    
    if len(config) > 0:
        kwargs["ConfigurationValues"] = json.dumps(config)
    
    return _get_addon("EksPodIdentityAddon", "eks-pod-identity-agent", cluster, **kwargs)
