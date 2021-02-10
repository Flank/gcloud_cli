# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to describe a KubeRun Backing Resource."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import backing_resource_printer
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core.resource import resource_printer

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all the data about a KubeRun Backing Resource, run:

            $ {command} RESOURCE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(kuberun_command.KubeRunCommand, base.DescribeCommand):
  """Describe a KubeRun Backing Resource."""

  detailed_help = _DETAILED_HELP
  flags = []

  @classmethod
  def Args(cls, parser):
    super(Describe, cls).Args(parser)
    parser.add_argument('resource', help='Name of the resource.')
    resource_printer.RegisterFormatter(
        backing_resource_printer.RESOURCE_PRINTER_FORMAT,
        backing_resource_printer.ResourcePrinter,
        hidden=True)
    parser.display_info.AddFormat(
        backing_resource_printer.RESOURCE_PRINTER_FORMAT)

  def Command(self):
    return ['resources', 'describe']

  def BuildKubeRunArgs(self, args):
    return [args.resource]

  def FormatOutput(self, out, args):
    return json.loads(out)
