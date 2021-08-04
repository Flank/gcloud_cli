# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to create a new GKE node pool on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.azure import util as command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a node pool in an Azure cluster."""

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(
        parser, 'to create', positional=True)

    flags.AddNodeVersion(parser)
    flags.AddAutoscaling(parser)
    flags.AddSubnetID(parser, 'the node pool')
    flags.AddVMSize(parser)
    flags.AddSSHPublicKey(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddTags(parser, 'node pool')
    flags.AddValidateOnly(parser, 'creation of the node pool')
    flags.AddMaxPodsPerNode(parser)
    flags.AddNodeLabels(parser)
    flags.AddNodeTaints(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(command_util.NODE_POOL_FORMAT)

  def Run(self, args):
    """Run the create command."""

    node_version = flags.GetNodeVersion(args)
    subnet_id = flags.GetSubnetID(args)
    vm_size = flags.GetVMSize(args)
    ssh_key = flags.GetSSHPublicKey(args)
    root_volume_size = flags.GetRootVolumeSize(args)
    tags = flags.GetTags(args)
    validate_only = flags.GetValidateOnly(args)
    max_pods_per_node = flags.GetMaxPodsPerNode(args)
    min_nodes, max_nodes = flags.GetAutoscalingParams(args)
    taints = flags.GetNodeTaints(args)
    labels = flags.GetNodeLabels(args)

    async_ = args.async_

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureNodePoolResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      nodepool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
      api_client = azure_api_util.NodePoolsClient(track=self.ReleaseTrack())
      op = api_client.Create(
          nodepool_ref=nodepool_ref,
          node_version=node_version,
          subnet_id=subnet_id,
          vm_size=vm_size,
          ssh_public_key=ssh_key,
          root_volume_size=root_volume_size,
          tags=tags,
          validate_only=validate_only,
          min_nodes=min_nodes,
          max_nodes=max_nodes,
          max_pods_per_node=max_pods_per_node,
          taints=taints,
          labels=labels)

      if validate_only:
        args.format = 'disable'
        return

      op_ref = resource_args.GetOperationResource(op)
      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                api_client.client.projects_locations_operations),
            op_ref,
            'Creating node pool {}'.format(nodepool_ref.azureNodePoolsId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.CreatedResource(
          nodepool_ref, kind=constants.AZURE_NODEPOOL_KIND, is_async=async_)
      return api_client.Get(nodepool_ref)
