# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instance-groups unmanaged add-instances subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base

API_VERSION = 'v1'


class UnmanagedInstanceGroupsAddInstancesTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)

  def testAddInstancesToInstanceGroup(self):
    self.Run("""
        compute instance-groups unmanaged add-instances group-1
          --instances inst-1,inst-2,inst-3
          --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'AddInstances',
          self.messages.ComputeInstanceGroupsAddInstancesRequest(
              instanceGroup='group-1',
              instanceGroupsAddInstancesRequest=(
                  self.messages.InstanceGroupsAddInstancesRequest(instances=[
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-1'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-2'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-3'.format(
                                        API_VERSION)))])),
              project='my-project',
              zone='central2-a'))])

  def testAddInstancesToInstanceGroupByUri(self):
    self.Run("""
        compute instance-groups unmanaged add-instances
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroups/group-1
          --instances
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1,https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2,https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
        """.format(API_VERSION))

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'AddInstances',
          self.messages.ComputeInstanceGroupsAddInstancesRequest(
              instanceGroup='group-1',
              instanceGroupsAddInstancesRequest=(
                  self.messages.InstanceGroupsAddInstancesRequest(instances=[
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-1'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-2'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-3'.format(
                                        API_VERSION)))])),
              project='my-project',
              zone='central2-a'))])

  def testAddInstancesToInstanceGroupWithZonePrompt(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('3\n')
    self.Run("""
        compute instance-groups unmanaged add-instances group-1
          --instances inst-1,inst-2,inst-3
        """)

    self.CheckRequests(
        self.zones_list_request,
        [(self.compute.instanceGroups,
          'AddInstances',
          self.messages.ComputeInstanceGroupsAddInstancesRequest(
              instanceGroup='group-1',
              instanceGroupsAddInstancesRequest=(
                  self.messages.InstanceGroupsAddInstancesRequest(instances=[
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-1'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-2'.format(
                                        API_VERSION))),
                      self.messages.InstanceReference(
                          instance=('https://www.googleapis.com/compute/'
                                    '{0}/projects/my-project/'
                                    'zones/central2-a/instances/inst-3'.format(
                                        API_VERSION)))])),
              project='my-project',
              zone='central2-a'))])

  def testAddInstancesToInstanceGroupInconsistentZones(self):
    with self.AssertRaisesToolExceptionRegexp(
        'The zone of instance must match the instance group zone. '
        'Following instances has invalid zone: '
        'https://www.googleapis.com/compute/{0}/projects/my-project/zones/'
        'central1-a/instances/inst-2'.format(API_VERSION)):
      self.Run("""
          compute instance-groups unmanaged add-instances
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroups/group-1
            --instances
              https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1,https://www.googleapis.com/compute/{0}/projects/my-project/zones/central1-a/instances/inst-2,https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
          """.format(API_VERSION))


if __name__ == '__main__':
  test_case.main()
