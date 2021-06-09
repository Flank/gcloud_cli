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
"""The command to uninstall Cloud Build from a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@gbase.Hidden
class Uninstall(base.UpdateCommand):
  r"""Uninstall Cloud Build from the specified member.

  ### Examples

  Uninstall Cloud Build from a member named MEMBERSHIP-ID:

    $ {command} --membership=[MEMBERSHIP-ID]
  """

  feature_name = 'cloudbuild'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
            The name of the Membership to uninstall Cloud Build from.
            """),
        required=True,
    )

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    feature = utils.GetFeature(self.feature_name, self.feature.display_name,
                               project)
    membership = utils.GetMembership(args.membership, project)
    messages = core_apis.GetMessagesModule('gkehub', 'v1alpha1')

    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, messages)
    if membership not in feature_spec_memberships:
      log.warning(
          'No Cloud Build installation was registered for this membership.')

    applied_config = messages.CloudBuildFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership, value=messages.CloudBuildMembershipConfig())
    m_configs = messages.CloudBuildFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'cloudbuild_feature_spec.membership_configs',
        cloudbuildFeatureSpec=messages.CloudBuildFeatureSpec(
            membershipConfigs=m_configs))
