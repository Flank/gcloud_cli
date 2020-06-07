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

"""Tests for the instance-configs create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
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


class _InstanceGroupManagerInstanceConfigsCreateBetaTestBase(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

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

  def _MakePreservedStateDiskMapEntry(self,
                                      device_name,
                                      source,
                                      mode,
                                      auto_delete_str='never'):
    mode_map = {
        'READ_ONLY': self.messages.PreservedStatePreservedDisk
                     .ModeValueValuesEnum.READ_ONLY,
        'READ_WRITE': self.messages.PreservedStatePreservedDisk
                      .ModeValueValuesEnum.READ_WRITE
    }
    auto_delete_map = {
        'never':
            self.messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum
            .NEVER,
        'on-permanent-instance-deletion':
            self.messages.PreservedStatePreservedDisk.AutoDeleteValueValuesEnum
            .ON_PERMANENT_INSTANCE_DELETION,
    }
    return self.messages.PreservedState.DisksValue.AdditionalProperty(
        key=device_name,
        value=self.messages.PreservedStatePreservedDisk(
            autoDelete=auto_delete_map[auto_delete_str],
            source=source,
            mode=mode_map[mode]))

  def _MakePreservedStateMetadataMapEntry(self, key, value):
    return self.messages.PreservedState.MetadataValue.AdditionalProperty(
        key=key, value=value)

  @staticmethod
  def _CreateTestHttpNotFoundError(status, reason, body=None, url=None):
    if body is None:
      body = ''
    response = httplib2.Response({'status': status, 'reason': reason})
    return exceptions.HttpNotFoundError(response, body, url)


class InstanceGroupManagerInstanceConfigsCreateBetaZonalTest(
    _InstanceGroupManagerInstanceConfigsCreateBetaTestBase):

  def _ExpectListPerInstanceConfigs(self,
                                    instance_name='foo',
                                    return_config=False):
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest
    )(
        filter=
        'name eq {instance}'.format(instance=instance_name),
        instanceGroupManager=u'group-1',
        maxResults=1,
        project=u'fake-project',
        zone=u'us-central2-a',
    )
    if return_config:
      items = [
          self.messages.PerInstanceConfig(
              name=instance_name,
              preservedState=self.messages.PreservedState(
                  disks=self.messages.PreservedState.DisksValue(
                      additionalProperties=[]
                  ),
                  metadata=self.messages.PreservedState.MetadataValue(
                      additionalProperties=[]
                  )
              ),
          )
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
                                      preserved_state_metadata,
                                      instance_name='foo'):
    request = (
        self.messages
        .ComputeInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            instanceGroupManagersUpdatePerInstanceConfigsReq=(
                self.messages.InstanceGroupManagersUpdatePerInstanceConfigsReq
            )(perInstanceConfigs=[
                self.messages.PerInstanceConfig(
                    name=instance_name,
                    preservedState=self.messages.PreservedState(
                        disks=self.messages.PreservedState.DisksValue(
                            additionalProperties=preserved_state_disks
                        ),
                        metadata=self.messages.PreservedState.MetadataValue(
                            additionalProperties=preserved_state_metadata
                        )
                    )
                )
            ],),
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
          .MostDisruptiveAllowedActionValueValuesEnum.REPLACE),
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
    disk_source_1 = self.project_uri + '/zones/us-central2-a/disks/foo'
    disk_source_2 = self.project_uri + '/zones/us-central2-a/disks/baz'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry('foo', disk_source_1,
                                             'READ_WRITE',
                                             'on-permanent-instance-deletion'),
        self._MakePreservedStateDiskMapEntry('baz', disk_source_2,
                                             'READ_ONLY', 'never')
    ]
    preserved_state_metadata = [
        self._MakePreservedStateMetadataMapEntry(
            key='key-BAR', value='value BAR'),
        self._MakePreservedStateMetadataMapEntry(
            key='key-foo', value='value foo')
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
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw,auto-delete=on-permanent-instance-deletion
          --stateful-disk device-name=baz,source={project_uri}/zones/us-central2-a/disks/baz,mode=ro,auto-delete=never
          --stateful-metadata "key-BAR=value BAR,key-foo=value foo"
        """.format(project_uri=self.project_uri))

  def testCreateOverrideForNonExistingDisk(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/abc123'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry('qwerty', disk_source,
                                             'READ_WRITE',
                                             'on-permanent-instance-deletion')
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=rw,auto-delete=on-permanent-instance-deletion
        """.format(project_uri=self.project_uri))

  def testCreateOverrideForNonExistingDiskWithoutModeGiven(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/abc123'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry('qwerty', disk_source,
                                             'READ_WRITE', 'never')
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk \
          device-name=qwerty,source={0}/zones/us-central2-a/disks/abc123,auto-delete=never
        """.format(self.project_uri))

  def testCreateDiskOverrideUsingOnlyDeviceName(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry(
            'foo', disk_source, 'READ_WRITE')
    ]
    self._ExpectListPerInstanceConfigs()
    self.ExpectGetInstance()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=foo
        """)

  def testCreateWithoutAnyResources(self):
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=[], preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
        """)

  def testCreateWithoutUpdateInstance(self):
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry(
            'foo',
            self.project_uri + '/zones/us-central2-a/disks/foo',
            'READ_WRITE')
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw
          --no-update-instance
        """.format(project_uri=self.project_uri))

  def testUnsuccessfulCreateForAlreadyExistingConfig(self):
    self._ExpectListPerInstanceConfigs(return_config=True)
    with self.AssertRaisesExceptionMatches(
        managed_instance_groups_utils.ResourceAlreadyExistsException,
        'already exists'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
          """)

  def testUnsuccessfulCreateForIncorrectModeValue(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'Value for [mode] must be [rw] or [ro]'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=rrr
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulCreateForInvalidAutoDeleteValue(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'Value for [auto-delete] must be [never] or '
        '[on-permanent-instance-deletion]'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=ro,auto-delete=when-not
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulCreateForSkippedDeviceName(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '[device-name] is required'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk source={project_uri}/zones/us-central2-a/disks/abc123,mode=rrr
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulCreateForSkippedSourceWhenModeIsGiven(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '[mode] can be set then and only then when [source] is given'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=qwerty,mode=ro
          """)

  def testUnsuccessfulCreateForDuplicatedDeviceName(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '`foo` is not unique in the collection'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=foo
            --stateful-disk device-name=foo
          """)

  def testUnsuccessfulCreateUsingOnlyDeviceNamesForNonExistingInstance(self):
    self._ExpectListPerInstanceConfigs()
    self.ExpectGetInstance(found=False)

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.BadArgumentException,
        ('[source] must be given while defining stateful disks in instance'
         ' configs for non existing instances')):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=foo
          """)

  def testUnsuccessfulCreateUsingOnlyDeviceNamesForNonExistingDisks(self):
    self._ExpectListPerInstanceConfigs()
    self.ExpectGetInstance()

    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.BadArgumentException,
        ('[source] must be given while defining stateful disks in instance'
         ' configs for non existing disks in given instance')):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=abc
          """)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --zone us-central2-a
            --instance foo
          """)


class InstanceGroupManagerInstanceConfigsCreateBetaRegionalTest(
    _InstanceGroupManagerInstanceConfigsCreateBetaTestBase):

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

  def _ExpectListPerInstanceConfigs(self,
                                    instance_name='foo',
                                    return_config=False):
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest
    )(
        filter=
        'name eq {instance}'.
        format(instance=instance_name),
        instanceGroupManager='group-1',
        maxResults=1,
        project='fake-project',
        region='us-central2',
    )
    if return_config:
      items = [
          self.messages.PerInstanceConfig(
              name=instance_name,
              preservedState=self.messages.PreservedState(
                  disks=self.messages.PreservedState.DisksValue(
                      additionalProperties=[]
                  ),
                  metadata=self.messages.PreservedState.MetadataValue(
                      additionalProperties=[]
                  )
              ),
          )
      ]
    else:
      items = []
    response = self.messages.RegionInstanceGroupManagersListInstanceConfigsResp(
        items=items)
    self.client.regionInstanceGroupManagers.ListPerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectUpdatePerInstanceConfigs(self,
                                      preserved_state_disks,
                                      preserved_state_metadata,
                                      instance_name='foo'):
    request = (
        self.messages
        .ComputeRegionInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagerUpdateInstanceConfigReq=(
                self.messages.RegionInstanceGroupManagerUpdateInstanceConfigReq
            )(perInstanceConfigs=[
                self.messages.PerInstanceConfig(
                    name=instance_name,
                    preservedState=self.messages.PreservedState(
                        disks=self.messages.PreservedState.DisksValue(
                            additionalProperties=preserved_state_disks
                        ),
                        metadata=self.messages.PreservedState.MetadataValue(
                            additionalProperties=preserved_state_metadata
                        )
                    )
                ),
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
                    .MostDisruptiveAllowedActionValueValuesEnum.REPLACE),
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
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry(
            'foo',
            self.project_uri + '/zones/us-central2-a/disks/foo',
            'READ_WRITE'),
        self._MakePreservedStateDiskMapEntry(
            'baz',
            self.project_uri + '/zones/us-central2-a/disks/baz',
            'READ_ONLY')
    ]
    preserved_state_metadata = [
        self._MakePreservedStateMetadataMapEntry(
            key='key-BAR', value='value BAR'),
        self._MakePreservedStateMetadataMapEntry(
            key='key-foo', value='value foo')
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
        compute instance-groups managed instance-configs create group-1
          --region us-central2
          --instance {project_uri}/zones/us-central2-a/instances/foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw
          --stateful-disk device-name=baz,source={project_uri}/zones/us-central2-a/disks/baz,mode=ro
          --stateful-metadata "key-BAR=value BAR,key-foo=value foo"
        """.format(project_uri=self.project_uri))

  def testCreateWithoutUpdateInstance(self):
    disk_source = self.project_uri + '/zones/us-central2-a/disks/foo'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry(
            'foo', disk_source, 'READ_WRITE')
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --region us-central2
          --instance {project_uri}/zones/us-central2-a/instances/foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw
          --no-update-instance
        """.format(project_uri=self.project_uri))

  def testCreateForExistingInstanceUsingOnlyInstanceName(self):
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        preserved_state_disks=[], preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectPollingOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs create group-1
          --region us-central2
          --instance foo
        """)

  def testUnsuccessfulCreateForNonExistingInstanceUsingOnlyInstanceName(self):
    self._ExpectListManagedInstances()
    with self.AssertRaisesExceptionMatches(
        managed_instance_groups_utils.ResourceCannotBeResolvedException,
        'Instance name abc cannot be resolved'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --region us-central2
            --instance abc
          """)

  def testUnsuccessfulCreateForAlreadyExistingConfig(self):
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs(return_config=True)
    with self.AssertRaisesExceptionMatches(
        managed_instance_groups_utils.ResourceAlreadyExistsException,
        'already exists'):
      self.Run("""
          compute instance-groups managed instance-configs create group-1
            --region us-central2
            --instance foo
            --stateful-metadata "key-BAR=value BAR,key-foo=value foo"
          """.format(project_uri=self.project_uri))


class _InstanceGroupManagerInstanceConfigsCreateAlphaTestBase(
    _InstanceGroupManagerInstanceConfigsCreateBetaTestBase):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupManagerInstanceConfigsCreateAlphaZonalTest(
    _InstanceGroupManagerInstanceConfigsCreateAlphaTestBase,
    InstanceGroupManagerInstanceConfigsCreateBetaZonalTest):
  pass


class _InstanceGroupManagerInstanceConfigsCreateAlphaRegionalTest(
    _InstanceGroupManagerInstanceConfigsCreateAlphaTestBase,
    InstanceGroupManagerInstanceConfigsCreateBetaRegionalTest):
  pass


if __name__ == '__main__':
  test_case.main()
