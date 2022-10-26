# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helpers for flags in commands working with Anthos clusters on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def Get(args, flag_name, default=None):
  """Returns the value if it's set, otherwise returns None.

  Args:
    args: An argparser Namespace class instance.
    flag_name: A string type flag name.
    default: The default value to return if not found in the argparser
      namespace.

  Returns:
    The flag value if it is set by the user. If the flag is not added to the
    interface, or it is added by not specified by the user, returns the
    default value.
  """
  default_values = {
      'page_size': 100,
  }
  if hasattr(args, flag_name) and args.IsSpecified(flag_name):
    return getattr(args, flag_name)
  return default_values.get(flag_name, default)


def IsSet(kwargs):
  """Returns True if any of the kwargs is set to not None value.

  Args:
    kwargs: dict, a mapping from proto field to its respective constructor
      function.

  Returns:
    True if there exists a field that contains a user specified argument.
  """
  return any(value is not None for value in kwargs.values())


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.container_vmware.location),
      ])


def GetLocationResourceSpec():
  """Constructs and returns the Resource specification for Location."""

  return concepts.ResourceSpec(
      'gkeonprem.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def AddLocationResourceArg(parser, verb):
  """Adds a resource argument for Google Cloud location.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Google Cloud location {}.'.format(verb),
      required=True).AddToParser(parser)


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='cluster of the {resource}.',
  )


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.vmwareClusters',
      resource_name='cluster',
      vmwareClustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddClusterResourceArg(parser,
                          verb,
                          positional=True,
                          required=True,
                          flag_name_overrides=None):
  """Adds a resource argument for an Anthos cluster on VMware.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
    flag_name_overrides: {str: str}, dict of attribute names to the desired flag
      name.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetClusterResourceSpec(),
      'cluster {}'.format(verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
  ).AddToParser(parser)


def AdminClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='admin_cluster',
      help_text='cluster of the {resource}.',
  )


def GetAdminClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.vmwareAdminClusters',
      resource_name='admin_cluster',
      vmwareAdminClustersId=AdminClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddAdminClusterResourceArg(parser,
                               verb,
                               positional=True,
                               required=True,
                               flag_name_overrides=None):
  """Adds a resource argument for an Anthos on VMware admin cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
    flag_name_overrides: {str: str}, dict of attribute names to the desired flag
      name.
  """
  name = 'admin_cluster' if positional else '--admin-cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAdminClusterResourceSpec(),
      'admin cluster {}'.format(verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
  ).AddToParser(parser)


def NodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='node_pool', help_text='node pool of the {resource}.')


def GetNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'gkeonprem.projects.locations.vmwareClusters.vmwareNodePools',
      resource_name='node_pool',
      vmwareNodePoolsId=NodePoolAttributeConfig(),
      vmwareClustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddNodePoolResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a VMware node pool.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'node_pool' if positional else '--node-pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetNodePoolResourceSpec(),
      'node pool {}'.format(verb),
      required=True).AddToParser(parser)


def AddForceUnenroll(parser):
  """Adds a flag for force unenroll operation when there are existing node pools.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--force',
      action='store_true',
      help='If set, any child node pools will also be unenrolled. This flag is required if the cluster has any associated node pools.',
  )


def AddForceDeleteCluster(parser):
  """Adds a flag for force delete cluster operation when there are existing node pools.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--force',
      action='store_true',
      help='If set, any node pools from the cluster will also be deleted. This flag is required if the cluster has any associated node pools.',
  )


def AddAllowMissingDeleteNodePool(parser):
  """Adds a flag for delete node pool operation to return success and perform no action when there is no matching node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help='If set, and the Vmware Node Pool is not found, the request will succeed but no action will be taken.',
  )


def AddAllowMissingDeleteCluster(parser):
  """Adds a flag for delete cluster operation to return success and perform no action when there is no matching cluster.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      help='If set, and the Anthos cluster on VMware is not found, the request will succeed but no action will be taken.',
  )


def AddAllowMissingUpdateCluster(parser):
  """Adds a flag to enable allow missing in an update cluster request.

  If set to true, and the cluster is not found, the request will
  create a new cluster with the provided configuration. The user
  must have both create and update permission to call Update with
  allow_missing set to true.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--allow-missing',
      action='store_true',
      hidden=True,
      help='If set, and the Anthos cluster on VMware is not found, the update request will try to create a new cluster with the provided configuration.',
  )


def AddValidationOnly(parser, hidden=False):
  """Adds a flag to only validate the request without performing the operation.

  Args:
    parser: The argparse parser to add the flag to.
    hidden: Set to False when validate-only flag is implemented in the API.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      help='If set, only validate the request, but do not actually perform the operation.',
      hidden=hidden,
  )


