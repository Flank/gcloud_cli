# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Creates a new Lux cluster."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.lux import api_util
from googlecloudsdk.api_lib.lux import cluster_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.lux import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Creates a new Lux cluster within a given project."""

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

      --region: the region the cluster will be located in.

    Args:
      parser: argparse.Parser: Parser object for command line inputs

    """

    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddRegion(parser)
    flags.AddCluster(parser)

  def Run(self, args):
    args.format = 'default'
    client = api_util.LuxClient(api_util.API_VERSION_DEFAULT)
    lux_client = client.lux_client
    lux_messages = client.lux_messages
    project_ref = client.resource_parser.Create(
        'luxadmin.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)
    req = lux_messages.LuxadminProjectsLocationsClustersCreateRequest(
        clusterId=args.cluster,
        parent=project_ref.RelativeName())
    op = lux_client.projects_locations_clusters.Create(req)
    if not args.async_:
      cluster_operations.Await(op, 'Creating cluster')
    return op
