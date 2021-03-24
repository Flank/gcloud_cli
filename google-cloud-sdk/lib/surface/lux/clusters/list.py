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
"""Lists clusters in a given project and region.

Lists clusters in a given project in the alphabetical order of the
cluster name.
"""

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
  """Lists Lux clusters in a given region.

  Lists Lux clusters in a given project in the alphabetical
  order of the cluster name.
  """

  @staticmethod
  def Args(parser):
    flags.AddRegion(parser)
    parser.display_info.AddFormat(flags.GetClusterListFormat())

  def Run(self, args):
    """Lists Lux clusters in a given project.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Lux cluster resource iterator.
    """
    client = api_util.LuxClient(api_util.API_VERSION_DEFAULT)
    lux_client = client.lux_client
    lux_messages = client.lux_messages
    project_id = properties.VALUES.core.project.Get(required=True)
    collection_info = client.resource_parser.GetCollectionInfo(
        'luxadmin.projects.locations', api_util.API_VERSION_DEFAULT)
    path = collection_info.GetPath('')
    params = {
        'projectsId': project_id,
        'locationsId': args.region
    }
    path = path.format(**params)

    result = list_pager.YieldFromList(
        lux_client.projects_locations_clusters,
        lux_messages.LuxadminProjectsLocationsClustersListRequest(
            parent=path),
        field='resources',
        batch_size_attribute=None)
    return result
