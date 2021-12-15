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
"""'vmware privateclouds delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Marks a VMware Engine private cloud for deletion. The resource is deleted 3 hours after being marked for deletion. This process can be reversed by using `{parent_command} undelete`.
        """,
    'EXAMPLES':
        """
          To mark a private cloud called ``my-private-cloud'' for deletion, run:

            $ {command} my-private-cloud --location=us-west2-a --project=my-project

          Or:

            $ {command} my-private-cloud

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(base.DeleteCommand):
  """Delete a Google Cloud VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    parser.add_argument(
        '--delay-hours',
        required=False,
        hidden=True,
        default=3,
        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        type=int,
        help="""
        Number of hours to wait before deleting the private cloud. Specifying a value of `0` for this field begins the deletion process immediately.
        """)

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    operation = client.Delete(privatecloud, args.delay_hours)
    log.DeletedResource(operation.name, kind='private cloud', is_async=True)


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(DeleteAlpha):
  """Delete a Google Cloud VMware Engine private cloud."""
