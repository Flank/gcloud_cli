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
"""Tests for instances update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class UpdateContainerTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                          waiter_test_base.Base):

  def SetUpTrack(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.client_class = core_apis.GetClientClass('compute', 'v1')
    self.messages = core_apis.GetMessagesModule('compute', 'v1')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'v1')

  def SetUp(self):
    self.SetUpTrack()

    self.default_container_manifest = {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'command': ['echo -a "Hello world!"'],
                'args': ['arg1', 'arg2'],
                'stdin':
                    True,
                'tty':
                    True,
                'securityContext': {
                    'privileged': True
                },
                'env': [{
                    'name': 'key1',
                    'value': 'val1'
                }],
                'volumeMounts': [{
                    'mountPath': 'mount-path',
                    'name': 'host-path-0',
                    'readOnly': False
                }, {
                    'mountPath': 'tmpfs',
                    'name': 'host-path-1'
                }]
            }],
            'restartPolicy':
                'OnFailure',
            'volumes': [{
                'name': 'tmpfs-0',
                'hostPath': {
                    'path': 'host-path'
                }
            }, {
                'name': 'tmpfs-1',
                'emptyDir': {
                    'medium': 'Memory'
                }
            }]
        }
    }

  def Client(self):
    return api_mock.Client(
        self.client_class,
        real_client=core_apis.GetClientInstance(
            'compute', 'beta', no_http=True))

  def _GetOperationRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.zoneOperations')

  def _GetInstanceRef(self, name, zone):
    return self.resources.Parse(
        name,
        params={'project': self.Project(),
                'zone': zone},
        collection='compute.instances')

  def _GetOperationMessage(self, operation_ref, status, resource_ref=None):
    return self.messages.Operation(
        name=operation_ref.Name(),
        status=status,
        selfLink=operation_ref.SelfLink(),
        targetLink=resource_ref.SelfLink() if resource_ref else None)

  def _GetInstanceWithStatus(self, status):
    return self.messages.Instance(
        status=status,
        metadata=self.messages.Metadata(items=[
            self.messages.Metadata.ItemsValueListEntry(
                key='gce-container-declaration',
                value=containers_utils.DumpYaml(
                    self.default_container_manifest))
        ]))

  def _GetMetadataRequest(self):
    return self.messages.ComputeInstancesSetMetadataRequest(
        project=self.Project(),
        zone='central2-a',
        instance='instance-1',
        metadata=self.messages.Metadata(items=[
            self.messages.Metadata.ItemsValueListEntry(
                key='gce-container-declaration',
                value=containers_utils.DumpYaml({
                    'spec': {
                        'containers': [{
                            'name':
                                'instance-1',
                            'image':
                                'container-image',
                            'command': ['container-command'],
                            'args': ['container-arg'],
                            'stdin':
                                True,
                            'tty':
                                False,
                            'securityContext': {
                                'privileged': True
                            },
                            'env': [{
                                'name': 'key1',
                                'value': 'val2'
                            }],
                            'volumeMounts': [{
                                'mountPath': 'mount1',
                                'name': 'host-path-0',
                                'readOnly': True
                            }, {
                                'mountPath': 'mount2',
                                'name': 'host-path-1',
                                'readOnly': False
                            }, {
                                'mountPath': 'tmpfs2',
                                'name': 'tmpfs-2'
                            }]
                        }],
                        'restartPolicy':
                            'Always',
                        'volumes': [{
                            'name': 'tmpfs-0',
                            'hostPath': {
                                'path': 'host-path',
                            },
                        }, {
                            'name': 'tmpfs-1',
                            'emptyDir': {
                                'medium': 'Memory',
                            },
                        }, {
                            'name': 'host-path-0',
                            'hostPath': {
                                'path': 'host1',
                            },
                        }, {
                            'name': 'host-path-1',
                            'hostPath': {
                                'path': 'host2',
                            },
                        }, {
                            'name': 'tmpfs-2',
                            'emptyDir': {
                                'medium': 'Memory',
                            },
                        }],
                    }
                }))
        ]))

  def _ExpectStart(self, client):
    messages = self.messages
    client.instances.Start.Expect(
        messages.ComputeInstancesStartRequest(
            project=self.Project(), zone='central2-a', instance='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-3', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

    client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-3',
            zone='central2-a',
            project=self.Project()),
        self._GetOperationMessage(
            self._GetOperationRef('operation-3', 'central2-a'),
            self.messages.Operation.StatusValueValuesEnum.DONE,
            self._GetInstanceRef('instance-1', 'central2-a')))

    client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='instance-1', project='fake-project', zone='central2-a'),
        self.messages.Instance(name='instance-1'))

  def _ExpectStop(self, client):
    messages = self.messages
    client.instances.Stop.Expect(
        messages.ComputeInstancesStopRequest(
            project=self.Project(), zone='central2-a', instance='instance-1'),
        self._GetOperationMessage(
            self._GetOperationRef('operation-2', 'central2-a'),
            messages.Operation.StatusValueValuesEnum.PENDING))

    client.zoneOperations.Wait.Expect(
        self.messages.ComputeZoneOperationsWaitRequest(
            operation='operation-2',
            zone='central2-a',
            project=self.Project()),
        self._GetOperationMessage(
            self._GetOperationRef('operation-2', 'central2-a'),
            self.messages.Operation.StatusValueValuesEnum.DONE,
            self._GetInstanceRef('instance-1', 'central2-a')))

    client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='instance-1', project='fake-project', zone='central2-a'),
        self.messages.Instance(name='instance-1'))

  def testWithOperationPolling_runningVm(self):
    messages = self.messages
    with self.Client() as client:
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          self._GetInstanceWithStatus(
              messages.Instance.StatusValueValuesEnum.RUNNING))

      client.instances.SetMetadata.Expect(
          self._GetMetadataRequest(),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              messages.Operation.StatusValueValuesEnum.PENDING))

      client.zoneOperations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))

      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self._ExpectStop(client)
      self._ExpectStart(client)

      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            --container-image container-image
            --container-command container-command
            --container-arg container-arg
            --container-privileged
            --remove-container-mounts mount-path,tmpfs
            --container-mount-host-path host-path=host1,mount-path=mount1,mode=ro
            --container-mount-host-path host-path=host2,mount-path=mount2,mode=rw
            --container-mount-tmpfs mount-path=tmpfs2
            --container-env key1=val2
            --container-stdin
            --no-container-tty
            --container-restart-policy ALWAYS
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating specification of container [instance-1]')
    self.AssertErrContains('Stopping instance [instance-1]')
    self.AssertErrContains('Starting instance [instance-1]')

  def testWithOperationPolling_suspendedVm(self):
    messages = self.messages
    with self.Client() as client:
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          self._GetInstanceWithStatus(
              messages.Instance.StatusValueValuesEnum.SUSPENDED))

      client.instances.SetMetadata.Expect(
          self._GetMetadataRequest(),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              messages.Operation.StatusValueValuesEnum.PENDING))

      client.zoneOperations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))

      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self._ExpectStop(client)

      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            --container-image container-image
            --container-command container-command
            --container-arg container-arg
            --container-privileged
            --remove-container-mounts mount-path,tmpfs
            --container-mount-host-path host-path=host1,mount-path=mount1,mode=ro
            --container-mount-host-path host-path=host2,mount-path=mount2,mode=rw
            --container-mount-tmpfs mount-path=tmpfs2
            --container-env key1=val2
            --container-stdin
            --no-container-tty
            --container-restart-policy ALWAYS
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating specification of container [instance-1]')
    self.AssertErrContains('Stopping instance [instance-1]')

  def testWithOperationPolling_stoppedVm(self):
    messages = self.messages
    with self.Client() as client:
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          self._GetInstanceWithStatus(
              messages.Instance.StatusValueValuesEnum.TERMINATED))

      client.instances.SetMetadata.Expect(
          self._GetMetadataRequest(),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              messages.Operation.StatusValueValuesEnum.PENDING))

      client.zoneOperations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))

      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            --container-image container-image
            --container-command container-command
            --container-arg container-arg
            --container-privileged
            --remove-container-mounts mount-path,tmpfs
            --container-mount-host-path host-path=host1,mount-path=mount1,mode=ro
            --container-mount-host-path host-path=host2,mount-path=mount2,mode=rw
            --container-mount-tmpfs mount-path=tmpfs2
            --container-env key1=val2
            --container-stdin
            --no-container-tty
            --container-restart-policy ALWAYS
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains(
        'Updating specification of container [instance-1]')

  def testEmptyContainerImage(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--container-image]: Empty string is not allowed.'):
      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            --container-image ""
          """)

  def testNoContainer(self):
    messages = self.messages
    with self.Client() as client:
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          messages.Instance(metadata=messages.Metadata(items=[])))
      with self.AssertRaisesExceptionMatches(
          containers_utils.NoGceContainerDeclarationMetadataKey,
          "Instance doesn't have gce-container-declaration metadata key - it "
          'is not a container.'):
        self.Run("""
            compute instances update-container instance-1
              --zone central2-a
              --container-stdin
            """)

  def testNoContainerCommandAndArgs(self):
    messages = self.messages
    with self.Client() as client:
      client.instances.Get.Expect(
          messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          messages.Instance(metadata=messages.Metadata(items=[
              messages.Metadata.ItemsValueListEntry(
                  key='gce-container-declaration',
                  value=containers_utils.DumpYaml({
                      'spec': {
                          'containers': [{
                              'name': 'instance-1',
                              'image': 'gcr.io/my-docker/test-image',
                              'securityContext': {
                                  'privileged': True
                              },
                          }],
                      }
                  }))
          ])))

      client.instances.SetMetadata.Expect(
          messages.ComputeInstancesSetMetadataRequest(
              project=self.Project(),
              zone='central2-a',
              instance='instance-1',
              metadata=messages.Metadata(items=[
                  messages.Metadata.ItemsValueListEntry(
                      key='gce-container-declaration',
                      value=containers_utils.DumpYaml({
                          'spec': {
                              'containers': [{
                                  'name': 'instance-1',
                                  'image': 'gcr.io/my-docker/test-image',
                                  'securityContext': {
                                      'privileged': True
                                  },
                                  'volumeMounts': [],
                              }],
                              'volumes': []
                          }
                      }))
              ])),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              messages.Operation.StatusValueValuesEnum.PENDING))

      client.zoneOperations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))

      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))

      self._ExpectStop(client)
      self._ExpectStart(client)

      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            --clear-container-command
            --clear-container-args
          """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Updating specification of container [instance-1]')
    self.AssertErrContains('Stopping instance [instance-1]')
    self.AssertErrContains('Starting instance [instance-1]')


class UpdateContainerTestBeta(UpdateContainerTest):

  def SetUpTrack(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.client_class = core_apis.GetClientClass('compute', 'beta')
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')


class UpdateContainerAlphaTest(
    UpdateContainerTest, parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.client_class = core_apis.GetClientClass('compute', 'alpha')
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def Client(self):
    return api_mock.Client(
        self.client_class,
        real_client=core_apis.GetClientInstance(
            'compute', 'alpha', no_http=True))

  def _GetContainerManifest(self, volume_mounts, volumes):
    return {
        'spec': {
            'containers': [{
                'name':
                    'instance-1',
                'image':
                    'gcr.io/my-docker/test-image',
                'command': ['echo -a "Hello world!"'],
                'args': ['arg1', 'arg2'],
                'stdin':
                    True,
                'tty':
                    True,
                'securityContext': {
                    'privileged': True
                },
                'env': [{
                    'name': 'key1',
                    'value': 'val1'
                }],
                'volumeMounts': volume_mounts}],
            'restartPolicy':
                'OnFailure',
            'volumes': volumes}
    }

  def _GetInstanceWithManifest(self, manifest=None, disks=None):
    disks = disks or []
    manifest = manifest or {}
    return self.messages.Instance(
        status=self.messages.Instance.StatusValueValuesEnum.RUNNING,
        disks=disks,
        metadata=self.messages.Metadata(items=[
            self.messages.Metadata.ItemsValueListEntry(
                key='gce-container-declaration',
                value=containers_utils.DumpYaml(
                    manifest))
        ]))

  def _GetDiskMessage(self, device_name=None, mode=None, disk_name=None):
    return self.messages.AttachedDisk(
        autoDelete=False,
        boot=False,
        deviceName=device_name,
        licenses=[],
        mode=mode or self.messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=(self.messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        source='https://compute.googleapis.com/compute/v1/projects/{}/zones'
        '/central2-a/disks/{}'.format(self.Project(), disk_name))

  def _GetMetadataRequestWithMetadata(self, metadata):
    return self.messages.ComputeInstancesSetMetadataRequest(
        project=self.Project(),
        zone='central2-a',
        instance='instance-1',
        metadata=self.messages.Metadata(items=[
            self.messages.Metadata.ItemsValueListEntry(
                key='gce-container-declaration',
                value=containers_utils.DumpYaml(metadata))
        ]))

  @parameterized.named_parameters(
      ('Remove',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       [], [], [], '--remove-container-mounts "/mounted"'),
      ('Update',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       ['disk-0', 'disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-1', 'mountPath': '/mounted1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}},
        {'name': 'pd-1',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       '--container-mount-disk name=disk-1,mount-path="/mounted1"'),
      ('UpdateNoDiskName',
       [], [], ['disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       '--container-mount-disk mount-path="/mounted"'),
      ('UpdateAndRemove',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       ['disk-0', 'disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       '--container-mount-disk name=disk-1,mount-path="/mounted1" '
       '--remove-container-mounts "/mounted"'),
      ('UpdateWithRepeated',
       [], [], ['disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-0', 'mountPath': '/mounted-1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4',
                               'partition': 1}}],
       '--container-mount-disk name=disk-1,partition=1,mount-path="/mounted" '
       '--container-mount-disk name=disk-1,partition=1,mount-path="/mounted-1"'
      ),
      ('UpdateWithRepeatedNoName',
       [], [], ['disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-0', 'mountPath': '/mounted-1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4',
                               'partition': 1}}],
       '--container-mount-disk partition=1,mount-path="/mounted" '
       '--container-mount-disk partition=1,mount-path="/mounted-1"'),
      ('UpdateWithRepeatedNoPartition',
       [], [], ['disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-0', 'mountPath': '/mounted-1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       '--container-mount-disk name=disk-1,mount-path="/mounted" '
       '--container-mount-disk name=disk-1,mount-path="/mounted-1"'),
      ('UpdateWithRepeatedNoNameNoPartition',
       [], [], ['disk-1'],
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-0', 'mountPath': '/mounted-1', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       '--container-mount-disk mount-path="/mounted" '
       '--container-mount-disk mount-path="/mounted-1"')
  )
  def testUpdateContainerMountDisk(self, volume_mounts, volumes, disk_names,
                                   updated_volume_mounts, updated_volumes,
                                   flag):
    disks = [
        self._GetDiskMessage(device_name=disk_name, disk_name=disk_name)
        for disk_name in disk_names]
    instance = self._GetInstanceWithManifest(
        self._GetContainerManifest(volume_mounts, volumes),
        disks=disks)
    with self.Client() as client:
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          instance)
      client.instances.SetMetadata.Expect(
          self._GetMetadataRequestWithMetadata(
              self._GetContainerManifest(updated_volume_mounts,
                                         updated_volumes)),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.PENDING))
      client.zoneOperations.Wait.Expect(
          self.messages.ComputeZoneOperationsWaitRequest(
              operation='operation-X',
              zone='central2-a',
              project=self.Project()),
          self._GetOperationMessage(
              self._GetOperationRef('operation-X', 'central2-a'),
              self.messages.Operation.StatusValueValuesEnum.DONE,
              self._GetInstanceRef('instance-1', 'central2-a')))
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              instance='instance-1', project='fake-project', zone='central2-a'),
          self.messages.Instance(name='instance-1'))
      self._ExpectStop(client)
      self._ExpectStart(client)

      self.Run("""
          compute instances update-container instance-1
            --zone central2-a
            {}
          """.format(flag))

  @parameterized.named_parameters(
      # Must have a disk attached.
      ('DiskNotPresent', [], [], [],
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)Attempting to mount a disk that is not '
       r'attached to the instance(.*)\[disk-1\]'),
      # Must attach a disk with the same name first.
      ('DiskNameNotPresent',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       [('disk-0', 'disk-0')],
       '--container-mount-disk name=disk-1,mount-path="/mounted"',
       r'--container-mount-disk(.*)Attempting to mount a disk that is not '
       r'attached to the instance(.*)\[disk-1\]'),
      # If no name is given for --container-mount-disk, there can be only one
      # disk attached.
      ('NoNameSpecified',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': False},
        {'name': 'pd-1', 'mountPath': '/mounted', 'readOnly': False}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}},
        {'name': 'pd-1',
         'gcePersistentDisk': {'pdName': 'disk-1', 'fsType': 'ext4'}}],
       [('disk-0', 'disk-0'), ('disk-1', 'disk-1')],
       '--container-mount-disk mount-path="/mounted"',
       r'--container-mount-disk(.*)Must specify the name of the disk to be '
       r'mounted unless exactly one disk is attached to the instance'),
      # attached disk mode must be rw if --container-mount-disk mode is rw
      ('MismatchedMode',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': True}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       [('disk-0', 'disk-0')],
       '--container-mount-disk name=disk-0,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[rw\](.*)\[ro\](.*)disk name \[disk-0\], '
       r'partition \[None\]'),
      # attached disk must have the same name as deviceName
      ('MismatchedDiskName',
       [{'name': 'pd-0', 'mountPath': '/mounted', 'readOnly': True}],
       [{'name': 'pd-0',
         'gcePersistentDisk': {'pdName': 'disk-0', 'fsType': 'ext4'}}],
       [('disk-x', 'disk-0')],
       '--container-mount-disk name=disk-0,mount-path="/mounted",mode=rw',
       r'--container-mount-disk(.*)\[disk-0\](.*)\[disk-x\]'))
  def testContainerMountDiskInvalid(self, volume_mounts, volumes, disk_names,
                                    container_mount_disk_flag, regexp):
    disks = [
        self._GetDiskMessage(device_name=dev, disk_name=disk)
        for (dev, disk) in disk_names]
    with self.Client() as client:
      client.instances.Get.Expect(
          self.messages.ComputeInstancesGetRequest(
              project=self.Project(), zone='central2-a', instance='instance-1'),
          self._GetInstanceWithManifest(
              self._GetContainerManifest(volume_mounts, volumes),
              disks=disks))
      with self.assertRaisesRegexp(
          exceptions.InvalidArgumentException,
          regexp):
        self.Run("""
            compute instances update-container instance-1
              --zone central2-a
              {}
            """.format(container_mount_disk_flag))


if __name__ == '__main__':
  test_case.main()
