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
"""Tests for the instance-groups managed describe-instance subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.instance_groups.managed import stateful_policy_utils as policy_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed.instance_configs import utils as config_utils
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class InstanceGroupsDescribeInstanceAlphaZonalTest(test_base.BaseTest):

  API_VERSION = 'alpha'

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.endpoint_uri = 'https://compute.googleapis.com/compute/alpha/'
    self.project_uri = '{endpoint_uri}projects/my-project'.format(
        endpoint_uri=self.endpoint_uri)

    managed_instances = test_resources.MakeInstancesInManagedInstanceGroup(
        self.messages, self.API_VERSION)

    # Add stateful policy to all 4 managed instances
    for i in range(len(managed_instances)):
      managed_instances[i].preservedStateFromPolicy = (
          policy_utils.MakePreservedState(self.messages, [
              policy_utils.MakePreservedStateDisksMapEntry(
                  self.messages, {
                      'device_name': 'disk-a',
                      'auto_delete': 'never'
                  }),
          ]))

    # Add PICs to the last two managed instances
    source = self.project_uri + '/zones/us-central2-a/disks/baz'
    for managed_instance in managed_instances[2:]:
      managed_instance.preservedStateFromConfig = (
          config_utils.MakePreservedState(self.messages, [
              config_utils.MakePreservedStateDiskMapEntry(
                  self.messages, 'disk-a', source, 'ro'),
          ]))

    self.make_requests.side_effect = iter([
        [
            self.messages.InstanceGroupManagersListManagedInstancesResponse(
                managedInstances=managed_instances),
        ],
    ])

  def testDescribeInstance(self):
    self.Run("""
        compute instance-groups managed describe-instance group-1
          --instance inst-1
          --zone central2-a
        """)
    instance_uri = ('{project_uri}/zones/'
                    'central2-a/instances/{instance_name}'.format(
                        project_uri=self.project_uri, instance_name='inst-1'))
    self.AssertOutputMatches(
        """\
        .*
        instance: {instance_uri}
        .*
        instanceTemplate: template-1
        .*
        """.format(instance_uri=instance_uri),
        normalize_space=True)

  def testDescribeInvalidInstanceThrowsError(self):
    with self.assertRaisesRegex(ValueError, 'Unknown instance with name.*'):
      self.Run("""
          compute instance-groups managed describe-instance group-1
            --instance non-existant
            --zone central2-a
          """)


class InstanceGroupsDescribeInstanceRegionalTest(
    InstanceGroupsDescribeInstanceAlphaZonalTest):

  API_VERSION = 'alpha'

  def testDescribeInstance(self):
    self.Run("""
        compute instance-groups managed describe-instance group-1
          --instance inst-1
          --region central2
        """)
    instance_uri = ('{project_uri}/zones/'
                    'central2-a/instances/{instance_name}'.format(
                        project_uri=self.project_uri, instance_name='inst-1'))
    self.AssertOutputMatches(
        """\
        .*
        instance: {instance_uri}
        .*
        instanceTemplate: template-1
        .*
        """.format(instance_uri=instance_uri),
        normalize_space=True)

  def testDescribeInvalidInstanceThrowsError(self):
    with self.assertRaisesRegex(ValueError, 'Unknown instance with name.*'):
      self.Run("""
          compute instance-groups managed describe-instance group-1
            --instance non-existant
            --region central2
          """)


if __name__ == '__main__':
  test_case.main()
