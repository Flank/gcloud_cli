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
"""'vmware operations describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.operations import OperationsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe operation
        """,
    'EXAMPLES':
        """
          To get a description of private cloud related operation
          ``operation-1620372841887-5c1b873a4f837-589a2b50-51e0613c''
          in location ``us-west1-a''
          region, run:

            $ {command} operation-1620372841887-5c1b873a4f837-589a2b50-51e0613c --location=us-central1 --project=my-project

          Or:

            $ {command} operation-1620372841887-5c1b873a4f837-589a2b50-51e0613c --location=us-central1

          In the second example, the project and region are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe VMware Engine operation."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddOperationArgToParser(parser)

  def Run(self, args):
    resource = args.CONCEPTS.operation.Parse()
    client = OperationsClient()
    return client.Get(resource)


Describe.detailed_help = DETAILED_HELP
