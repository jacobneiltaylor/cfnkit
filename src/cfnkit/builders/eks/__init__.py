from cfnkit import helpers, constants
from cfnkit.types import Parameters, Resources, Outputs, ParameterMap, ResourceMap
from cfnkit.builders.builder import Builder
from cfnkit.builders.eks import cluster, iam, nodes, addons, karpenter


def _get_boundary_param(**kwargs):
    return {
        f"{k}RolePermissionsBoundary": {
            "Type": "String",
            "Description": f"ARN to a managed IAM policy that will constrain the {v} role",
        }
        for k, v in kwargs.items()
    }


class EksClusterTemplateBuilder(Builder):
    OUTPUT_ROLES = (
        "EksClusterRole",
        "EksVpcCniServiceAccountRole",
        "EksAwsLbControllerServiceAccountRole",
        "EksNodeEc2InstanceRole",
    )

    def __init__(
        self,
        enable_karpenter: bool = False,
        provide_boundaries: bool = False,
        enable_external_secrets: bool = False,
    ) -> None:
        self.enable_karpenter = enable_karpenter
        self.provide_boundaries = provide_boundaries
        self.enable_external_secrets = enable_external_secrets

    @property
    def role_names(self):
        keys = list(constants.EKS_BOUNDARY_POLICIES.keys())

        if not self.enable_karpenter:
            keys.remove("Karpenter")

        if not self.enable_external_secrets:
            keys.remove("ExternalSecrets")

        return keys

    @property
    def role_descriptions(self):
        return {name: constants.EKS_BOUNDARY_DESCS[name] for name in self.role_names}

    def get_parameters(self) -> Parameters:
        params = dict()

        params.update(helpers.load_static_json("default_parameters_eks"))

        if self.provide_boundaries:
            params.update(_get_boundary_param(**self.role_descriptions))

        yield from helpers.generate_parameters(params)

    def _get_boundary(self, name: str, params: ParameterMap):
        if self.provide_boundaries:
            return params[f"{name}RolePermissionsBoundary"]

        return iam.get_managed_policy(
            f"{name}RoleBoundaryPolicy",
            f"Permissions boundary policy to constrain the {self.role_descriptions[name]} role",
            helpers.load_static_json(
                f"boundary_{constants.EKS_BOUNDARY_POLICIES[name]}"
            ),
        )

    def get_boundaries(self, params: ParameterMap):
        return {name: self._get_boundary(name, params) for name in self.role_names}

    def get_resources(self, parameters: ParameterMap) -> Resources:
        perm_boundaries = self.get_boundaries(parameters)

        if not self.provide_boundaries:
            yield from perm_boundaries.values()

        # EKS cluster Role
        yield (cluster_role := iam.get_eks_cluster_role(perm_boundaries["EksCluster"]))

        # EKS cluster
        yield (
            eks_cluster := cluster.get_cluster(
                parameters["ClusterName"],
                parameters["ClusterVersion"],
                parameters["SubnetIds"],
                parameters["ClusterSecurityGroupIds"],
                cluster_role,
            )
        )

        # Cluster OIDC Provider
        yield iam.get_cluster_oidc_provider(
            eks_cluster,
            parameters["OidcThumbprint"],
        )

        # Karpenter support infra
        if self.enable_karpenter:
            yield (interrupt_queue := karpenter.get_interrupt_queue())
            yield karpenter.get_interrupt_queue_policy(interrupt_queue)
            yield karpenter.get_scheduled_change_rule(interrupt_queue)
            yield karpenter.get_spot_interruption_rule(interrupt_queue)
            yield karpenter.get_rebalance_rule(interrupt_queue)
            yield karpenter.get_instance_state_rule(interrupt_queue)

        # IRSAs and Node Role
        yield iam.get_lb_controller_irsa(
            eks_cluster, perm_boundaries["AwsLbController"]
        )
        yield (
            node_role := iam.get_node_instance_role(perm_boundaries["EksNodeInstance"])
        )
        yield (
            ebs_csi_role := iam.get_ebs_csi_irsa(
                eks_cluster, perm_boundaries["AwsEbsCsi"]
            )
        )
        yield (
            vpc_cni_role := iam.get_vpc_cni_irsa(
                eks_cluster, perm_boundaries["AwsVpcCni"]
            )
        )

        if self.enable_karpenter:
            yield iam.get_karpenter_irsa(
                eks_cluster,
                interrupt_queue,
                node_role,
                perm_boundaries["Karpenter"],
            )
            yield iam.get_instance_profile("EksKarpenter", node_role)

        if self.enable_external_secrets:
            yield iam.get_external_secrets_irsa(
                eks_cluster,
                perm_boundaries["ExternalSecrets"],
            )

        # Addons
        yield addons.get_ebs_csi_addon(
            eks_cluster,
            ebs_csi_role,
            parameters["ClusterEbsCsiAddonVersion"],
        )

        yield addons.get_vpc_cni_addon(
            eks_cluster,
            vpc_cni_role,
            parameters["ClusterVpcCniAddonVersion"],
        )

        yield addons.get_coredns_addon(
            eks_cluster,
            parameters["ClusterCoreDnsAddonVersion"],
        )

        yield addons.get_kubeproxy_addon(
            eks_cluster,
            parameters["ClusterKubeProxyAddonVersion"],
        )

        yield addons.get_pod_identity_addon(
            eks_cluster, parameters["ClusterPodIdentityAddonVersion"]
        )

        # Managed Node Group
        yield nodes.get_managed_node_group(
            eks_cluster,
            parameters["NodeGroupName"],
            node_role,
            parameters["SubnetIds"],
            parameters["DesiredCapacity"],
            parameters["NodeInstanceTypes"],
            parameters["NodeAmiType"],
        )

    def get_outputs(self, resources: ResourceMap) -> Outputs:
        for role in self.OUTPUT_ROLES:
            yield helpers.get_role_output(resources[role])

        yield helpers.get_oidc_provider_output(resources["EksClusterOidcProvider"])
        yield from helpers.get_cluster_outputs(resources["EksCluster"])
        yield helpers.get_mng_output(resources["EksClusterManagedNodeGroup"])

        if self.enable_karpenter:
            yield helpers.get_role_output(resources["EksKarpenterServiceAccountRole"])
            yield helpers.get_instance_profile_output(
                resources["EksKarpenterInstanceProfile"]
            )
            yield from helpers.get_sqs_queue_outputs(
                resources["EksKarpenterInterruptQueue"]
            )

        if self.enable_external_secrets:
            yield helpers.get_role_output(
                resources["EksExternalSecretsServiceAccountRole"]
            )
