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
"""Describes a Lux cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.lux import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.lux import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describes a Lux cluster in a given project and region."""

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

      --region: the region the cluster is located in

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    flags.AddRegion(parser)
    flags.AddCluster(parser)

  def Run(self, args):
    """Describes a Lux cluster in a given project and region.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Lux cluster resource iterator used for displaying resources.
    """
    args.format = 'default'
    client = api_util.LuxClient(api_util.API_VERSION_DEFAULT)
    lux_client = client.lux_client
    lux_messages = client.lux_messages
    project_ref = client.resource_parser.Create(
        'luxadmin.projects.locations.clusters',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region, clustersId=args.cluster)
    req = lux_messages.LuxadminProjectsLocationsClustersGetRequest(
        name=project_ref.RelativeName())
    return lux_client.projects_locations_clusters.Get(req)
