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
"""Lists Lux clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.lux import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.lux import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists Lux clusters in a given project and region.

  Lists Lux clusters in a given project in the alphabetical
  order of the cluster name.
  """

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    --region: an optional flag that, if specified, will only list clusters
        within that given region.

    Args:
      parser: argparse.Parser: Parser object for command line inputs
    """
    parser.add_argument(
        '--region',
        default='-',
        help=('Regional location (e.g. asia-east1, us-east1). See the full '
              'list of regions at '
              'https://cloud.google.com/sql/docs/instance-locations. '
              'Default: list clusters in all regions.'))
    parser.display_info.AddFormat(flags.GetClusterListFormat())

  def Run(self, args):
    """Lists Lux clusters in a given project.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Lux cluster resource iterator used for displaying resources.
    """
    client = api_util.LuxClient(api_util.API_VERSION_DEFAULT)
    lux_client = client.lux_client
    lux_messages = client.lux_messages
    project_ref = client.resource_parser.Create(
        'luxadmin.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)

    result = list_pager.YieldFromList(
        lux_client.projects_locations_clusters,
        lux_messages.LuxadminProjectsLocationsClustersListRequest(
            parent=project_ref.RelativeName(), pageSize=args.limit),
        field='resources',
        batch_size_attribute=None)

    return result
