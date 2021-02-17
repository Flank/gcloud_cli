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
"""Command to create a new Kuberun Backing Resource."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To create a new Backing Resource, run:

            $ {command}  RESOURCE --template TEMPLATE
        """,
}


def _TemplateFlag():
  return flags.StringFlag(
      '--template',
      help='Type of template to use for the resource definition',
      required=True)


def _EnvironmentFlag():
  return flags.StringFlag(
      '--environment',
      help='If set, the name of the environment the resource applies to. If '
      'not set, the resource will be the default value for all environments',
      required=False)


def _DataFlag():
  return flags.StringFlag(
      '--data',
      help='Additional parameters as JSON to pass to the template',
      required=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(kuberun_command.KubeRunCommand, base.CreateCommand):
  """Create a new Backing Resource."""

  detailed_help = _DETAILED_HELP
  flags = [_TemplateFlag(), _EnvironmentFlag(), _DataFlag()]

  @classmethod
  def Args(cls, parser):
    super(Create, cls).Args(parser)
    parser.add_argument('resource', help='Name of the backing resource.')

  def Command(self):
    return ['resources', 'add']

  def BuildKubeRunArgs(self, args):
    return [args.resource] + super(Create, self).BuildKubeRunArgs(args)
