# -*- coding: utf-8 -*- #
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
"""Tests for instances update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.api_lib.util import waiter as waiter_test_base


class UpdateContainerTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                          waiter_test_base.Base):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.client_class = core_apis.GetClientClass('compute', 'beta')
    self.messages = core_apis.GetMessagesModule('compute', 'beta')
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'beta')

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

    client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
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

    client.zoneOperations.Get.Expect(
        self.messages.ComputeZoneOperationsGetRequest(
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

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
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

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
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

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
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

      client.zoneOperations.Get.Expect(
          self.messages.ComputeZoneOperationsGetRequest(
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


if __name__ == '__main__':
  test_case.main()
