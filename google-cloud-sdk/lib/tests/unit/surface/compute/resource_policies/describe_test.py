# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the resource policies describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class DescribeBetaTest(resource_policies_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDescribe_Simple(self):
    policy = self.resource_policies[1]
    policy_self_link = (self.compute_uri + 'projects/{0}/regions/{1}/'
                        'resourcePolicies/{2}'.format(
                            self.Project(), self.region, 'pol2'))

    policy.kind = 'compute#resourcePolicy'
    policy.selfLink = policy_self_link

    self.make_requests.side_effect = [[policy]]
    self.Run('compute resource-policies describe pol2 '
             '--region {}'.format(self.region))

    self.CheckRequests(
        [(self.compute.resourcePolicies,
          'Get',
          self.messages.ComputeResourcePoliciesGetRequest(
              project=self.Project(),
              region=self.region,
              resourcePolicy='pol2'))])

    self.AssertOutputEquals(
        """\
creationTimestamp: '2017-10-27T17:54:10.636-07:00'
description: desc
kind: compute#resourcePolicy
name: pol2
region: {region}
selfLink: {uri}
""".format(region=self.region, uri=policy_self_link),
        normalize_space=True)


class DescribeAlphsTest(resource_policies_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDescribe_Simple(self):
    policy = self.resource_policies[1]
    policy_self_link = (
        self.compute_uri + 'projects/{0}/regions/{1}/'
        'resourcePolicies/{2}'.format(self.Project(), self.region, 'pol2'))

    policy.kind = 'compute#resourcePolicy'
    policy.selfLink = policy_self_link

    self.make_requests.side_effect = [[policy]]
    self.Run('compute resource-policies describe pol2 '
             '--region {}'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Get',
                         self.messages.ComputeResourcePoliciesGetRequest(
                             project=self.Project(),
                             region=self.region,
                             resourcePolicy='pol2'))])

    self.AssertOutputEquals(
        """\
creationTimestamp: '2017-10-27T17:54:10.636-07:00'
description: desc
kind: compute#resourcePolicy
name: pol2
region: {region}
selfLink: {uri}
vmMaintenancePolicy:
  maintenanceWindow:
    dailyMaintenanceWindow:
      daysInCycle: 3
      startTime: 08:00
""".format(region=self.region, uri=policy_self_link),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
