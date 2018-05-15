# Copyright 2017 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
from apitools.base.py import exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import httplib2


class _InstanceGroupManagerInstanceConfigsUpdateTestBase(
    sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.client = mock.Client(core_apis.GetClientClass('compute', 'alpha'))
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE
    self.endpoint_uri = 'https://www.googleapis.com/compute/alpha/'
    self.project_uri = '{endpoint_uri}projects/fake-project'.format(
        endpoint_uri=self.endpoint_uri)

    metadata_override_1 = (
        self.messages.ManagedInstanceOverride.MetadataValueListEntry)(
            key='key-BAR', value='value BAR')
    metadata_override_2 = (
        self.messages.ManagedInstanceOverride.MetadataValueListEntry)(
            key='key-foo', value='value foo')
    self.metadata_overrides = [metadata_override_1, metadata_override_2]

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


class InstanceGroupManagerInstanceConfigsUpdateZonalTest(
    _InstanceGroupManagerInstanceConfigsUpdateTestBase):

  def SetUp(self):
    self._disk_override_1 = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='foo',
        source=(self.project_uri + '/zones/us-central2-a/disks/foo'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_WRITE'),
    )
    self._disk_override_2 = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='baz',
        source=(self.project_uri + '/zones/us-central2-a/disks/baz'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_ONLY'),
    )

  def _ExpectListPerInstanceConfigs(self, return_config=True):
    request = (
        self.messages.ComputeInstanceGroupManagersListPerInstanceConfigsRequest
    )(
        filter='instance eq {project_uri}/zones/us-central2-a/instances/foo'.
        format(project_uri=self.project_uri),
        instanceGroupManager='group-1',
        maxResults=1,
        project='fake-project',
        zone='us-central2-a',
    )
    if return_config:
      items = [
          self.messages.PerInstanceConfig(
              instance='{project_uri}/zones/us-central2-a/instances/foo'.format(
                  project_uri=self.project_uri),
              override=self.messages.ManagedInstanceOverride(
                  disks=[
                      self.messages.ManagedInstanceOverrideDiskOverride(
                          deviceName='foo',
                          source=(self.project_uri +
                                  '/zones/us-central2-a/disks/foo'),
                          mode=self.messages.
                          ManagedInstanceOverrideDiskOverride.
                          ModeValueValuesEnum('READ_WRITE'),
                      ),
                      self.messages.ManagedInstanceOverrideDiskOverride(
                          deviceName='baz',
                          source=(self.project_uri +
                                  '/zones/us-central2-a/disks/baz'),
                          mode=self.messages.
                          ManagedInstanceOverrideDiskOverride.
                          ModeValueValuesEnum('READ_ONLY'),
                      ),
                  ],
                  metadata=[
                      self.messages.ManagedInstanceOverride.
                      MetadataValueListEntry(key='key-BAR', value='value BAR'),
                      self.messages.ManagedInstanceOverride.
                      MetadataValueListEntry(key='key-foo', value='value foo'),
                  ],
                  origin=self.messages.ManagedInstanceOverride.
                  OriginValueValuesEnum('AUTO_GENERATED'),
              ),
          ),
      ]
    else:
      items = []
    response = self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
        items=items)
    self.client.instanceGroupManagers.ListPerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectUpdatePerInstanceConfigs(self, disk_overrides, metadata_overrides):
    request = (
        self.messages.
        ComputeInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            instanceGroupManagersUpdatePerInstanceConfigsReq=(
                self.messages.InstanceGroupManagersUpdatePerInstanceConfigsReq
            )(perInstanceConfigs=[
                self.messages.PerInstanceConfig(
                    instance=('{project_uri}/zones/us-central2-a/instances/foo'.
                              format(project_uri=self.project_uri)),
                    override=self.messages.ManagedInstanceOverride(
                        disks=disk_overrides,
                        metadata=metadata_overrides,
                    )),
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
    disk_override = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='foo',
        source=(self.project_uri + '/zones/us-central2-a/disks/foo-2'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_ONLY'),
    )
    disk_overrides = [disk_override]
    metadata_override = (
        self.messages.ManagedInstanceOverride.MetadataValueListEntry)(
            key='key-BAR', value='new value')
    metadata_overrides = [metadata_override]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides, metadata_overrides=metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --update-stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo-2,mode=ro
          --remove-stateful-disks baz
          --update-stateful-metadata "key-BAR=new value"
          --remove-stateful-metadata key-foo
        """.format(project_uri=self.project_uri))

  def testUpdateAddNonExistingDisk(self):
    disk_override_3 = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='qwerty',
        source=(self.project_uri + '/zones/us-central2-a/disks/abc123'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_WRITE'),
    )
    disk_overrides = [
        self._disk_override_1, self._disk_override_2, disk_override_3
    ]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides,
        metadata_overrides=self.metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --update-stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=rw
        """.format(project_uri=self.project_uri))

  def testUpdateAddDiskOverrideUsingOnlyDeviceName(self):
    disk_override_3 = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='bar',
        source=(self.project_uri + '/zones/us-central2-a/disks/bar'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_WRITE'),
    )
    disk_overrides = [
        self._disk_override_1, self._disk_override_2, disk_override_3
    ]
    self._ExpectListPerInstanceConfigs()
    self.ExpectGetInstance()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides,
        metadata_overrides=self.metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --update-stateful-disk device-name=bar
        """)

  def testUpdateRemoveAllDiskAndMetadataOverrides(self):
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=[], metadata_overrides=[])
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --remove-stateful-disks foo,baz
          --remove-stateful-metadata key-BAR,key-foo
        """)

  def testUpdateWithForceInstanceUpdate(self):
    disk_override = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='foo',
        source=(self.project_uri + '/zones/us-central2-a/disks/foo'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_WRITE'),
    )
    disk_overrides = [disk_override]
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides,
        metadata_overrides=self.metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectGetOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --zone us-central2-a
          --instance foo
          --remove-stateful-disks baz
          --force-instance-update
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
            --update-stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/abc123,mode=ro
          """.format(project_uri=self.project_uri))

  def testUnsuccessfulUpdateForTheSameDeviceNameToUpdateAndRemove(self):
    with self.AssertRaisesExceptionMatches(
        calliope_exceptions.InvalidArgumentException,
        'cannot be updated and removed in one command call'):
      self.Run("""
          compute instance-groups managed instance-configs update group-1
            --zone us-central2-a
            --instance foo
            --update-stateful-disk device-name=qwerty,source={project_uri}/zones/us-central2-a/disks/abc123,mode=ro
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
            --update-stateful-metadata key-abc=value
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
            --update-stateful-disk device-name=foo
          """)


class InstanceGroupManagerInstanceConfigsUpdateRegionalTest(
    _InstanceGroupManagerInstanceConfigsUpdateTestBase):

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
    response = self.messages.InstanceGroupManagersListManagedInstancesResponse(
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
        filter='instance eq {project_uri}/zones/us-central2-a/instances/foo'.
        format(project_uri=self.project_uri),
        instanceGroupManager='group-1',
        maxResults=1,
        project='fake-project',
        region='us-central2',
    )
    items = [
        self.messages.PerInstanceConfig(
            instance='{project_uri}/zones/us-central2-a/instances/foo'.format(
                project_uri=self.project_uri),
            override=self.messages.ManagedInstanceOverride(
                disks=[
                    self.messages.ManagedInstanceOverrideDiskOverride(
                        deviceName='foo',
                        source=(self.project_uri +
                                '/zones/us-central2-a/disks/foo'),
                        mode=self.messages.ManagedInstanceOverrideDiskOverride.
                        ModeValueValuesEnum('READ_WRITE'),
                    ),
                    self.messages.ManagedInstanceOverrideDiskOverride(
                        deviceName='baz',
                        source=(self.project_uri +
                                '/zones/us-central2-a/disks/baz'),
                        mode=self.messages.ManagedInstanceOverrideDiskOverride.
                        ModeValueValuesEnum('READ_ONLY'),
                    ),
                ],
                metadata=[
                    self.messages.ManagedInstanceOverride.
                    MetadataValueListEntry(key='key-BAR', value='value BAR'),
                    self.messages.ManagedInstanceOverride.
                    MetadataValueListEntry(key='key-foo', value='value foo'),
                ],
                origin=self.messages.ManagedInstanceOverride.
                OriginValueValuesEnum('AUTO_GENERATED'),
            ),
        ),
    ]
    response = self.messages.InstanceGroupManagersListPerInstanceConfigsResp(
        items=items)
    self.client.regionInstanceGroupManagers.ListPerInstanceConfigs.Expect(
        request,
        response=response,
    )

  def _ExpectUpdatePerInstanceConfigs(self, disk_overrides, metadata_overrides):
    request = (
        self.messages.
        ComputeRegionInstanceGroupManagersUpdatePerInstanceConfigsRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagerUpdateInstanceConfigReq=(
                self.messages.RegionInstanceGroupManagerUpdateInstanceConfigReq
            )(perInstanceConfigs=[
                self.messages.PerInstanceConfig(
                    instance=('{project_uri}/zones/us-central2-a/instances/foo'.
                              format(project_uri=self.project_uri)),
                    override=self.messages.ManagedInstanceOverride(
                        disks=disk_overrides,
                        metadata=metadata_overrides,
                    )),
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
        self.messages.
        ComputeRegionInstanceGroupManagersApplyUpdatesToInstancesRequest)(
            instanceGroupManager='group-1',
            regionInstanceGroupManagersApplyUpdatesRequest=(
                self.messages.RegionInstanceGroupManagersApplyUpdatesRequest)(
                    instances=[
                        self.project_uri + '/zones/us-central2-a/instances/foo',
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
    disk_override = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='foo',
        source=(self.project_uri + '/zones/us-central2-a/disks/foo-2'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_ONLY'),
    )
    disk_overrides = [disk_override]
    metadata_override = (
        self.messages.ManagedInstanceOverride.MetadataValueListEntry)(
            key='key-BAR', value='new value')
    metadata_overrides = [metadata_override]
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides, metadata_overrides=metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --region us-central2
          --instance foo
          --update-stateful-disk device-name=foo,source={project_uri}/zones/us-central2-a/disks/foo-2,mode=ro
          --remove-stateful-disks baz
          --update-stateful-metadata "key-BAR=new value"
          --remove-stateful-metadata key-foo
        """.format(project_uri=self.project_uri))

  def testUpdateWithForceInstanceUpdate(self):
    disk_override = self.messages.ManagedInstanceOverrideDiskOverride(
        deviceName='foo',
        source=(self.project_uri + '/zones/us-central2-a/disks/foo'),
        mode=self.messages.ManagedInstanceOverrideDiskOverride.
        ModeValueValuesEnum('READ_WRITE'),
    )
    disk_overrides = [disk_override]
    self._ExpectListManagedInstances()
    self._ExpectListPerInstanceConfigs()
    self._ExpectUpdatePerInstanceConfigs(
        disk_overrides=disk_overrides,
        metadata_overrides=self.metadata_overrides)
    self._ExpectGetOperation()
    self._ExpectGetInstanceGroupManager()
    self._ExpectApplyUpdatesToInstances()
    self._ExpectGetOperation('apply')
    self._ExpectGetInstanceGroupManager()

    self.Run("""
        compute instance-groups managed instance-configs update group-1
          --region us-central2
          --instance foo
          --remove-stateful-disks baz
          --force-instance-update
        """)


if __name__ == '__main__':
  test_case.main()
