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
"""The command to list all the members with Cloud Build installed."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as gbase
from googlecloudsdk.command_lib.container.hub.build import utils
from googlecloudsdk.command_lib.container.hub.features import base
from googlecloudsdk.core import properties


@gbase.Hidden
class List(base.FeatureCommand, gbase.ListCommand):
  """Lists all members with Cloud Build installed.

  Lists all members with Cloud Build installed.

  ## Examples

    $ {command}
  """

  feature_name = 'cloudbuild'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    table(
            NAME:label=NAME:sort=1
      )
    """)

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    feature = utils.GetFeature(self.feature_name, self.feature.display_name,
                               project)

    messages = core_apis.GetMessagesModule('gkehub', 'v1alpha1')

    feature_spec_memberships = _parse_feature_spec_memberships(
        feature, messages)

    cluster_list = []
    for membership in feature_spec_memberships:
      cluster_list.append({'NAME': membership})

    return cluster_list


def _parse_feature_spec_memberships(feature, messages):
  """Return feature spec for every registered member."""
  if feature.cloudbuildFeatureSpec is None or feature.cloudbuildFeatureSpec.membershipConfigs is None:
    feature_spec_membership_details = []
  else:
    feature_spec_membership_details = feature.cloudbuildFeatureSpec.membershipConfigs.additionalProperties

  status = {}
  for membership_detail in feature_spec_membership_details:
    if membership_detail.value != messages.CloudBuildMembershipConfig():
      status[membership_detail.key] = membership_detail.value

  return status
