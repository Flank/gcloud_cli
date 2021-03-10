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
"""The command to get the version of all memberships with the Config Management Feature enabled."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.hub.features import base as feature_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

NA = 'NA'


class ConfigmanagementFeatureState(object):
  """Feature state class stores ACM status."""

  def __init__(self, clusterName):
    self.name = clusterName
    self.version = NA


class Version(base.ListCommand):
  """Print the version of all clusters with Config Management enabled."""

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Anthos Config Management'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(name:label=Name:sort=1,version:label=Version)')

  def Run(self, args):
    try:
      project_id = properties.VALUES.core.project.GetOrFail()
      memberships = feature_base.ListMemberships(project_id)
      name = 'projects/{0}/locations/global/features/{1}'.format(
          project_id, self.FEATURE_NAME)
      response = feature_base.GetFeature(name)
    except apitools_exceptions.HttpUnauthorizedError as e:
      raise exceptions.Error(
          'You are not authorized to see the status of {} '
          'Feature from project [{}]. Underlying error: {}'.format(
              self.FEATURE_DISPLAY_NAME, project_id, e))
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.Error(
          '{} Feature for project [{}] is not enabled'.format(
              self.FEATURE_DISPLAY_NAME, project_id))
    if not memberships:
      return None

    acm_status = []
    feature_state_memberships = parse_feature_state_memberships(response)
    for name in memberships:
      cluster = ConfigmanagementFeatureState(name)
      if name not in feature_state_memberships:
        acm_status.append(cluster)
        continue
      md = feature_state_memberships[name]
      fs = md.value.configmanagementFeatureState
      if fs and fs.membershipConfig and fs.membershipConfig.version:
        cluster.version = fs.membershipConfig.version
      acm_status.append(cluster)

    return acm_status


def parse_feature_state_memberships(response):
  if response.featureState is None or response.featureState.detailsByMembership is None:
    feature_state_membership_details = []
  else:
    feature_state_membership_details = response.featureState.detailsByMembership.additionalProperties
  return {
      os.path.basename(membership_detail.key): membership_detail
      for membership_detail in feature_state_membership_details
  }
