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

"""Tests for the instance-configs update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed.instance_configs import utils as config_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2
from mock import patch


class _InstanceGroupManagerInstanceConfigsUpdateBetaTestBase(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
    sdk_test_base.WithLogCapture):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.client = mock.Client(
        core_apis.GetClientClass('compute', self.API_VERSION))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.API_VERSION)
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.endpoint_uri = (
        'https://compute.googleapis.com/compute/{api_version}/'.format(
            api_version=self.API_VERSION))
    self.project_uri = '{endpoint_uri}projects/fake-project'.format(
        endpoint_uri=self.endpoint_uri)

  def ExpectGetInstance(self, found=True):
    request = self.messages.ComputeInstancesGetRequest(
        instance='foo',
        project='fake-project',
        zone='us-central2-a',
    )
    if found:
      response = self.messages.Instance(
          name='foo',
          selfLink=(self.project_uri + '/zones/us-central2-a/instances/foo'),
          disks=[
              self.messages.AttachedDisk(
                  deviceName='foo',
                  source=(self.project_uri + '/zones/us-central2-a/disks/foo'),
                  mode=self.messages.AttachedDisk.ModeValueValuesEnum(
                      'READ_WRITE'),
              ),
              self.messages.AttachedDisk(
                  deviceName='bar',
                  source=(self.project_uri + '/zones/us-central2-a/disks/bar'),
                  mode=self.messages.AttachedDisk.ModeValueValuesEnum(
                      'READ_WRITE'),
              ),
              self.messages.AttachedDisk(
                  deviceName='baz',
                  source=(self.project_uri + '/zones/us-central2-a/disks/baz'),
                  mode=self.messages.AttachedDisk.ModeValueValuesEnum(
                      'READ_ONLY'),
              )
          ],
      )
      exception = None
    else:
      response = None
      exception = self._CreateTestHttpNotFoundError(404, 'Not Found')
    self.client.instances.Get.Expect(
        request, response=response, exception=exception)

  @staticmethod
  def _CreateTestHttpNotFoundError(status, reason, body=None, url=None):
    if body is None:
      body = ''
    response = httplib2.Response({'status': status, 'reason': reason})
    return exceptions.HttpNotFoundError(response, body, url)


class InstanceGroupManagerInstanceConfigsUpdateBetaZonalTest(
    _InstanceGroupManagerInstanceConfigsUpdateBetaTestBase):

  def SetUp(self):
    self._preserved_state_disk_1 = config_utils.MakePreservedStateDiskMapEntry(
        self.messages, 'foo',
        (self.project_uri + '/zones/us-central2-a/disks/foo'), 'READ_WRITE')
    self._preserved_state_disk_2 = config_utils.MakePreservedStateDiskMapEntry(
        self.messages, 'baz',
        (self.project_uri + '/zones/us-central2-a/disks/baz'), 'READ_ONLY')

    self.preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='value BAR'),
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-foo', value='value foo'),
    ]

  def _ExpectListPerInstanceConfigs(self, return_config=True):
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest
    )(
        filter='name eq foo'.
        format(project_uri=self.project_uri),
        instanceGroupManager='group-1',
        maxResults=1,
        project='fake-project',
        zone='us-central2-a',
    )
    if return_config:
      preserved_state_disks = [
          config_utils.MakePreservedStateDiskMapEntry(
              self.messages, 'foo',
              (self.project_uri + '/zones/us-central2-a/disks/foo'),
              'READ_WRITE'),
          config_utils.MakePreservedStateDiskMapEntry(
              self.messages, 'baz',
              (self.project_uri + '/zones/us-central2-a/disks/baz'),
              'READ_ONLY'),
      ]
      items = [
          config_utils.MakePerInstanceConfig(self.messages, 'foo',
                                             preserved_state_disks,
                                             self.preserved_state_metadata)
      ]
    else:
      items = []
    response = self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
        items=items)
    self.client.instanceGroupManagers.ListPerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectUpdatePerInstanceConfigs(self,
                                      preserved_state_disks,
                                      preserved_state_metadata):
    request = (
        self.messages
        .ComputeInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            instanceGroupManagersUpdatePerInstanceConfigsReq=(
                self.messages.InstanceGroupManagersUpdatePerInstanceConfigsReq)(
                    perInstanceConfigs=[
                        config_utils.MakePerInstanceConfig(
                            self.messages, 'foo', preserved_state_disks,
                            preserved_state_metadata),
                    ]),
            project='fake-project',
            zone='us-central2-a',
        )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/zones/us-central2-a/operations/foo'),)
    self.client.instanceGroupManagers.UpdatePerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectGetOperation(self, name='foo'):
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

  def _ExpectWaitOperation(self, name='foo'):
    request = self.messages.ComputeZoneOperationsWaitRequest(
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
    self.client.zoneOperations.Wait.Expect(
        request,
        response=response,
    )

  def _ExpectPollingOperation(self, name='foo'):
    self._ExpectWaitOperation(name)

  def _ExpectGetInstanceGroupManager(self):
    request = self.messages.ComputeInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        project='fake-project',
        zone='us-central2-a',
    )
    response = self.messages.InstanceGroupManager(name='group-1')
    self.client.instanceGroupManagers.Get.Expect(request, response=response)

  def _ExpectApplyUpdatesToInstances(self):
    request = (
        self.messages.ComputeInstanceGroupManagersApplyUpdatesToInstancesRequest
    )(
        instanceGroupManager='group-1',
        instanceGroupManagersApplyUpdatesRequest=(
            self.messages.InstanceGroupManagersApplyUpdatesRequest
        )(instances=[
            self.project_uri + '/zones/us-central2-a/instances/foo',
        ],
          minimalAction=self.messages.InstanceGroupManagersApplyUpdatesRequest
          .MinimalActionValueValuesEnum.NONE,
          mostDisruptiveAllowedAction=self.messages
          .InstanceGroupManagersApplyUpdatesRequest
          .MostDisruptiveAllowedActionValueValuesEnum.RESTART),
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
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo-2'
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'foo', disk_source, 'READ_ONLY',
            'on-permanent-instance-deletion'),
    ]
    preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='new value'),
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo-2,mode=ro,auto-delete=on-permanent-instance-deletion
          --remove-stateful-disks baz
          --stateful-metadata "key-BAR=new value"
          --remove-stateful-metadata key-foo
        """.format(project_uri=self.project_uri))

  def testUpdateAddNonExistingDisk(self):
    preserved_state_disks = [
        self._preserved_state_disk_1, self._preserved_state_disk_2,
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'qwerty',
            (self.project_uri + '/zones/us-central2-a/disks/abc123'),
            'READ_WRITE', 'on-permanent-instance-deletion')
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=self.preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=rw,auto-delete=on-permanent-instance-deletion
        """.format(project_uri=self.project_uri))

  def testUpdateAddDiskOverrideUsingOnlyDeviceName(self):
    preserved_state_disks = [
        self._preserved_state_disk_1, self._preserved_state_disk_2,
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'bar',
            (self.project_uri + '/zones/us-central2-a/disks/bar'), 'READ_WRITE')
    ]
    self._ExpectListPerInstanceConfigs()
    self.ExpectGetInstance()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=self.preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=bar
        """)

  def testUpdateRemoveAllDiskAndMetadataOverrides(self):
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=[], preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --remove-stateful-disks foo,baz
          --remove-stateful-metadata key-BAR,key-foo
        """)

  def testUpdateWithoutInstanceUpdate(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo'
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(self.messages, 'foo',
                                                    disk_source, 'READ_WRITE'),
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=self.preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --remove-stateful-disks baz
          --no-update-instance
        """)

  def testUnsuccessfulUpdateForNonExistingConfig(self):
    self._ExpectListPerInstanceConfigs(return_config=False)
    with self.AssertRaisesExceptionMatches(
        managed_instance_groups_utils.ResourceNotFoundException,
        'does not exist'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/abc123,mode=ro
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulUpdateForTheSameDeviceNameToUpdateAndRemove(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'cannot be updated and removed in one command call'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=ro
            --remove-stateful-disks qwerty
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulUpdateForTheSameMetadataKeyToUpdateAndRemove(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'cannot be updated and removed in one command call'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --stateful-metadata key-abc=value
            --remove-stateful-metadata key-abc
          """)

  def testUnsuccessfulUpdateForRemoveNonExistingStatefulMetadataKey(self):
    self._ExpectListPerInstanceConfigs()
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'stateful metadata key to remove `non-existing-key` does not exist in'
        ' the given instance config'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --remove-stateful-metadata non-existing-key
          """)

  def testUnsuccessfulUpdateForPassingOnlyDeviceNameWithoutParameters(self):
    self._ExpectListPerInstanceConfigs()
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        ('[source] or [mode] is required when updating'
         ' [device-name] already existing in instance config')):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=foo
          """)

  def testUnsuccessfulUpdateForRemoveNonExistingStatefulDisk(self):
    self._ExpectListPerInstanceConfigs()
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'The following are invalid stateful disks: `nonexistent`'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --remove-stateful-disks nonexistent
          """)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
          """)


class InstanceGroupManagerInstanceConfigsUpdateBetaRegionalTest(
    _InstanceGroupManagerInstanceConfigsUpdateBetaTestBase):

  def SetUp(self):
    self.preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='value BAR'),
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-foo', value='value foo'),
    ]

  def _ExpectListManagedInstances(self):
    request = (self.messages.
               ComputeRegionInstanceGroupManagersListManagedInstancesRequest)(
                   instanceGroupManager='group-1',
                   maxResults=500,
                   project='fake-project',
                   region='us-central2',
               )
    managed_instances = [
        self.messages.ManagedInstance(
            instance='{project_uri}/zones/us-central2-a/instances/foo'.format(
                project_uri=self.project_uri),),
    ]
    response = self.messages.RegionInstanceGroupManagersListInstancesResponse(
        managedInstances=managed_instances)
    self.client.regionInstanceGroupManagers.ListManagedInstances.Expect(
        request,
        response=response,
    )

  def _ExpectListPerInstanceConfigs(self):
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest
    )(
        filter='name eq foo'.
        format(project_uri=self.project_uri),
        instanceGroupManager='group-1',
        maxResults=1,
        project='fake-project',
        region='us-central2',
    )
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'foo',
            (self.project_uri + '/zones/us-central2-a/disks/foo'),
            'READ_WRITE'),
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'baz',
            (self.project_uri + '/zones/us-central2-a/disks/baz'), 'READ_ONLY'),
    ]
    items = [
        config_utils.MakePerInstanceConfig(self.messages, 'foo',
                                           preserved_state_disks,
                                           self.preserved_state_metadata),
    ]
    response = self.messages.RegionInstanceGroupManagersListInstanceConfigsResp(
        items=items)
    self.client.regionInstanceGroupManagers.ListPerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectUpdatePerInstanceConfigs(self,
                                      preserved_state_disks,
                                      preserved_state_metadata):
    request = (
        self.messages
        .ComputeRegionInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagerUpdateInstanceConfigReq=(
                self.messages.RegionInstanceGroupManagerUpdateInstanceConfigReq
            )(perInstanceConfigs=[
                config_utils.MakePerInstanceConfig(self.messages, 'foo',
                                                   preserved_state_disks,
                                                   preserved_state_metadata),
            ],),
            project='fake-project',
            region='us-central2',
        )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/regions/us-central2/operations/foo'),)
    self.client.regionInstanceGroupManagers.UpdatePerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectGetOperation(self, name='foo'):
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

  def _ExpectWaitOperation(self, name='foo'):
    request = self.messages.ComputeRegionOperationsWaitRequest(
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
    self.client.regionOperations.Wait.Expect(
        request,
        response=response,
    )

  def _ExpectPollingOperation(self, name='foo'):
    self._ExpectWaitOperation(name)

  def _ExpectGetInstanceGroupManager(self):
    request = self.messages.ComputeRegionInstanceGroupManagersGetRequest(
        instanceGroupManager='group-1',
        project='fake-project',
        region='us-central2',
    )
    response = self.messages.InstanceGroupManager(name='group-1')
    self.client.regionInstanceGroupManagers.Get.Expect(
        request, response=response)

  def _ExpectApplyUpdatesToInstances(self):
    request = (
        self.messages
        .ComputeRegionInstanceGroupManagersApplyUpdatesToInstancesRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersApplyUpdatesRequest=(
                self.messages.RegionInstanceGroupManagersApplyUpdatesRequest)(
                    instances=[
                        self.project_uri + '/zones/us-central2-a/instances/foo',
                    ],
                    minimalAction=self.messages
                    .RegionInstanceGroupManagersApplyUpdatesRequest
                    .MinimalActionValueValuesEnum.NONE,
                    mostDisruptiveAllowedAction=self.messages
                    .RegionInstanceGroupManagersApplyUpdatesRequest
                    .MostDisruptiveAllowedActionValueValuesEnum.RESTART),
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
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo-2'
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'foo', disk_source, 'READ_ONLY',
            'on-permanent-instance-deletion'),
    ]
    preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='new value'),
    ]
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --region us-central2
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo-2,mode=ro,auto-delete=on-permanent-instance-deletion
          --remove-stateful-disks baz
          --stateful-metadata "key-BAR=new value"
          --remove-stateful-metadata key-foo
        """.format(project_uri=self.project_uri))

  def testUpdateWithoutInstanceUpdate(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo'
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(self.messages, 'foo',
                                                    disk_source, 'READ_WRITE'),
    ]
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=self.preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --region us-central2
          --instance foo
          --remove-stateful-disks baz
          --no-update-instance
        """)


class _InstanceGroupManagerInstanceConfigsUpdateAlphaTestBase(
    _InstanceGroupManagerInstanceConfigsUpdateBetaTestBase):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupManagerInstanceConfigsUpdateAlphaZonalTest(
    _InstanceGroupManagerInstanceConfigsUpdateAlphaTestBase,
    InstanceGroupManagerInstanceConfigsUpdateBetaZonalTest):

  def SetUp(self):
    self._preserved_state_disk_1 = config_utils.MakePreservedStateDiskMapEntry(
        self.messages, 'foo',
        (self.project_uri + '/zones/us-central2-a/disks/foo'), 'READ_WRITE')
    self._preserved_state_disk_2 = config_utils.MakePreservedStateDiskMapEntry(
        self.messages, 'baz',
        (self.project_uri + '/zones/us-central2-a/disks/baz'), 'READ_ONLY')

    self.preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='value BAR'),
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-foo', value='value foo'),
    ]

  def testSimpleCase(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo-2'
    preserved_state_disks = [
        config_utils.MakePreservedStateDiskMapEntry(
            self.messages, 'foo', disk_source, 'READ_ONLY',
            'on-permanent-instance-deletion'),
    ]
    preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='new value'),
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --update-stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo-2,mode=ro,auto-delete=on-permanent-instance-deletion
          --remove-stateful-disks baz
          --update-stateful-metadata "key-BAR=new value"
          --remove-stateful-metadata key-foo
        """.format(project_uri=self.project_uri))

    self.AssertLogContains('The --update-stateful-disk option is deprecated; '
                           'use --stateful-disk instead.')

    self.AssertLogContains(
        'The --update-stateful-metadata option is deprecated; '
        'use --stateful-metadata instead.')


class InstanceGroupManagerInstanceConfigsUpdateAlphaRegionalTest(
    _InstanceGroupManagerInstanceConfigsUpdateAlphaTestBase,
    InstanceGroupManagerInstanceConfigsUpdateBetaRegionalTest):

  def SetUp(self):
    self.preserved_state_metadata = [
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-BAR', value='value BAR'),
        config_utils.MakePreservedStateMetadataMapEntry(
            self.messages, key='key-foo', value='value foo'),
    ]


if __name__ == '__main__':
  test_case.main()
