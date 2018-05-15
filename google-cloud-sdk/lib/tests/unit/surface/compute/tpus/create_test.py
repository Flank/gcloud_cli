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
"""tpus Create tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class CreateTest(base.TpuUnitTestBase):

  def _GetNodeResponseValue(self, node):
    return encoding.JsonToMessage(
        self.messages.Operation.ResponseValue,
        encoding.MessageToJson(node))

  def GetParent(self, project=None, zone=None):
    project = project or self.Project()
    zone = zone or self.zone
    return 'projects/{0}/locations/{1}'.format(project, zone)

  def SetUp(self):
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)
    self.create_op_ref = resources.REGISTRY.Parse(
        'create',
        params={
            'projectsId': self.Project(),
            'locationsId': self.zone},
        collection='tpu.projects.locations.operations')
    self.StartPatch('time.sleep')

  def testCreateWithDefaults(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    node = self.messages.Node(cidrBlock='10.20.10.0/29',
                              acceleratorType='v2-8',
                              network='my-tf-network',
                              tensorflowVersion='1.6')
    create_response = self.GetOperationResponse(
        self.create_op_ref.RelativeName())
    create_response.response = self._GetNodeResponseValue(node)
    create_request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        node=node, nodeId='mytpu', parent=self.GetParent())

    self.mock_client.projects_locations_nodes.Create.Expect(
        request=create_request,
        response=create_response
    )

    op_done_response = self.ExpectLongRunningOpResult(
        'create',
        response_value=create_response.response
    )

    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run('compute tpus create mytpu --range 10.20.10.0/29 '
                 '--network my-tf-network --version 1.6'),
        op_done_response.response
    )

  def testCreateWithCustParams(self, track):
    self._SetTrack(track)
    node = self.messages.Node(
        cidrBlock='10.240.0.0/29',
        description='My TF Node',
        network='my-tf-network',
        tensorflowVersion='1.6',
        acceleratorType='v2-8',
    )

    create_response = self.GetOperationResponse(
        self.create_op_ref.RelativeName())
    create_response.response = self._GetNodeResponseValue(node)
    create_request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        node=node, nodeId='mytpu', parent=self.GetParent())

    self.mock_client.projects_locations_nodes.Create.Expect(
        request=create_request,
        response=create_response
    )

    op_done_response = self.ExpectLongRunningOpResult(
        'create',
        response_value=create_response.response
    )

    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run("""\
        compute tpus create mytpu --zone us-central1-c --range 10.240.0.0/29 \
    --accelerator-type 'v2-8' --network my-tf-network  --version '1.6' \
    --description 'My TF Node'
        """),
        op_done_response.response
    )

  def testCreateWithCustomAcceleratorType(self, track):
    self._SetTrack(track)
    node = self.messages.Node(
        cidrBlock='10.240.0.0/29',
        description='My TF Node',
        network='my-tf-network',
        tensorflowVersion='1.6',
        acceleratorType='v2-8',
    )

    create_response = self.GetOperationResponse(
        self.create_op_ref.RelativeName())
    create_response.response = self._GetNodeResponseValue(node)
    create_request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        node=node, nodeId='mytpu', parent=self.GetParent())

    self.mock_client.projects_locations_nodes.Create.Expect(
        request=create_request,
        response=create_response
    )

    op_done_response = self.ExpectLongRunningOpResult(
        'create',
        response_value=create_response.response
    )

    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run("""\
        compute tpus create mytpu --zone us-central1-c --range 10.240.0.0/29 \
    --accelerator-type 'v2-8' --network my-tf-network  --version '1.6' \
    --description 'My TF Node'
        """),
        op_done_response.response
    )

  def testCreateDefaultOutput(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    node = self.messages.Node(cidrBlock='10.20.10.0/29',
                              acceleratorType='v2-8',
                              network='my-tf-network',
                              tensorflowVersion='1.6')
    create_response = self.GetOperationResponse(
        self.create_op_ref.RelativeName())
    create_response.response = self._GetNodeResponseValue(node)
    create_request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        node=node, nodeId='mytpu', parent=self.GetParent())

    self.mock_client.projects_locations_nodes.Create.Expect(
        request=create_request,
        response=create_response
    )

    self.ExpectLongRunningOpResult(
        'create',
        response_value=create_response.response
    )

    self.WriteInput('Y\n')
    self.Run('compute tpus create mytpu --range 10.20.10.0/29 --version 1.6 '
             '--network my-tf-network')
    self.AssertErrMatches(r'Waiting for operation \[.*create\] to complete')
    self.AssertErrContains('Created tpu [mytpu].')

  def testCreateFailed(self, track):
    self._SetTrack(track)
    node = self.messages.Node(cidrBlock='10.20.10.0/29',
                              acceleratorType='v2-8',
                              network='my-tf-network',
                              tensorflowVersion='1.6')
    create_response = self.GetOperationResponse(
        self.create_op_ref.RelativeName())
    create_response.response = self._GetNodeResponseValue(node)
    create_request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        node=node, nodeId='mytpu', parent=self.GetParent())

    self.mock_client.projects_locations_nodes.Create.Expect(
        request=create_request,
        response=create_response
    )

    self.ExpectLongRunningOpResult(
        'create',
        response_value=create_response.response,
        error_json={'code': 500, 'message': 'Create Failed.'}
    )

    self.WriteInput('Y\n')
    with self.assertRaisesRegex(waiter.OperationError, r'Create Failed.'):
      self.Run('compute tpus create mytpu --range 10.20.10.0/29 --version 1.6'
               ' --network my-tf-network')


if __name__ == '__main__':
  test_case.main()
