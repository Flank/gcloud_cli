# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the security policies list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from mock import patch


class InstanceGroupManagerInstanceConfigsDeleteTestBase(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  API_VERSION = 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.API_VERSION))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.API_VERSION)
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.project_uri = (
        'https://compute.googleapis.com/compute/alpha/projects/fake-project')


class InstanceGroupManagerInstanceConfigsDeleteTest(
    InstanceGroupManagerInstanceConfigsDeleteTestBase):

  def _ExpectDeletePerInstanceConfigs(self):
    request = (
        self.messages.
        ComputeInstanceGroupManagersDeletePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            instanceGroupManagersDeletePerInstanceConfigsReq=(
                self.messages.InstanceGroupManagersDeletePerInstanceConfigsReq)(
                    names=['foo', 'bas']
                ),
            project='fake-project',
            zone='us-central2-a',
        )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/zones/us-central2-a/operations/delete'),)
    self.client.instanceGroupManagers.DeletePerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectGetOperation(self, name):
    request = self.messages.ComputeZoneOperationsGetRequest(
        operation=name,
        project='fake-project',
        zone='us-central2-a',
    )
    response = self.messages.Operation(
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=self.project_uri + '/zones/us-central2-a/operations/' + name,
        targetLink=(self.project_uri +
                    '/zones/us-central2-a/instanceGroupManagers/group-1'),
    )
    self.client.zoneOperations.Get.Expect(
        request,
        response=response,
    )

  def _ExpectGetInstanceGroupManager(self):
    request = self.messages.ComputeInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        project='fake-project',
        zone='us-central2-a',
    )
    response = self.messages.InstanceGroupManager(
        name='group-1',
        zone='us-central2-a',
    )
    self.client.instanceGroupManagers.Get.Expect(request, response=response)

  def _ExpectApplyNow(self):
    request = (
        self.messages.ComputeInstanceGroupManagersApplyUpdatesToInstancesRequest
    )(
        instanceGroupManager='group-1',
        instanceGroupManagersApplyUpdatesRequest=(
            self.messages.InstanceGroupManagersApplyUpdatesRequest
        )(instances=[
            self.project_uri + '/zones/us-central2-a/instances/foo',
            self.project_uri + '/zones/us-central2-a/instances/bas',
        ],
          minimalAction=self.messages.InstanceGroupManagersApplyUpdatesRequest.
          MinimalActionValueValuesEnum.NONE,
          maximalAction=self.messages.InstanceGroupManagersApplyUpdatesRequest.
          MaximalActionValueValuesEnum.RESTART),
        project='fake-project',
        zone='us-central2-a',
    )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/zones/us-central2-a/operations/apply'),)
    self.client.instanceGroupManagers.ApplyUpdatesToInstances.Expect(
        request,
        response=response,
    )

  def testSimpleCase(self):
    self._ExpectDeletePerInstanceConfigs()
    self._ExpectGetOperation('delete')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs delete group-1
          --zone us-central2-a
          --instances foo,bas
        """)

  def testNoInstanceProvided(self):
    with self.AssertRaisesArgumentErrorMatches(
        r'argument --instances: Must be specified.'):
      self.Run("""
          compute instance-groups managed instance-configs delete group-1
            --zone us-central2-a
          """)

  def testWithApplyNow(self):
    self._ExpectDeletePerInstanceConfigs()
    self._ExpectGetOperation('delete')
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyNow()
    self._ExpectGetOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs delete group-1
          --zone us-central2-a
          --instances foo,bas
          --force-instance-update
        """)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
          compute instance-groups managed instance-configs delete group-1
            --zone us-central2-a
            --instances foo
          """)


class RegionInstanceGroupManagerInstanceConfigsDeleteTest(
    InstanceGroupManagerInstanceConfigsDeleteTestBase):

  def _ExpectDeletePerInstanceConfigs(self):
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersDeletePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagerDeleteInstanceConfigReq=(
                self.messages.RegionInstanceGroupManagerDeleteInstanceConfigReq
            )(names=['foo', 'bas']),
            project='fake-project',
            region='us-central2')
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/regions/us-central2/operations/delete'),)
    self.client.regionInstanceGroupManagers.DeletePerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectGetOperation(self, name):
    request = self.messages.ComputeRegionOperationsGetRequest(
        operation=name,
        project='fake-project',
        region='us-central2',
    )
    response = self.messages.Operation(
        status=self.messages.Operation.StatusValueValuesEnum.DONE,
        selfLink=self.project_uri + '/regions/us-central2/operations/' + name,
        targetLink=(self.project_uri +
                    '/regions/us-central2/instanceGroupManagers/group-1'),
    )
    self.client.regionOperations.Get.Expect(
        request,
        response=response,
    )

  def _ExpectListManagedInstances(self):
    request = (self.messages.
               ComputeRegionInstanceGroupManagersListManagedInstancesRequest)(
                   instanceGroupManager='group-1',
                   project='fake-project',
                   region='us-central2',
               )
    response = self.messages.RegionInstanceGroupManagersListInstancesResponse(
        managedInstances=([
            self.messages.ManagedInstance(
                instance=(
                    self.project_uri + '/zones/us-central2-a/instances/foo'),
                instanceStatus=(self.messages.ManagedInstance.
                                InstanceStatusValueValuesEnum.RUNNING),
                currentAction=(self.messages.ManagedInstance.
                               CurrentActionValueValuesEnum.NONE)),
            self.messages.ManagedInstance(
                instance=(
                    self.project_uri + '/zones/us-central2-a/instances/bas'),
                instanceStatus=(self.messages.ManagedInstance.
                                InstanceStatusValueValuesEnum.STOPPED),
                currentAction=(self.messages.ManagedInstance.
                               CurrentActionValueValuesEnum.RECREATING))
        ]))
    self.client.regionInstanceGroupManagers.ListManagedInstances.Expect(
        request,
        response=response,
    )

  def _ExpectGetInstanceGroupManager(self):
    request = self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        project='fake-project',
        region='us-central2',
    )
    response = self.messages.InstanceGroupManager(
        name='group-1',
        region='us-central2',
    )
    self.client.regionInstanceGroupManagers.Get.Expect(
        request, response=response)

  def _ExpectApplyNow(self):
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersApplyUpdatesToInstancesRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersApplyUpdatesRequest=(
                self.messages.RegionInstanceGroupManagersApplyUpdatesRequest)(
                    instances=[
                        self.project_uri + '/zones/us-central2-a/instances/foo',
                        self.project_uri + '/zones/us-central2-a/instances/bas',
                    ],
                    minimalAction=self.messages.
                    RegionInstanceGroupManagersApplyUpdatesRequest.
                    MinimalActionValueValuesEnum.NONE,
                    maximalAction=self.messages.
                    RegionInstanceGroupManagersApplyUpdatesRequest.
                    MaximalActionValueValuesEnum.RESTART),
            project='fake-project',
            region='us-central2',
        )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/regions/us-central2/operations/apply'),)
    self.client.regionInstanceGroupManagers.ApplyUpdatesToInstances.Expect(
        request,
        response=response,
    )

  def testSimpleCase(self):
    self._ExpectListManagedInstances()
    self._ExpectDeletePerInstanceConfigs()
    self._ExpectGetOperation('delete')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs delete group-1
          --region us-central2
          --instances foo,bas
        """)

  def testNoInstanceProvided(self):
    with self.AssertRaisesArgumentErrorMatches(
        r'argument --instances: Must be specified.'):
      self.Run("""
          compute instance-groups managed instance-configs delete group-1
            --region us-central2
          """)

  def testWithApplyNow(self):
    self._ExpectListManagedInstances()
    self._ExpectDeletePerInstanceConfigs()
    self._ExpectGetOperation('delete')
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyNow()
    self._ExpectGetOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs delete group-1
          --region us-central2
          --instances foo,bas
          --force-instance-update
        """)


if __name__ == '__main__':
  test_case.main()
