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
"""Lists AlloyDB clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.alloydb import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.alloydb import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists AlloyDB clusters in a given project and region.

  Lists AlloyDB clusters in a given project in the alphabetical
  order of the cluster name.
  """

  @staticmethod
  def Args(parser):
    """Specifies additional command flags.

    --region: An optional flag that, if specified, will only list clusters
        within that given region.

    Args:
      parser: argparse.Parser: Parser object for command line inputs.
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
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Responses that we want to have displayed later.
    """
    client = api_util.AlloyDBClient(api_util.API_VERSION_DEFAULT)
    alloydb_client = client.alloydb_client
    alloydb_messages = client.alloydb_messages
    project_ref = client.resource_parser.Create(
        'alloydbadmin.projects.locations',
        projectsId=properties.VALUES.core.project.GetOrFail,
        locationsId=args.region)

    result = list_pager.YieldFromList(
        alloydb_client.projects_locations_clusters,
        alloydb_messages.AlloydbadminProjectsLocationsClustersListRequest(
            parent=project_ref.RelativeName(), pageSize=args.limit),
        field='clusters',
        batch_size_attribute=None)

    return result
