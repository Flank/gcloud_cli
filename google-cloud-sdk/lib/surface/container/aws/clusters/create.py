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
"""Command to create a new GKE cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import clusters
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a GKE cluster on AWS."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    resource_args.AddAwsClusterResourceArg(parser, 'to create')
    flags.AddClusterIpv4Cidr(parser)
    flags.AddServiceIpv4Cidr(parser)
    flags.AddClusterVersion(parser)
    flags.AddSubnetId(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddMainVolumeSize(parser)
    flags.AddValidateOnly(parser, 'cluster to create')
    flags.AddTags(parser)

    aws_flags.AddAwsRegion(parser)
    aws_flags.AddServicesLbSubnetId(parser)
    aws_flags.AddIamInstanceProfile(parser)
    aws_flags.AddInstanceType(parser)
    aws_flags.AddKeyPairName(parser)
    aws_flags.AddDatabaseEncryptionKey(parser)
    aws_flags.AddRoleArn(parser)
    aws_flags.AddRoleSessionName(parser)
    aws_flags.AddVpcId(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(clusters.CLUSTERS_FORMAT)

  def Run(self, args):
    """Run the create command."""
    release_track = self.ReleaseTrack()
    cluster_ref = args.CONCEPTS.cluster.Parse()

    with endpoint_util.GkemulticloudEndpointOverride(cluster_ref.locationsId,
                                                     release_track):
      cluster_client = clusters.Client(track=release_track)
      op = cluster_client.Create(cluster_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      validate_only = getattr(args, 'validate_only', False)
      if validate_only:
        args.format = 'disable'
        return

      async_ = getattr(args, 'async_', False)
      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                cluster_client.client.projects_locations_operations), op_ref,
            'Creating cluster {} in AWS region {}'.format(
                cluster_ref.awsClustersId, args.aws_region))

      log.CreatedResource(cluster_ref)
      return cluster_client.Get(cluster_ref)
