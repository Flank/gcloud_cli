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
"""Describe template command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet.policycontroller import status_api_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from surface.container.fleet.policycontroller import templates as poco_templates


@calliope_base.Hidden
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Describe(calliope_base.DescribeCommand):
  """Describe Policy Controller constraint template.

  ## EXAMPLES

  To describe the "k8srequiredlabels" constraint template:

      $ {command} k8srequiredlabels
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'TEMPLATE_NAME',
        type=str,
        help='The constraint template name.'
    )

  def Run(self, args):
    calliope_base.EnableUserProjectQuota()

    project_id = properties.VALUES.core.project.Get(required=True)

    client = status_api_utils.GetClientInstance(
        self.ReleaseTrack())
    messages = status_api_utils.GetMessagesModule(
        self.ReleaseTrack())

    formatted_templates = poco_templates.list_membership_templates(
        project_id, messages, client, name_filter=args.TEMPLATE_NAME)

    if not formatted_templates:
      log.status.Print('Template {} not found.'.format(args.TEMPLATE_NAME))

    return formatted_templates