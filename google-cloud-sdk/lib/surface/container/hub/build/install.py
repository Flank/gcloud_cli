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
"""The command to install Cloud Build on a cluster."""

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
class Install(base.UpdateCommand):
  r"""Install Cloud Build on the specified member.

  ### Examples

  Install Cloud Build hybrid worker pools on a member named MEMBERSHIP-ID.
  If the desired security policy or version is omitted, the member will be
  configured as
  NON_PRIVILEGED with the latest version of Cloud Build.

    $ {command} --membership=[MEMBERSHIP-ID]

  Install Cloud Build hybrid worker pools on a member named MEMBERSHIP-ID.
  The installation configuration will have security policy [SECURITY_POLICY]
  and version [X.Y.Z].

    $ {command} --membership=[MEMBERSHIP-ID]
    --security-policy=[SECURITY_POLICY] \
    --version=[X.Y.Z]

  """

  feature_name = 'cloudbuild'
  LATEST_VERSION = '0.1.0'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
            The name of the Membership to install Cloud Build hybrid worker pools on.
            """),
        required=True,
    )
    parser.add_argument(
        '--security-policy',
        type=str,
        default='NON_PRIVILEGED',
        choices=['NON_PRIVILEGED', 'PRIVILEGED'],
        help=textwrap.dedent("""\
            Privilege options for build steps.
            """),
        required=False,
    )
    parser.add_argument(
        '--version',
        type=str,
        default=cls.LATEST_VERSION,
        choices=[cls.LATEST_VERSION],
        help=textwrap.dedent("""\
            Cloud Build version to be installed on the member.
            """),
        required=False,
    )

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    feature = utils.GetFeature(self.feature_name, self.feature.display_name,
                               project)
    membership = utils.GetMembership(args.membership, project)

    version = self._parse_version(args.version)
    messages = core_apis.GetMessagesModule('gkehub', 'v1alpha1')

    feature_spec_memberships = utils.GetFeatureSpecMemberships(
        feature, messages)
    # TODO(b/189313110): Move check to CLH/API
    if membership in feature_spec_memberships:
      raise exceptions.Error(
          'Cloud Build hybrid worker pool installation on the member already exists.'
      )

    securitypolicy = utils.ParseSecuritypolicy(args.security_policy, messages)
    applied_config = messages.CloudBuildFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership,
        value=messages.CloudBuildMembershipConfig(
            securityPolicy=securitypolicy, version=version))
    m_configs = messages.CloudBuildFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'cloudbuild_feature_spec.membership_configs',
        cloudbuildFeatureSpec=messages.CloudBuildFeatureSpec(
            membershipConfigs=m_configs))

  def _parse_version(self, version):
    if version is None:
      return self.LATEST_VERSION
    return version
