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
"""Tests for the instance-groups managed list-instances subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


class InstanceGroupsListInstancesZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroup(
                    self.messages, API_VERSION)))],
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            inst-3 central2-a RUNNING DELETING
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            """), normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroupManagers/group-1
          --zone central2-a
        """.format(API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            inst-3 central2-a RUNNING DELETING
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING DELETING
            inst-2 central2-a STOPPED RECREATING
            inst-1 central2-a RUNNING NONE
            """), normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(API_VERSION)))


class InstanceGroupsListInstancesRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroup(
                    self.messages, API_VERSION)))],
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            inst-3 central2-a RUNNING DELETING
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            """), normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/central2/instanceGroupManagers/group-1
          --region central2
        """.format(API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            inst-3 central2-a RUNNING DELETING
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING DELETING
            inst-2 central2-a STOPPED RECREATING
            inst-1 central2-a RUNNING NONE
            """), normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(API_VERSION)))

  def testPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='central2')],
        [self.messages.Zone(name='central2-a')],
        [self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=(
                test_resources.MakeInstancesInManagedInstanceGroup(
                    self.messages, API_VERSION)))],
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed list-instances group-1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  ACTION     LAST_ERROR
            inst-1 central2-a RUNNING NONE
            inst-2 central2-a STOPPED RECREATING
            inst-3 central2-a RUNNING DELETING
            inst-4 central2-a         CREATING   Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()

