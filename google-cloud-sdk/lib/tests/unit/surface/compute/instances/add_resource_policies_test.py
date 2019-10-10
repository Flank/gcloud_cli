# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the instances add-resource-policies subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import instances_test_base as test_base


class InstancesAddResourcePoliciesTest(test_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _CheckAddRequest(self, policy_names):
    add_request = self.messages.ComputeInstancesAddResourcePoliciesRequest(
        instance=self.instance_name,
        project=self.Project(),
        zone=self.zone,
        instancesAddResourcePoliciesRequest=
        self.messages.InstancesAddResourcePoliciesRequest(
            resourcePolicies=[
                self.compute_uri + '/projects/{0}/regions/{1}/'
                'resourcePolicies/{2}'.format(
                    self.Project(), self.region, name)
                for name in policy_names]))
    self.CheckRequests(
        [(self.compute.instances,
          'AddResourcePolicies',
          add_request)],
    )

  def testAddSinglePolicy(self):
    self.Run('compute instances add-resource-policies {instance} '
             '--zone {zone} --resource-policies pol1'
             .format(instance=self.instance_name,
                     zone=self.zone))
    self._CheckAddRequest(['pol1'])

  def testAddMultiplePolicies(self):
    self.Run('compute instances add-resource-policies {instance} '
             '--zone {zone} --resource-policies pol1,pol2'
             .format(instance=self.instance_name,
                     zone=self.zone))
    self._CheckAddRequest(['pol1', 'pol2'])

  def testAddSinglePolicySelfLink(self):
    policy_name = 'pol1'
    policy_self_link = (self.compute_uri + '/projects/{0}/regions/{1}/'
                        'resourcePolicies/{2}'.format(
                            self.Project(), self.region, policy_name))
    self.Run('compute instances add-resource-policies {instance} '
             '--zone {zone} --resource-policies {policy}'
             .format(instance=self.instance_name,
                     zone=self.zone,
                     policy=policy_self_link))
    self._CheckAddRequest([policy_name])

  def testAddNoPolicies(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        'argument --resource-policies: Must be specified.'):
      self.Run('compute instances add-resource-policies {instance} '
               '--zone {zone}'
               .format(instance=self.instance_name, zone=self.zone))


if __name__ == '__main__':
  test_case.main()
