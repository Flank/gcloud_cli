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
"""Command to describe a GKE cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import node_pools
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.ListCommand):
  """List GKE node pools on AWS."""

  @staticmethod
  def Args(parser):
    resource_args.AddAwsClusterResourceArg(parser, 'to list', positional=False)
    parser.display_info.AddFormat(node_pools.NODEPOOLS_FORMAT)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    node_pool_client = node_pools.NodePoolsClient(track=release_track)
    cluster_ref = args.CONCEPTS.cluster.Parse()

    with endpoint_util.GkemulticloudEndpointOverride(cluster_ref.locationsId,
                                                     release_track):
      node_pool_client = node_pools.NodePoolsClient(track=release_track)
      return node_pool_client.List(cluster_ref, args)
