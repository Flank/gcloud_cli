# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Create node pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.command_lib.container import container_command_util as cmd_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        *{command}* facilitates the creation of a node pool in a Google
        Kubernetes Engine cluster. A variety of options exists to customize the
        node configuration and the number of nodes created.
        """,
    'EXAMPLES':
        """\
        To create a new node pool "node-pool-1" with the default options in the
        cluster "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster

        The new node pool will show up in the cluster after all the nodes have
        been provisioned.

        To create a node pool with 5 nodes, run:

          $ {command} node-pool-1 --cluster=sample-cluster --num-nodes=5
        """,
}

WARN_WINDOWS_SAC_SUPPORT_LIFECYCLE = (
    'Windows SAC node pools must be upgraded regularly to remain operational. '
    'Please refer to https://cloud.google.com/kubernetes-engine/docs/how-to/'
    'creating-a-cluster-windows#choose_your_windows_server_node_image for more '
    'information.')


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  flags.AddNodePoolNameArg(parser, 'The name of the node pool to create.')
  flags.AddNodePoolClusterFlag(parser, 'The cluster to add the node pool to.')
  # Timeout in seconds for operation
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,
      hidden=True,
      help='THIS ARGUMENT NEEDS HELP TEXT.')
  parser.add_argument(
      '--num-nodes',
      type=int,
      help='The number of nodes in the node pool in each of the '
      'cluster\'s zones.',
      default=3)
  flags.AddMachineTypeFlag(parser)
  parser.add_argument(
      '--disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='Size for node VM boot disks. Defaults to 100GB.')
  flags.AddImageTypeFlag(parser, 'node pool')
  flags.AddImageFlag(parser, hidden=True)
  flags.AddImageProjectFlag(parser, hidden=True)
  flags.AddImageFamilyFlag(parser, hidden=True)
  flags.AddNodeLabelsFlag(parser, for_node_pool=True)
  flags.AddTagsFlag(
      parser, """\
Applies the given Compute Engine tags (comma separated) on all nodes in the new
node-pool. Example:

  $ {command} node-pool-1 --cluster=example-cluster --tags=tag1,tag2