def _AddImageType(vmware_node_config_group, for_update=False):
  """Adds a flag to specify the node pool image type.

  Args:
    vmware_node_config_group: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_node_config_group.add_argument(
      '--image-type',
      required=required,
      help='OS image type to use on node pool instances.',
  )


def _AddReplicas(vmware_node_config_group):
  """Adds a flag to specify the number of replicas in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--replicas',
      type=int,
      help='Number of replicas to use on node pool instances.',
  )


def _AddEnableLoadBalancer(vmware_node_config_group, for_update=False):
  """Adds a flag to enable load balancer in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  if for_update:
    enable_lb_mutex_group = vmware_node_config_group.add_group(mutex=True)
    surface = enable_lb_mutex_group
  else:
    surface = vmware_node_config_group

  surface.add_argument(
      '--enable-load-balancer',
      action='store_const',
      const=True,
      help='If set, enable the use of load balancer on the node pool instances.',
  )

  if for_update:
    surface.add_argument(
        '--disable-load-balancer',
        action='store_const',
        const=True,
        help='If set, disable the use of load balancer on the node pool instances.',
    )


def _AddCpus(vmware_node_config_group):
  """Adds a flag to specify the number of cpus in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--cpus',
      help='Number of CPUs for each node in the node pool.',
      type=int,
  )


def _AddMemoryMb(vmware_node_config_group):
  """Adds a flag to specify the memory in MB in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--memory-mb',
      help='Size of memory for each node in the node pool in MB.',
      type=arg_parsers.BinarySize(default_unit='MB', type_abbr='MB'),
  )


def _AddImage(vmware_node_config_group):
  """Adds a flag to specify the image in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--image',
      help='OS image name in vCenter.',
      type=str,
  )


def _AddBootDiskSizeGb(vmware_node_config_group):
  """Adds a flag to specify the boot disk size in GB in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--boot-disk-size-gb',
      help='Size of VMware disk to be used during creation in GB.',
      type=arg_parsers.BinarySize(default_unit='GB', type_abbr='GB'),
  )


def _AddNodeTaint(vmware_node_config_group, for_update=False):
  """Adds a flag to specify the node taint in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  node_pool_create_help_text = """\
Applies the given kubernetes taints on all nodes in the new node pool, which can
be used with tolerations for pod scheduling.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""
  node_pool_update_help_text = """\
Replaces all the user specified Kubernetes taints on all nodes in an existing
node pool, which can be used with tolerations for pod scheduling.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""

  help_text = node_pool_update_help_text if for_update else node_pool_create_help_text
  vmware_node_config_group.add_argument(
      '--node-taints',
      metavar='KEY=VALUE:EFFECT',
      help=help_text,
      type=arg_parsers.ArgDict(),
  )


def _AddNodeLabels(vmware_node_config_group):
  """Adds a flag to specify the labels in the node pool.

  Args:
    vmware_node_config_group: The parent group to add the flag to.
  """
  vmware_node_config_group.add_argument(
      '--node-labels',
      metavar='KEY=VALUE',
      help='Kubernetes labels (key/value pairs) to be applied to each node.',
      type=arg_parsers.ArgDict(),
  )


def AddVmwareNodeConfig(parser, for_update=False):
  """Adds flags to specify the configuration of the node pool.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  vmware_node_config_group = parser.add_group(
      help='Configuration of the node pool.',
      required=False if for_update else True,
  )
  # Workaround when not yet exposed to update command surface.
  if not for_update:
    _AddCpus(vmware_node_config_group)
    _AddMemoryMb(vmware_node_config_group)
    _AddImage(vmware_node_config_group)
    _AddBootDiskSizeGb(vmware_node_config_group)
    _AddNodeLabels(vmware_node_config_group)
    _AddNodeTaint(vmware_node_config_group)

  _AddReplicas(vmware_node_config_group)
  _AddImageType(vmware_node_config_group, for_update=for_update)
  _AddEnableLoadBalancer(vmware_node_config_group, for_update=for_update)


def AddVmwareNodePoolAutoscalingConfig(parser, for_update=False):
  """Adds a flag to specify the node pool autoscaling config.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  group = parser.add_group('Node pool autoscaling')
  group.add_argument(
      '--min-replicas',
      required=required,
      type=int,
      help='Minimum number of replicas in the node pool.',
  )
  group.add_argument(
      '--max-replicas',
      required=required,
      type=int,
      help='Maximum number of replicas in the node pool.',
  )


