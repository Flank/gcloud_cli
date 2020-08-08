# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Base class for all tpu_nodes tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import os

from apitools.base.py import encoding
from apitools.base.py.exceptions import HttpConflictError
from apitools.base.py.exceptions import HttpNotFoundError
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import resources
from tests.lib.api_lib.util import waiter as waiter_test_base
from tests.lib.surface.compute.tpus import base
import mock as base_mock


class TpuUnitTestBase(base.TpuUnitTestBase,
                      waiter_test_base.CloudOperationsBase):
  """Base class for all TPU Execution Group unit tests."""

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetupComputeMocks(self):
    self.instances_messages = core_apis.GetMessagesModule(
        'compute', self.compute_api_version)
    self.mock_instance_client = mock.Client(
        core_apis.GetClientClass('compute', self.compute_api_version),
        real_client=core_apis.GetClientInstance(
            'compute', self.compute_api_version, no_http=True))
    self.mock_instance_client.Mock()
    self.addCleanup(self.mock_instance_client.Unmock)

  def SetupSSHMocks(self):
    make_requests_patcher = base_mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    self.env = ssh.Environment(ssh.Suite.OPENSSH)
    self.env.ssh = 'ssh'
    self.env.ssh_term = 'ssh'

    self.home_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join('home', 'me')))
    self.ssh_dir = os.path.realpath(
        self.CreateTempDir(name=os.path.join(self.home_dir, '.ssh')))
    # self.private_key_file = os.path.join(self.ssh_dir, 'id_rsa')
    self.private_key_file = ssh.Keys.DEFAULT_KEY_FILE
    self.public_key_file = self.private_key_file + '.pub'
    self.known_hosts_file = os.path.join(self.ssh_dir, 'known_hosts')
    self.StartObjectPatch(ssh.KnownHosts, 'DEFAULT_PATH', self.known_hosts_file)

    # Common test vars
    self.remote = ssh.Remote('randomIP', user='me')
    self.options = {
        'UserKnownHostsFile': self.known_hosts_file,
        'IdentitiesOnly': 'yes',
        'CheckHostIP': 'no',
        'StrictHostKeyChecking': 'no',
    }

    # Keys
    self.pubkey = ssh.Keys.PublicKey(
        'ssh-rsa',
        'AAAAB3NzaC1yc2EAAAADAQABAAABAQCwFyCpWwERm3r1/snlgt9907rd5FcV2l'
        'vzdUxt04FCr+uNNusfx/9LUmRPVjHyIXZAcOeqRlnM8kKo765msDdyAn0n36M4LjmXBqnj'
        'edI+4OLhYPCDxGaHfnlOLIY3HCup7JSn1/u7iBddE0KnMQ13oBi010BK5iwNRe1Mr8m1ar'
        '06BK9n3UN/0DrbydTGbqcaOfYzKuMK5aeCEgvxu/TAOHsAG3fhJ0eR5orfRRUdIngP8kjZ'
        'rSrS12IRTEptaiR+NXd4/GVDcm1VvLcX8kyugVy3Md1i7kHV883jz9diMbhC/fVxERJK/7'
        'PfiEb/cYLCqWE6pTAFl+G6M4NvO3Bf', 'me@my-computer')
    # self.keys = ssh.Keys.FromFilename(ssh.Keys.DEFAULT_KEY_FILE)
    self.keys = ssh.Keys.FromFilename(self.private_key_file)

    self.get_public_key = self.StartObjectPatch(
        ssh.Keys, 'GetPublicKey', autospec=True, return_value=self.pubkey)
    self.ensure_keys = self.StartObjectPatch(ssh.Keys, 'EnsureKeysExist',
                                             autospec=True)

    self.ssh_init = self.StartObjectPatch(
        ssh.SSHCommand, '__init__', return_value=None, autospec=True)
    self.ssh_run = self.StartObjectPatch(
        ssh.SSHCommand, 'Run', autospec=True, return_value=0)

    self.poller_init = self.StartObjectPatch(
        ssh.SSHPoller, '__init__', return_value=None, autospec=True)
    self.poller_poll = self.StartObjectPatch(
        ssh.SSHPoller, 'Poll', autospec=True, return_value=0)

    self.project_resource = self.instances_messages.Project(
        commonInstanceMetadata=self.instances_messages.Metadata(
            items=[
                self.instances_messages.Metadata.ItemsValueListEntry(
                    key='a',
                    value='b'),
                self.instances_messages.Metadata.ItemsValueListEntry(
                    key='sshKeys',
                    value='me:{0}\n'.format(self.public_key_material)),
            ]),
        name='my-project',
    )

    self.make_requests.side_effect = iter([
        [self.project_resource],
        [self.project_resource],
        [self.project_resource],
    ])

  @property
  def public_key_material(self):
    return self.pubkey.ToEntry(include_comment=True)

  def SetUp(self):
    self.SetupComputeMocks()
    self.SetupSSHMocks()

  def MakeTestTPUNode(self):
    return self.tpu_messages.Node(
        acceleratorType=u'v2-8',
        network=u'',
        tensorflowVersion=u'1.6',
        schedulingConfig=None)

  def _BuildOperationResponse(self, name, instance_op_name, status):
    return self.instances_messages.Operation(
        name=instance_op_name,
        zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
        operationType='insert',
        targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
        .format(name),
        selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
        .format(instance_op_name),
        status=status)

  def _makeTestTPUNode(self,
                       accelerator_type,
                       tensorflow_version,
                       preemptible,
                       network):
    return self.tpu_messages.Node(
        acceleratorType=accelerator_type,
        network=network,
        tensorflowVersion=tensorflow_version,
        schedulingConfig=self.tpu_messages.SchedulingConfig(
            preemptible=preemptible))

  def _makeTestInstanceSpec(self,
                            instance_name,
                            preemptible_vm,
                            source_image,
                            network='default'):
    instance_helper = tpu_utils.Instance(self.track)
    return instance_helper.BuildInstanceSpec(
        instance_name,
        'central2-a',
        'n1-standard-1',
        250,
        preemptible=preemptible_vm,
        source_image=source_image,
        network=network)

  def ExpectTPUCreateCall(self, name, accelerator_type, tensorflow_version,
                          preemptible, network='default'):
    node = self._makeTestTPUNode(
        accelerator_type, tensorflow_version, preemptible, network)
    raw_dict = encoding.MessageToDict(node)
    response = encoding.DictToMessage(raw_dict,
                                      self.tpu_messages.Operation.ResponseValue)
    self.mock_tpu_client.projects_locations_nodes.Create.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesCreateRequest(
            node=node,
            nodeId=name,
            parent=u'projects/fake-project/locations/central2-a'),
        exception=None,
        response=self.tpu_messages.Operation(
            done=False,
            name=
            'projects/fake-project/locations/central2-a/operations/fake-operation',
            response=response
            )
        )

  def ExpectTPUCreateCallWithConflictError(
      self, name, accelerator_type, tensorflow_version, preemptible,
      network='default'):
    node = self._makeTestTPUNode(
        accelerator_type, tensorflow_version, preemptible, network)
    self.mock_tpu_client.projects_locations_nodes.Create.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesCreateRequest(
            node=node,
            nodeId=name,
            parent=u'projects/fake-project/locations/central2-a'),
        exception=HttpConflictError(None, None, None),
        response=None
        )

  def ExpectInstanceCreateCall(
      self, instance_name, instance_op_name, preemptible_vm, source_image):
    self.mock_instance_client.instances.Insert.Expect(
        request=self.instances_messages.ComputeInstancesInsertRequest(
            instance=self._makeTestInstanceSpec(
                instance_name, preemptible_vm, source_image),
            project='fake-project',
            zone=u'central2-a'),
        exception=None,
        response=self.instances_messages.Operation(
            id=6119375431605684808,
            name=instance_op_name,
            zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
            operationType='insert',
            targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/testinggcloud',
            targetId=938667187749259849,
            status=self.instances_messages.Operation.StatusValueValuesEnum
            .RUNNING,
            user='fakeuser@google.com',
            progress=0,
            insertTime='2020-05-05T11:47:03.249-07:00',
            startTime='2020-05-05T11:47:03.251-07:00',
            selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/operation-1588704422227-5a4eb12bd6fe5-8cacd251-ec86b3c2',
            kind='compute#operation'))

  def ExpectInstanceCreateCallFailure(
      self, instance_name, preemptible_vm, source_image):
    self.mock_instance_client.instances.Insert.Expect(
        request=self.instances_messages.ComputeInstancesInsertRequest(
            instance=self._makeTestInstanceSpec(
                instance_name, preemptible_vm, source_image),
            project='fake-project',
            zone=u'central2-a'),
        exception=HttpConflictError(None, None, None),
        response=None)

  def ExpectInstanceOperationCall(self, name, instance_op_name):
    self.mock_instance_client.zoneOperations.Wait.Expect(
        request=self.instances_messages.ComputeZoneOperationsWaitRequest(
            operation=instance_op_name,
            project=u'fake-project',
            zone=u'central2-a'),
        response=self._BuildOperationResponse(
            name, instance_op_name,
            self.instances_messages.Operation.StatusValueValuesEnum.DONE))

  def ExpectInstanceGetCall(self, name, instance_op_name):
    network_interface = self.instances_messages.NetworkInterface(
        network='projects/fake-project/global/networks/default',
        accessConfigs=[
            self.instances_messages.AccessConfig(
                name='External NAT',
                type=self.instances_messages.AccessConfig.TypeValueValuesEnum
                .ONE_TO_ONE_NAT,
                natIP='randomIP'
                )
        ])
    self.mock_instance_client.instances.Get.Expect(
        request=self.instances_messages.ComputeInstancesGetRequest(
            instance=name,
            project=u'fake-project',
            zone=u'central2-a'),
        response=self.instances_messages.Instance(
            name=name,
            networkInterfaces=[network_interface])
        )

  def ExpectTPUDeleteCall(self, name, tpu_op_name):
    self.mock_tpu_client.projects_locations_nodes.Delete.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/fake-project/locations/central2-a/nodes/{}'.format(
                name)),
        response=self.tpu_messages.Operation(
            done=False,
            name=tpu_op_name,
            response=self.tpu_messages.Operation.ResponseValue()
            )
        )

  def ExpectTPUOperationNoResource(self, tpu_op_name):
    request_type = self.mock_tpu_client.projects_locations_operations.GetRequestType(
        'Get')
    response_type = self.mock_tpu_client.projects_locations_operations.GetResponseType(
        'Get')
    response = response_type(done=True, response=response_type.ResponseValue())
    self.mock_tpu_client.projects_locations_operations.Get.Expect(
        request=request_type(name=tpu_op_name),
        response=response
        )

  def ExpectTPUDeleteCallWithHTTPNotFound(self, name, tpu_op_name):
    self.mock_tpu_client.projects_locations_nodes.Delete.Expect(
        request=self.tpu_messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/fake-project/locations/central2-a/nodes/{}'.format(
                name)),
        exception=HttpNotFoundError(None, None, None)
        )

  def ExpectTPUOperationCallWithHTTPNotFound(self, name, tpu_op_name):
    result_request_type = self.mock_tpu_client.projects_locations_operations.GetRequestType(
        'Get')
    self.mock_tpu_client.projects_locations_operations.Get.Expect(
        request=result_request_type(name=tpu_op_name),
        exception=HttpNotFoundError(None, None, None)
        )

  def ExpectInstanceDeleteCall(self, name, instance_op_name):
    self.mock_instance_client.instances.Delete.Expect(
        request=self.instances_messages.ComputeInstancesDeleteRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        response=self.instances_messages.Operation(
            name=instance_op_name,
            zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
            operationType='delete',
            targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
            .format(name),
            selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
            .format(instance_op_name),
            status=self.instances_messages.Operation.StatusValueValuesEnum
            .PENDING))

  def ExpectInstanceStopCall(self, name, instance_op_name):
    self.mock_instance_client.instances.Stop.Expect(
        request=self.instances_messages.ComputeInstancesStopRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        response=self.instances_messages.Operation(
            name=instance_op_name,
            zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
            operationType='delete',
            targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
            .format(name),
            selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
            .format(instance_op_name),
            status=self.instances_messages.Operation.StatusValueValuesEnum
            .PENDING))

  def ExpectInstanceStartCall(self, name, instance_op_name):
    self.mock_instance_client.instances.Start.Expect(
        request=self.instances_messages.ComputeInstancesStartRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        response=self.instances_messages.Operation(
            name=instance_op_name,
            zone='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a',
            operationType='delete',
            targetLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/instances/{}'
            .format(name),
            selfLink='https://www.googleapis.com/compute/v1/projects/fake-project/zones/central2-a/operations/{}'
            .format(instance_op_name),
            status=self.instances_messages.Operation.StatusValueValuesEnum
            .PENDING))

  def ExpectInstanceStartCallWithHTTPNotFoundError(
      self, name):
    self.mock_instance_client.instances.Start.Expect(
        request=self.instances_messages.ComputeInstancesStartRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        exception=HttpNotFoundError(None, None, None),
        response=None)

  def ExpectInstanceStopCallWithHTTPNotFound(self, name, instance_op_name):
    self.mock_instance_client.instances.Stop.Expect(
        request=self.instances_messages.ComputeInstancesStopRequest(
            project='fake-project',
            zone='central2-a',
            instance=name
            ),
        exception=HttpNotFoundError(None, None, None))

  def ExpectInstanceOperationCallWithHTTPNotFound(self, name, instance_op_name):
    self.mock_instance_client.zoneOperations.Wait.Expect(
        request=self.instances_messages.ComputeZoneOperationsWaitRequest(
            operation=instance_op_name,
            project=u'fake-project',
            zone=u'central2-a'),
        exception=HttpNotFoundError(None, None, None))

  def ExpectComputeImagesGetFamily(
      self, image_family, project, image_self_link):
    self.mock_instance_client.images.GetFromFamily.Expect(
        request=self.instances_messages.ComputeImagesGetFromFamilyRequest(
            family=image_family, project=project
            ),
        response=self.instances_messages.Image(selfLink=image_self_link),
        exception=None
        )

  def ExpectTensorflowVersionList(self, project, zone, want_versions):
    parent_ref = resources.REGISTRY.Parse(
        zone,
        params={'projectsId': project},
        collection='tpu.projects.locations')
    request = self.tpu_messages.TpuProjectsLocationsTensorflowVersionsListRequest(
        parent=parent_ref.RelativeName(),
        pageSize=100
        )
    tf_versions = []
    for want_version in want_versions:
      tf_versions.append(
          self.tpu_messages.TensorFlowVersion(
              name=want_version[0], version=want_version[1]))
    self.mock_tpu_client.projects_locations_tensorflowVersions.List.Expect(
        request=request,
        response=self.tpu_messages.ListTensorFlowVersionsResponse(
            nextPageToken=None,
            tensorflowVersions=tf_versions),
        exception=None)
