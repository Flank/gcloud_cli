# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.compute.instance_groups.managed import stateful_policy_utils as policy_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed.instance_configs import utils as config_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_groups import test_resources

import mock


class InstanceGroupsListInstancesZonalTest(test_base.BaseTest):

  API_VERSION = 'v1'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.make_requests.side_effect = iter([
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, self.API_VERSION),
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            """),
        normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroupManagers/group-1
          --zone central2-a
        """.format(self.API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            """),
        normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(self.API_VERSION)))


class InstanceGroupsListInstancesRegionalTest(test_base.BaseTest):

  API_VERSION = 'v1'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.make_requests.side_effect = iter([
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, self.API_VERSION),
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            """),
        normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://compute.googleapis.com/compute/{0}/projects/my-project/regions/central2/instanceGroupManagers/group-1
          --region central2
        """.format(self.API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            """),
        normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(self.API_VERSION)))

  def testPrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='central2')],
        [self.messages.Zone(name='central2-a')],
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, self.API_VERSION),
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed list-instances group-1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   template-2        yyy
            inst-4 central2-a                      CREATING   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)


class InstanceGroupsListInstancesBetaZonalTest(
    InstanceGroupsListInstancesZonalTest):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.endpoint_uri = (
        'https://compute.googleapis.com/compute/{api_version}/'.format(
            api_version=self.API_VERSION))
    self.project_uri = '{endpoint_uri}projects/fake-project'.format(
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
    source = self.project_uri + '/zones/central2-a/disks/baz'
    for managed_instance in managed_instances[2:]:
      managed_instance.preservedStateFromConfig = (
          config_utils.MakePreservedState(self.messages, [
              config_utils.MakePreservedStateDiskMapEntry(
                  self.messages, 'disk-a', source, 'ro'),
          ]))

    self.make_requests.side_effect = iter([
        managed_instances,
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG   template-2        yyy
            inst-4 central2-a                      CREATING   POLICY,CONFIG   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            """),
        normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instanceGroupManagers/group-1
          --zone central2-a
        """.format(self.API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG   template-2        yyy
            inst-4 central2-a                      CREATING   POLICY,CONFIG   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                      CREATING   POLICY,CONFIG   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG   template-2        yyy
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            """),
        normalize_space=True)


class InstanceGroupsListInstancesBetaRegionalTest(
    InstanceGroupsListInstancesRegionalTest):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.SelectApi(self.API_VERSION)
    self.endpoint_uri = (
        'https://compute.googleapis.com/compute/{api_version}/'.format(
            api_version=self.API_VERSION))
    self.project_uri = '{endpoint_uri}projects/fake-project'.format(
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
    source = self.project_uri + '/zones/central2-a/disks/baz'
    for managed_instance in managed_instances[2:]:
      managed_instance.preservedStateFromConfig = (
          config_utils.MakePreservedState(self.messages, [
              config_utils.MakePreservedStateDiskMapEntry(
                  self.messages, 'disk-a', source, 'ro'),
          ]))

    self.make_requests.side_effect = iter([
        managed_instances,
    ])

  def testListInstances(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG  template-2        yyy
            inst-4 central2-a                      CREATING   POLICY,CONFIG  template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesWithLimit(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --limit 2
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            """),
        normalize_space=True)

  def testListInstancesByUri(self):
    self.Run("""
        compute instance-groups managed list-instances
          https://compute.googleapis.com/compute/{0}/projects/my-project/regions/central2/instanceGroupManagers/group-1
          --region central2
        """.format(self.API_VERSION))
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG  template-2        yyy
            inst-4 central2-a                      CREATING   POLICY,CONFIG  template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesBySorted(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --sort-by ~NAME
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-4 central2-a                      CREATING   POLICY,CONFIG   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            inst-3 central2-a RUNNING TIMEOUT      DELETING   POLICY,CONFIG   template-2        yyy
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING POLICY          template-1
            inst-1 central2-a RUNNING HEALTHY      NONE       POLICY          template-1        xxx
            """),
        normalize_space=True)

  def testListInstancesUriOutput(self):
    self.Run("""
        compute instance-groups managed list-instances group-1
          --region central2
          --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-1
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-2
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-3
            https://compute.googleapis.com/compute/{0}/projects/my-project/zones/central2-a/instances/inst-4
            """.format(self.API_VERSION)))

  def testPrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='central2')],
        [self.messages.Zone(name='central2-a')],
        test_resources.MakeInstancesInManagedInstanceGroup(
            self.messages, self.API_VERSION),
    ])
    self.WriteInput('2\n')
    self.Run("""
        compute instance-groups managed list-instances group-1
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION     PRESERVED_STATE INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE                       template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING                 template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING                   template-2        yyy
            inst-4 central2-a                      CREATING                   template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)


class InstanceGroupsListInstancesAlphaZonalTest(
    InstanceGroupsListInstancesBetaZonalTest):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupsManagedListInstancesPaginationTest(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  API_VERSION = 'v1'

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('compute', self.API_VERSION)
    batch_make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.batch_helper.MakeRequests',
        autospec=True)
    self.addCleanup(batch_make_requests_patcher.stop)
    self.batch_make_requests = batch_make_requests_patcher.start()

  def testListInstancesWithPagination(self):
    items = test_resources.MakeInstancesInManagedInstanceGroup(
        self.messages, self.API_VERSION)

    self.batch_make_requests.side_effect = iter([
        [[self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=[items[0], items[1]], nextPageToken='token-1')],
         []],
        [[self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=[items[2], items[3]],)],
         []]
    ])

    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION      INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE        template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING  template-1
            inst-3 central2-a RUNNING TIMEOUT      DELETING    template-2        yyy
            inst-4 central2-a                      CREATING    template-3                     Error CONDITION_NOT_MET: True is not False, Error QUOTA_EXCEEDED: Limit is 5
            """),
        normalize_space=True)

  def testListInstancesWithoutPagination(self):
    items = test_resources.MakeInstancesInManagedInstanceGroup(
        self.messages, self.API_VERSION)

    self.batch_make_requests.side_effect = iter([
        [[self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=[items[0], items[1]],)],
         []],
        [[self.messages.InstanceGroupManagersListManagedInstancesResponse(
            managedInstances=[items[2], items[3]],)],
         []]
    ])

    self.Run("""
        compute instance-groups managed list-instances group-1
          --zone central2-a
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   ZONE       STATUS  HEALTH_STATE ACTION      INSTANCE_TEMPLATE VERSION_NAME LAST_ERROR
            inst-1 central2-a RUNNING HEALTHY      NONE        template-1        xxx
            inst-2 central2-a STOPPED UNHEALTHY    RECREATING  template-1
            """),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