def AddVersion(parser):
  """Adds a flag to specify the Anthos cluster on VMware version.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--version',
      help='Anthos Cluster on VMware version for the user cluster resource',
  )


def _AddF5Config(lb_config_mutex_group, for_update=False):
  """Adds flags for F5 Big IP load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  f5_config_group = lb_config_mutex_group.add_group(
      help='F5 Big IP Configuration',)
  f5_config_group.add_argument(
      '--f5-config-address',
      type=str,
      required=required,
      help='F5 Big IP load balancer address.',
  )
  f5_config_group.add_argument(
      '--f5-config-partition',
      type=str,
      required=required,
      help='F5 Big IP load balancer partition.',
  )
  f5_config_group.add_argument(
      '--f5-config-snat-pool',
      type=str,
      help='F5 Big IP load balancer pool name if using SNAT.',
  )


def _AddMetalLbConfig(lb_config_mutex_group, for_update=False):
  """Adds flags for MetalLB load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  metal_lb_config_group = lb_config_mutex_group.add_group(
      'MetalLB Configuration')
  metal_lb_config_group.add_argument(
      '--metal-lb-config-address-pools',
      action='append',
      required=required,
      type=arg_parsers.ArgDict(
          spec={
              'pool': str,
              'addresses': arg_parsers.ArgList(),
              'avoid-buggy-ips': bool,
              'manual-assign': bool,
          },
          required_keys=[
              'pool',
              'addresses',
          ],
      ),
      help='MetalLB typed load balancers configuration.',
  )


def _AddManualLbConfig(lb_config_mutex_group):
  """Adds flags for Manual load balancer.

  Args:
    lb_config_mutex_group: The parent mutex group to add the flags to.
  """
  manual_lb_config_group = lb_config_mutex_group.add_group(
      help='Manual load balancer configuration.',)
  manual_lb_config_group.add_argument(
      '--ingress-http-node-port',
      help='NodePort for ingress service\'s http.',
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--ingress-https-node-port',
      help='NodePort for ingress service\'s https.',
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--control-plane-node-port',
      help='NodePort for control plane service.',
      type=int,
  )
  manual_lb_config_group.add_argument(
      '--konnectivity-server-node-port',
      help='NodePort for konnectivity service running as a sidecar in each kube-apiserver pod.',
      type=int,
  )


def _AddVmwareVipConfig(vmware_load_balancer_config_group, for_update=False):
  """Adds flags to set VIPs used by the load balancer..

  Args:
    vmware_load_balancer_config_group: The parent group to add the flags to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_vip_config_group = vmware_load_balancer_config_group.add_group(
      help=' VIPs used by the load balancer.',
      required=required,
  )
  vmware_vip_config_group.add_argument(
      '--control-plane-vip',
      required=required,
      help='VIP for the Kubernetes API of this cluster.',
  )
  vmware_vip_config_group.add_argument(
      '--ingress-vip',
      required=required,
      help='VIP for ingress traffic into this cluster.',
  )


def AddVmwareLoadBalancerConfig(parser, for_update=False):
  """Adds a command group to set the load balancer config.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_load_balancer_config_group = parser.add_group(
      help='Anthos on Vmware cluster load balancer configuration.',
      required=required,
  )
  _AddVmwareVipConfig(vmware_load_balancer_config_group)

  lb_config_mutex_group = vmware_load_balancer_config_group.add_group(
      mutex=True,
      help='Populate one of the load balancers.',
      required=required,
  )
  _AddMetalLbConfig(lb_config_mutex_group, for_update)
  _AddF5Config(lb_config_mutex_group, for_update)
  _AddManualLbConfig(lb_config_mutex_group)


def AddDescription(parser):
  """Adds a flag to specify the description of the resource.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--description', type=str, help='Description for the resource.')


