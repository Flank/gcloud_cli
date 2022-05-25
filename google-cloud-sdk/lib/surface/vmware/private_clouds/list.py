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
"""'vmware private-clouds list' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VMware Engine private clouds.
        """,
    'EXAMPLES':
        """
          To list VMware Engine operations in the location ``us-west2-a'', run:

            $ {command} --location=us-west2-a

          Or:

            $ {command}

          In the second example, the location is taken from gcloud properties compute/zone.
    """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List Google Cloud VMware Engine private clouds."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLocationArgToParser(parser)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,'
        'name.segment(-5):label=PROJECT,'
        'name.segment(-3):label=LOCATION,'
        'createTime,state,vcenter.fqdn:label=VCENTER_FQDN)')

  def Run(self, args):
    location = args.CONCEPTS.location.Parse()

    client = PrivateCloudsClient()
    return client.List(location, limit=args.limit)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Google Cloud VMware Engine private clouds."""
  _is_hidden = False
