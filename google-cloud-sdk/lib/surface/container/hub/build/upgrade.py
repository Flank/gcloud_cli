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
"""The command to upgrade a Cloud Build cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


@gbase.Hidden
class Upgrade(base.UpdateCommand):
  r"""Upgrades the Cloud Build installation on the specified member.

  ### Examples

  Upgrades the Cloud Build version on a member named [MEMBERSHIP-ID].
  Defaults to the latest version if the --version flag is omitted

    $ {command} --membership=[MEMBERSHIP-ID] --version=[X.Y.Z]

  """

  feature_name = 'cloudbuild'
  LATEST_VERSION = '0.1.0'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
            The name of the Membership to upgrade.
            """),
        required=True,
    )
    parser.add_argument(
        '--version',
        type=str,
        default=cls.LATEST_VERSION,
        choices=[cls.LATEST_VERSION],
        help=textwrap.dedent("""\
          Cloud Build version to upgrade to. Default to the latest version when omitted.
            """),
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
      raise exceptions.Error(
          'No Cloud Build hybrid worker pool installation was registered for this membership.'
      )

    mem_config = feature_spec_memberships[membership]
    mem_config.version = self._parse_version(args.version, mem_config.version,
                                             membership)
    applied_config = messages.CloudBuildFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership, value=mem_config)
    m_configs = messages.CloudBuildFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'cloudbuild_feature_spec.membership_configs',
        cloudbuildFeatureSpec=messages.CloudBuildFeatureSpec(
            membershipConfigs=m_configs))

  def _parse_version(self, version_requested, version_installed, membership):
    if version_requested is None:
      version_requested = self.LATEST_VERSION
    if version_requested == version_installed:
      raise exceptions.Error(
          'Membership {} already has version {} of the {} Feature installed.'
          .format(membership, version_installed, self.feature.display_name))
    if version_requested < version_installed:
      raise exceptions.Error(
          'Membership {} has version {} of the {} Feature installed and can not be downgraded to {}.'
          .format(membership, version_installed, self.feature.display_name,
                  version_requested))
    if version_requested > self.LATEST_VERSION:
      raise exceptions.Error(
          'Version {} does not exist.'.format(version_requested))

    return version_requested