def AddNodePoolDisplayName(parser):
  """Adds a flag to specify the display name of the node pool.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--display-name', type=str, help='Display name for the resource.')


def AddAnnotations(parser):
  """Adds a flag to specify node pool annotations."""
  parser.add_argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help='Annotations on the node pool.',
  )


def _AddServiceAddressCidrBlocks(vmware_network_config_group, for_update=False):
  """Adds a flag to specify the IPv4 address ranges used in the services in the cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_network_config_group.add_argument(
      '--service-address-cidr-blocks',
      metavar='SERVICE_ADDRESS',
      type=arg_parsers.ArgList(
          min_length=1,
          max_length=1,
      ),
      required=required,
      help='IPv4 address range for all services in the cluster.',
  )


def _AddPodAddressCidrBlocks(vmware_network_config_group, for_update=False):
  """Adds a flag to specify the IPv4 address ranges used in the pods in the cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_network_config_group.add_argument(
      '--pod-address-cidr-blocks',
      metavar='POD_ADDRESS',
      type=arg_parsers.ArgList(
          min_length=1,
          max_length=1,
      ),
      required=required,
      help='IPv4 address range for all pods in the cluster.',
  )


def AddVmwareNetworkConfig(parser, for_update=False):
  """Adds network config related flags.

  Args:
    parser: The argparse parser to add the flag to.
    for_update: bool, True to add flags for update command, False to add flags
      for create command.
  """
  required = False if for_update else True
  vmware_network_config_group = parser.add_group(
      help='VMware User Cluster network configuration.',
      required=required,
  )
  _AddServiceAddressCidrBlocks(vmware_network_config_group, for_update)
  _AddPodAddressCidrBlocks(vmware_network_config_group, for_update)
  _AddIpConfiguration(vmware_network_config_group)
  _AddVmwareHostConfig(vmware_network_config_group)


def AddConfigType(parser):
  """Adds flags to specify version config type.

  Args:
    parser: The argparse parser to add the flag to.
  """
  config_type_group = parser.add_group('Version configuration type', mutex=True)

  create_config = config_type_group.add_group('Create configuration')
  flags.AddAdminClusterMembershipResourceArg(
      create_config, positional=False, required=False)

  upgrade_config = config_type_group.add_group('Upgrade configuration')
  AddClusterResourceArg(
      upgrade_config,
      'to query version configuration',
      positional=False,
      required=False,
      flag_name_overrides={'location': ''})


def _AddIpConfiguration(vmware_network_config_group):
  """Adds flags to specify IP configuration used by the VMware User Cluster.

  Args:
    vmware_network_config_group: The parent group to add the flag to.
  """
  ip_configuration_mutex_group = vmware_network_config_group.add_group(
      mutex=True,
      help='IP configuration used by the VMware User Cluster.',
  )
  dhcp_config_group = ip_configuration_mutex_group.add_group(
      help='DHCP configuration group.')
  dhcp_config_group.add_argument(
      '--enable-dhcp',
      help='Enable DHCP IP allocation for VMware user clusters.',
  )

  static_ip_config_group = ip_configuration_mutex_group.add_group(
      help='Static IP configuration group.')
  static_ip_config_group.add_argument(
      '--netmask',
      help='Netmask used by the VMware user cluster.',
  )
  static_ip_config_group.add_argument(
      '--gateway',
      help='Gateway used by the VMware user cluster.',
  )
  static_ip_config_group.add_argument(
      '--host-ips',
      help='Network configurations used by the VMware user cluster node pools.',
      action='append',
      type=arg_parsers.ArgDict(spec={
          'ip': str,
          'hostname': str,
      },),
  )


def _AddVmwareHostConfig(vmware_network_config_group):
  """Adds flags to specify common parameters for all hosts irrespective of their IP address.

  Args:
    vmware_network_config_group: The parent group to add the flags to.
  """
  vmware_host_config_group = vmware_network_config_group.add_group(
      help='Common parameters for all hosts irrespective of their IP address.')

  vmware_host_config_group.add_argument(
      '--dns-servers',
      metavar='DNS_SERVERS',
      type=arg_parsers.ArgList(str),
      help='DNS server IP address',
  )
  vmware_host_config_group.add_argument(
      '--ntp-servers',
      metavar='NTP_SERVERS',
      type=arg_parsers.ArgList(str),
      help='NTP server IP address',
  )


def AddRequiredPlatformVersion(parser):
  """Adds flags to specify required platform version.

  Args:
    parser: The argparse parser to add the flag to.
  """
  parser.add_argument(
      '--required-platform-version',
      type=str,
      help=('Platform version required for upgrading a user cluster. '
            'If the current platform version is lower than the required '
            'version, the platform version will be updated to the required '
            'version. If it is not installed in the platform, '
            'download the required version bundle.'))