New nodes, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and can be used in firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
""")
  parser.display_info.AddFormat(util.NODEPOOLS_FORMAT)
  flags.AddNodeVersionFlag(parser)
  flags.AddDiskTypeFlag(parser)
  flags.AddMetadataFlags(parser)
  flags.AddShieldedInstanceFlags(parser)


def ParseCreateNodePoolOptionsBase(args):
  """Parses the flags provided with the node pool creation command."""
  enable_autorepair = cmd_util.GetAutoRepair(args)
  flags.WarnForNodeModification(args, enable_autorepair)
  flags.ValidateSurgeUpgradeSettings(args)
  metadata = metadata_utils.ConstructMetadataDict(args.metadata,
                                                  args.metadata_from_file)
  return api_adapter.CreateNodePoolOptions(
      accelerators=args.accelerator,
      boot_disk_kms_key=args.boot_disk_kms_key,
      machine_type=args.machine_type,
      disk_size_gb=utils.BytesToGb(args.disk_size),
      scopes=args.scopes,
      node_version=args.node_version,
      num_nodes=args.num_nodes,
      local_ssd_count=args.local_ssd_count,
      tags=args.tags,
      node_labels=args.node_labels,
      node_taints=args.node_taints,
      enable_autoscaling=args.enable_autoscaling,
      max_nodes=args.max_nodes,
      min_cpu_platform=args.min_cpu_platform,
      min_nodes=args.min_nodes,
      image_type=args.image_type,
      image=args.image,
      image_project=args.image_project,
      image_family=args.image_family,
      preemptible=args.preemptible,
      enable_autorepair=enable_autorepair,
      enable_autoupgrade=cmd_util.GetAutoUpgrade(args),
      service_account=args.service_account,
      disk_type=args.disk_type,
      metadata=metadata,
      max_pods_per_node=args.max_pods_per_node,
      enable_autoprovisioning=args.enable_autoprovisioning,
      workload_metadata=args.workload_metadata,
      workload_metadata_from_node=args.workload_metadata_from_node,
      shielded_secure_boot=args.shielded_secure_boot,
      shielded_integrity_monitoring=args.shielded_integrity_monitoring,
      reservation_affinity=args.reservation_affinity,
      reservation=args.reservation,
      sandbox=args.sandbox,
      max_surge_upgrade=args.max_surge_upgrade,
      max_unavailable_upgrade=args.max_unavailable_upgrade,
      node_group=args.node_group,
      system_config_from_file=args.system_config_from_file)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(parser, enable_gpu_partition=False)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDFlag(parser)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddNodeGroupFlag(parser)

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    ops.node_locations = args.node_locations
    return ops

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Cluster message for the successfully created node pool.

    Raises:
      util.Error, if creation failed.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    try:
      pool_ref = adapter.ParseNodePool(args.name, location)
      options = self.ParseCreateNodePoolOptions(args)

      if options.accelerators is not None:
        log.status.Print(constants.KUBERNETES_GPU_LIMITATION_MSG)

      if not options.image_type:
        log.warning(
            'Starting with version 1.19, newly created node-pools '
            'will have COS_CONTAINERD as the default node image '
            'when no image type is specified.'
        )
      elif options.image_type.upper() == 'WINDOWS_SAC':
        log.warning(WARN_WINDOWS_SAC_SUPPORT_LIFECYCLE)

      operation_ref = adapter.CreateNodePool(pool_ref, options)

      adapter.WaitForOperation(
          operation_ref,
          'Creating node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
      pool = adapter.GetNodePool(pool_ref)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.CreatedResource(pool_ref)
    return [pool]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(parser, enable_gpu_partition=True)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddLocalSSDsBetaFlags(parser, for_node_pool=True)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True, default=1)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddNodeGroupFlag(parser)
    flags.AddEnableGcfsFlag(parser, for_node_pool=True)
    flags.AddEnableImageStreamingFlag(parser, for_node_pool=True)
    flags.AddNetworkConfigFlags(parser)
    flags.AddNodePoolEnablePrivateNodes(parser, hidden=True)
    flags.AddThreadsPerCore(parser)

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    ops.threads_per_core = args.threads_per_core
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.sandbox = args.sandbox
    ops.node_locations = args.node_locations
    ops.system_config_from_file = args.system_config_from_file
    ops.enable_gcfs = args.enable_gcfs
    ops.enable_image_streaming = args.enable_image_streaming
    ops.ephemeral_storage = args.ephemeral_storage
    ops.pod_ipv4_range = args.pod_ipv4_range
    ops.create_pod_ipv4_range = args.create_pod_ipv4_range
    ops.enable_private_nodes = args.enable_private_nodes
    return ops


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a node pool in a running cluster."""

  def ParseCreateNodePoolOptions(self, args):
    ops = ParseCreateNodePoolOptionsBase(args)
    ops.threads_per_core = args.threads_per_core
    flags.WarnForNodeVersionAutoUpgrade(args)
    flags.ValidateSurgeUpgradeSettings(args)
    ops.local_ssd_volume_configs = args.local_ssd_volumes
    ops.ephemeral_storage = args.ephemeral_storage
    ops.boot_disk_kms_key = args.boot_disk_kms_key
    ops.sandbox = args.sandbox
    ops.linux_sysctls = args.linux_sysctls
    ops.node_locations = args.node_locations
    ops.system_config_from_file = args.system_config_from_file
    ops.enable_gcfs = args.enable_gcfs
    ops.enable_image_streaming = args.enable_image_streaming
    ops.pod_ipv4_range = args.pod_ipv4_range
    ops.create_pod_ipv4_range = args.create_pod_ipv4_range
    ops.enable_private_nodes = args.enable_private_nodes
    return ops

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddAcceleratorArgs(parser, enable_gpu_partition=True)
    flags.AddClusterAutoscalingFlags(parser)
    flags.AddNodePoolAutoprovisioningFlag(parser, hidden=False)
    flags.AddLocalSSDsAlphaFlags(parser, for_node_pool=True)
    flags.AddBootDiskKmsKeyFlag(parser)
    flags.AddPreemptibleFlag(parser, for_node_pool=True)
    flags.AddEnableAutoRepairFlag(parser, for_node_pool=True, for_create=True)
    flags.AddMinCpuPlatformFlag(parser, for_node_pool=True)
    flags.AddWorkloadMetadataFlag(parser, use_mode=False)
    flags.AddNodeTaintsFlag(parser, for_node_pool=True)
    flags.AddNodePoolNodeIdentityFlags(parser)
    flags.AddMaxPodsPerNodeFlag(parser, for_node_pool=True)
    flags.AddSandboxFlag(parser)
    flags.AddNodeGroupFlag(parser)
    flags.AddEnableAutoUpgradeFlag(parser, for_node_pool=True, default=True)
    flags.AddLinuxSysctlFlags(parser, for_node_pool=True)
    flags.AddSurgeUpgradeFlag(parser, for_node_pool=True, default=1)
    flags.AddMaxUnavailableUpgradeFlag(
        parser, for_node_pool=True, is_create=True)
    flags.AddNodePoolLocationsFlag(parser, for_create=True)
    flags.AddSystemConfigFlag(parser, hidden=False)
    flags.AddReservationAffinityFlags(parser, for_node_pool=True)
    flags.AddEnableGcfsFlag(parser, for_node_pool=True)
    flags.AddEnableImageStreamingFlag(parser, for_node_pool=True)
    flags.AddNetworkConfigFlags(parser)
    flags.AddNodePoolEnablePrivateNodes(parser, hidden=True)
    flags.AddThreadsPerCore(parser)


Create.detailed_help = DETAILED_HELP
