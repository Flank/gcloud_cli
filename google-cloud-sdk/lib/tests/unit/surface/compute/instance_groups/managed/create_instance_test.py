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
"""Tests for the instance-groups managed create-instance command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from mock import patch


class _InstanceGroupManagerCreateInstanceTestBase(sdk_test_base.WithFakeAuth,
                                                  cli_test_base.CliTestBase):

  API_VERSION = 'v1'

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

  def _MakePreservedStateDiskMapEntry(self,
                                      device_name,
                                      source,
                                      mode,
                                      auto_delete_str='never'):
    mode_map = {
        'READ_ONLY':
            self.messages.PreservedStatePreservedDisk.ModeValueValuesEnum
            .READ_ONLY,
        'READ_WRITE':
            self.messages.PreservedStatePreservedDisk.ModeValueValuesEnum
            .READ_WRITE
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


class InstanceGroupManagerCreateInstanceGAZonalTest(
    _InstanceGroupManagerCreateInstanceTestBase):

  API_VERSION = 'v1'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectCreateInstance(self,
                            preserved_state_disks,
                            preserved_state_metadata,
                            instance_name='foo'):
    request = (
        self.messages.ComputeInstanceGroupManagersCreateInstancesRequest
    )(instanceGroupManager='group-1',
      instanceGroupManagersCreateInstancesRequest=(
          self.messages.InstanceGroupManagersCreateInstancesRequest)(instances=[
              self.messages.PerInstanceConfig(
                  name=instance_name,
                  preservedState=self.messages.PreservedState(
                      disks=self.messages.PreservedState.DisksValue(
                          additionalProperties=preserved_state_disks),
                      metadata=self.messages.PreservedState.MetadataValue(
                          additionalProperties=preserved_state_metadata)))
          ]),
      project='fake-project',
      zone='us-central2-a')
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/zones/us-central2-a/operations/foo'),)
    self.client.instanceGroupManagers.CreateInstances.Expect(
        request,
        response=response,
    )

  def _ExpectListPerInstanceConfigs(self,
                                    instance_name='foo',
                                    return_config=False):
    request = (self.messages
               .ComputeInstanceGroupManagersListPerInstanceConfigsRequest)(
                   filter='name eq {instance}'.format(instance=instance_name),
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
                      additionalProperties=[]),
                  metadata=self.messages.PreservedState.MetadataValue(
                      additionalProperties=[])),
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

  def testSimpleCreateInstanceWithoutPreservedState(self):
    self._ExpectCreateInstance(
        preserved_state_disks=[],
        preserved_state_metadata=[],
        instance_name='foo')
    self._ExpectWaitOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --zone us-central2-a
          --instance foo
        """)

  def testSimpleCreateInstance(self):
    self._ExpectCreateInstance(
        preserved_state_disks=[],
        preserved_state_metadata=[],
        instance_name='foo')
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --zone us-central2-a
          --instance foo
        """.format(project_uri=self.project_uri))

  def testSimpleCase(self):
    disk_source_1 = self.project_uri + '/zones/us-central2-a/disks/foo'
    disk_source_2 = self.project_uri + '/zones/us-central2-a/disks/baz'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry('foo', disk_source_1,
                                             'READ_WRITE', 'never'),
        self._MakePreservedStateDiskMapEntry('baz', disk_source_2,
                                             'READ_ONLY',
                                             'on-permanent-instance-deletion')
    ]
    preserved_state_metadata = [
        self._MakePreservedStateMetadataMapEntry(
            key='key-BAR', value='value BAR'),
        self._MakePreservedStateMetadataMapEntry(
            key='key-foo', value='value foo')
    ]
    self._ExpectCreateInstance(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --zone us-central2-a
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw,auto-delete=never
          --stateful-disk device-name=baz,source={project_uri}/zones/us-central2-a/disks/baz,mode=ro,auto-delete=on-permanent-instance-deletion
          --stateful-metadata "key-BAR=value BAR,key-foo=value foo"
        """.format(project_uri=self.project_uri))

  def testCreateWithoutAnyResources(self):
    self._ExpectCreateInstance(
        preserved_state_disks=[],
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --zone us-central2-a
          --instance foo
        """)

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""
          compute instance-groups managed create-instance group-1
            --zone us-central2-a
            --instance foo
          """)

  def testUnsuccessfulCreateForMissingDiskSource(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '[source] is required for all stateful disks'):
      self.Run("""
          compute instance-groups managed create-instance group-1
            --zone us-central2-a
            --instance foo
            --stateful-disk device-name=qwerty
          """.format(project_uri=self.project_uri))


