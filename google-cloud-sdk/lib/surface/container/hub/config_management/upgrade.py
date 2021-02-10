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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

MEMBERSHIP_FLAG = '--membership'


class Upgrade(base.UpdateCommand):
  r"""Upgrades the version of the Config Management Feature.

  Upgrades a specified membership to the latest version of the
  Config Management Feature.

  ## Examples

  Upgrade a membership named CLUSTER_NAME

    $ {command} --membership=CLUSTER_NAME \
  """

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Config Management'
  LATEST_VERSION = '1.6.0'
  FEATURE_API = 'anthosconfigmanagement.googleapis.com'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        MEMBERSHIP_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The Membership name provided during registration.
            """),
    )

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    feature_data = self._get_feature(project)
    membership = _get_or_prompt_membership(args, project)
    declared_v, cluster_v = _parse_versions(feature_data, membership)

    if not self._validate_versions(membership, declared_v, cluster_v):
      return
    console_io.PromptContinue(
        'You are about to upgrade the {} Feature for membership {} from version "{}" to version '
        '"{}".'.format(self.FEATURE_DISPLAY_NAME, membership,
                       cluster_v, self.LATEST_VERSION),
        throw_if_unattended=True,
        cancel_on_no=True)

    client = core_apis.GetClientInstance('gkehub', 'v1alpha1')
    msg = client.MESSAGES_MODULE
    mem_config = _parse_membership(feature_data,
                                   membership) or msg.MembershipConfig()
    mem_config.version = self.LATEST_VERSION
    applied_config = msg.ConfigManagementFeatureSpec.MembershipConfigsValue.AdditionalProperty(
        key=membership, value=mem_config)
    m_configs = msg.ConfigManagementFeatureSpec.MembershipConfigsValue(
        additionalProperties=[applied_config])
    self.RunCommand(
        'configmanagement_feature_spec.membership_configs',
        configmanagementFeatureSpec=msg.ConfigManagementFeatureSpec(
            membershipConfigs=m_configs))

  def _validate_versions(self, membership, declared_v, cluster_v):
    if declared_v == self.LATEST_VERSION:
      log.status.Print(
          'Membership {} already has the latest version of the {} Feature declared ({}).'
          .format(membership, self.FEATURE_DISPLAY_NAME, self.LATEST_VERSION))
      return False
    if cluster_v == self.LATEST_VERSION:
      log.status.Print(
          'Membership {} already has the latest version of the {} Feature installed ({}).'
          .format(membership, self.FEATURE_DISPLAY_NAME, self.LATEST_VERSION))
      return False

    if cluster_v > self.LATEST_VERSION:
      raise exceptions.Error(
          'Membership {} has a version of the {} Feature installed ({}) that is '
          'not supported by this command.'.format(membership,
                                                  self.FEATURE_DISPLAY_NAME,
                                                  cluster_v))

    return True

  def _get_feature(self, project):
    """Fetches the Config Management Feature.

    Args:
      project: project id

    Returns:
      configManagementFeature
    """
    try:
      name = 'projects/{0}/locations/global/features/{1}'.format(
          project, self.FEATURE_NAME)
      response = base.GetFeature(name)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to see the status of {} '
          'Feature from project [{}]. Underlying error: {}'.format(
              self.FEATURE_DISPLAY_NAME, project, e))
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.Error(
          '{} Feature for project [{}] is not enabled'.format(
              self.FEATURE_DISPLAY_NAME, project))

    return response


def _parse_versions(response, membership):
  """Extracts the declared version and cluster version.

  Args:
    response: A response from fetching the Config Management Feature
    membership: membership name

  Returns:
    A tuple of the form (declared version, cluster version).
  """
  declared_version = ''
  mem_config = _parse_membership(response, membership)
  if mem_config and mem_config.version:
    declared_version = mem_config.version

  cluster_version = ''
  if response.featureState.detailsByMembership:
    membership_details = response.featureState.detailsByMembership.additionalProperties
    for m in membership_details:
      if os.path.basename(m.key) == membership:
        fs = m.value.configmanagementFeatureState
        if fs and fs.membershipConfig and fs.membershipConfig.version:
          cluster_version = fs.membershipConfig.version

  return declared_version, cluster_version


def _get_or_prompt_membership(args, project):
  """Retrieves the membership name from args or prompts the user.

  Args:
    args: command line args
    project: project id
  Returns:
    membership: A membership name
  Raises: Error, if specified membership could not be found
  """
  memberships = base.ListMemberships(project)
  if not memberships:
    raise exceptions.Error('No Memberships available in Hub.')
  # User should choose an existing membership if this arg wasn't provided
  if not args.membership:
    index = console_io.PromptChoice(
        options=memberships,
        message='Please specify a membership to upgrade:\n')
    membership = memberships[index]
  else:
    membership = args.membership
    if membership not in memberships:
      raise exceptions.Error('Membership {} is not in Hub.'.format(membership))
  return membership


def _parse_membership(response, membership):
  if response.configmanagementFeatureSpec is None or response.configmanagementFeatureSpec.membershipConfigs is None:
    return None

  for details in response.configmanagementFeatureSpec.membershipConfigs.additionalProperties:
    if details.key == membership:
      return details.value
