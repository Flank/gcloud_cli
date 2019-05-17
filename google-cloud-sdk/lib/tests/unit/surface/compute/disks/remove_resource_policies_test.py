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
"""Tests for the disks remove-resource-policies subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import disks_test_base as test_base


class DisksRemoveResourcePoliciesTest(test_base.TestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _CheckRemoveRequest(self, policy_names):
    request_cls = self.messages.ComputeDisksRemoveResourcePoliciesRequest
    remove_request = request_cls(
        disk=self.disk_name,
        project=self.Project(),
        zone=self.zone,
        disksRemoveResourcePoliciesRequest=
        self.messages.DisksRemoveResourcePoliciesRequest(
            resourcePolicies=[
                self.compute_uri + '/projects/{0}/regions/{1}/'
                'resourcePolicies/{2}'.format(
                    self.Project(), self.region, name)
                for name in policy_names]))
    self.CheckRequests(
        [(self.compute.disks, 'RemoveResourcePolicies', remove_request)],)

  def _CheckRegionalRemoveRequest(self, policy_names):
    request_cls = self.messages.ComputeRegionDisksRemoveResourcePoliciesRequest
    remove_request = request_cls(
        disk=self.disk_name,
        project=self.Project(),
        region=self.region,
        regionDisksRemoveResourcePoliciesRequest=
        self.messages.RegionDisksRemoveResourcePoliciesRequest(
            resourcePolicies=[
                self.compute_uri + '/projects/{0}/regions/{1}/'
                'resourcePolicies/{2}'.format(
                    self.Project(), self.region, name)
                for name in policy_names]))
    self.CheckRequests(
        [(self.compute.regionDisks, 'RemoveResourcePolicies', remove_request)],)

  def testRemoveSinglePolicy(self):
    self.Run('compute disks remove-resource-policies {disk} '
             '--zone {zone} --resource-policies pol1'
             .format(disk=self.disk_name,
                     zone=self.zone))
    self._CheckRemoveRequest(['pol1'])

  def testRemoveMultiplePolicies(self):
    self.Run('compute disks remove-resource-policies {disk} '
             '--zone {zone} --resource-policies pol1,pol2'
             .format(disk=self.disk_name,
                     zone=self.zone))
    self._CheckRemoveRequest(['pol1', 'pol2'])

  def testRemoveSinglePolicySelfLink(self):
    policy_name = 'pol1'
    policy_self_link = (self.compute_uri + '/projects/{0}/regions/{1}/'
                        'resourcePolicies/{2}'.format(
                            self.Project(), self.region, policy_name))
    self.Run('compute disks remove-resource-policies {disk} '
             '--zone {zone} --resource-policies {policy}'
             .format(disk=self.disk_name,
                     zone=self.zone,
                     policy=policy_self_link))
    self._CheckRemoveRequest([policy_name])

  def testRemoveNoPolicies(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        'argument --resource-policies: Must be specified.'):
      self.Run('compute disks remove-resource-policies {disk} '
               '--zone {zone}'
               .format(disk=self.disk_name, zone=self.zone))

  def testRemovePolicyFromRegionalDisk(self):
    self.Run('compute disks remove-resource-policies {disk} '
             '--region {region} --resource-policies pol1'
             .format(disk=self.disk_name,
                     region=self.region))
    self._CheckRegionalRemoveRequest(['pol1'])


class DisksRemoveResourcePoliciesAlphaTest(DisksRemoveResourcePoliciesTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