class InstanceGroupManagerCreateInstanceGARegionalTest(
    _InstanceGroupManagerCreateInstanceTestBase):
  API_VERSION = 'v1'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def _ExpectListManagedInstances(self):
    request = (self.messages
               .ComputeRegionInstanceGroupManagersListManagedInstancesRequest)(
                   instanceGroupManager='group-1',
                   maxResults=500,
                   project='fake-project',
                   region='us-central2')
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
    request = (self.messages.
               ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest)(
                   filter='name eq {instance}'.format(instance=instance_name),
                   instanceGroupManager='group-1',
                   maxResults=1,
                   project='fake-project',
                   region='us-central2')
    if return_config:
      items = [
          self.messages.PerInstanceConfig(
              name=instance_name,
              preservedState=self.messages.PreservedState(
                  disks=self.messages.PreservedState.DisksValue(
                      additionalProperties=[]),
                  metadata=self.messages.PreservedState.MetadataValue(
                      additionalProperties=[])),
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

  def _ExpectCreateInstance(self,
                            preserved_state_disks,
                            preserved_state_metadata,
                            instance_name='foo'):
    request = (
        self.messages.ComputeRegionInstanceGroupManagersCreateInstancesRequest
    )(
        instanceGroupManager='group-1',
        regionInstanceGroupManagersCreateInstancesRequest=(
            self.messages.RegionInstanceGroupManagersCreateInstancesRequest
        )(instances=[
            self.messages.PerInstanceConfig(
                name=instance_name,
                preservedState=self.messages.PreservedState(
                    disks=self.messages.PreservedState.DisksValue(
                        additionalProperties=preserved_state_disks),
                    metadata=self.messages.PreservedState.MetadataValue(
                        additionalProperties=preserved_state_metadata)))
        ]),
        project='fake-project',
        region='us-central2',
    )
    response = self.messages.Operation(
        selfLink=(self.project_uri + '/regions/us-central2/operations/foo'),)
    self.client.regionInstanceGroupManagers.CreateInstances.Expect(
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

  def testSimpleCase(self):
    disk_source_1 = self.project_uri + '/zones/us-central2-a/disks/foo'
    disk_source_2 = self.project_uri + '/zones/us-central2-a/disks/baz'
    preserved_state_disks = [
        self._MakePreservedStateDiskMapEntry('foo', disk_source_1,
                                             'READ_WRITE',
                                             'on-permanent-instance-deletion'),
        self._MakePreservedStateDiskMapEntry('baz', disk_source_2,
                                             'READ_ONLY')
    ]
    preserved_state_metadata = [
        self._MakePreservedStateMetadataMapEntry(
            key='key-BAR', value='value BAR'),
        self._MakePreservedStateMetadataMapEntry(
            key='key-foo', value='value foo')
    ]
    self._ExpectCreateInstance(
        preserved_state_disks=preserved_state_disks,
        preserved_state_metadata=preserved_state_metadata)
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --region us-central2
          --instance foo
          --stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo,mode=rw,auto-delete=on-permanent-instance-deletion
          --stateful-disk device-name=baz,source={project_uri}/zones/us-central2-a/disks/baz,mode=ro
          --stateful-metadata "key-BAR=value BAR,key-foo=value foo"
        """.format(project_uri=self.project_uri))

  def testUnsuccessfulCreateForMissingDiskSource(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        '[source] is required for all stateful disks'):
      self.Run("""
          compute instance-groups managed create-instance group-1
            --region us-central2
            --instance foo
            --stateful-disk device-name=qwerty
          """.format(project_uri=self.project_uri))

  def testCreateInstanceUsingOnlyInstanceName(self):
    self._ExpectCreateInstance(
        preserved_state_disks=[],
        preserved_state_metadata=[])
    self._ExpectPollingOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed create-instance group-1
          --region us-central2
          --instance foo
        """)


class InstanceGroupManagerCreateInstanceBetaZonalTest(
    InstanceGroupManagerCreateInstanceGAZonalTest):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagerCreateInstanceBetaRegionalTest(
    InstanceGroupManagerCreateInstanceGARegionalTest):

  API_VERSION = 'beta'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagerCreateInstanceAlphaZonalTest(
    InstanceGroupManagerCreateInstanceBetaZonalTest):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupManagerCreateInstanceAlphaRegionalTest(
    InstanceGroupManagerCreateInstanceBetaRegionalTest):

  API_VERSION = 'alpha'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
