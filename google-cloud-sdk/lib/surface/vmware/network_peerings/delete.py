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
"""VMware Engine VPC network peering delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networkpeering import NetworkPeeringClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.networks import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Delete a VPC network peering. After you delete a VPC network peering, you won't be able to access the corresponding VMware Engine network through the peer network.
        """,
    'EXAMPLES':
        """
          To delete a VPC network peering with name ``my-peering'', run:

            $ {command} my-peering

          In this example, the project is taken from gcloud properties core/project and location is taken as ``global''.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  """Delete a Google Cloud VMware Engine VPC network peering."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPeeringToParser(parser, positional=True)

  def Run(self, args):
    peering = args.CONCEPTS.network_peering.Parse()
    client = NetworkPeeringClient()
    operation = client.Delete(peering)
    log.DeletedResource(
        operation.name, kind='VPC network peering', is_async=True)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(DescribeAlpha):
  """Delete a Google Cloud VMware Engine VPC network peering."""
