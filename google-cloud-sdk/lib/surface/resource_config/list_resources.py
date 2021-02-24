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
"""Command for listing all resources supported by bulk-export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags as declarative_flags
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client

_DETAILED_HELP = {
    "EXAMPLES":
        """
    To list all resources supported by bulk-export, run:

      $ {command}

    To list all resources supported by bulk-export in yaml format, run:

      $ {command} --output-format=yaml
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListResources(base.DeclarativeCommand):
  """List all resources supported by bulk-export."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    declarative_flags.AddListResourcesFormatFlag(parser)

  def Run(self, args):
    client = kcc_client.KccClient()
    return client.ListResources(args.output_format)
