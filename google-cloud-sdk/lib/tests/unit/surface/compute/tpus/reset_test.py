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
"""tpus reset tests."""
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class ResetTest(base.TpuUnitTestBase):

  def SetUp(self):
    self.zone = 'us-central1-c'
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.compute.zone.Set(self.zone)
    self.StartPatch('time.sleep')

  def testReset(self, track):
    self._SetTrack(track)
    reset_response = self.GetOperationResponse('reset')
    self.mock_client.projects_locations_nodes.Reset.Expect(
        self.messages.TpuProjectsLocationsNodesResetRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/reset'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.WriteInput('Y\n')
    self.assertEqual(self.Run('compute tpus reset mytpu'), reset_response)

  def testResetLongRunningOperation(self, track):
    self._SetTrack(track)
    # Reset Request
    reset_response = self.GetOperationResponse('reset')
    self.mock_client.projects_locations_nodes.Reset.Expect(
        self.messages.TpuProjectsLocationsNodesResetRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        reset_response
    )

    # Operation Polling Interval
    for _ in xrange(3):
      op_polling_response = self.GetOperationResponse('reset', is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name='projects/{0}/locations/{1}/operations/reset'.format(
                  self.Project(),
                  self.zone)),
          op_polling_response
      )

    # Operation Complete
    op_done_response = self.GetOperationResponse('reset', is_done=True)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/reset'.format(
                self.Project(),
                self.zone)),
        op_done_response
    )

    self.WriteInput('Y\n')
    self.assertEqual(self.Run('compute tpus reset mytpu'), reset_response)

  def testResetLongRunningOperationError(self, track):
    self._SetTrack(track)
    # Reset Request
    reset_response = self.GetOperationResponse('reset')
    self.mock_client.projects_locations_nodes.Reset.Expect(
        self.messages.TpuProjectsLocationsNodesResetRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        reset_response
    )

    # Operation Polling Interval
    for _ in xrange(3):
      op_polling_response = self.GetOperationResponse('reset', is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name='projects/{0}/locations/{1}/operations/reset'.format(
                  self.Project(),
                  self.zone)),
          op_polling_response
      )

    # Operation Error on Complete
    op_done_response = self.GetOperationResponse(
        'reset',
        is_done=True,
        error_json={'code': 400, 'message': 'Reset Failed.'}
    )

    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/reset'.format(
                self.Project(),
                self.zone)),
        op_done_response
    )

    self.WriteInput('Y\n')
    with self.assertRaisesRegexp(waiter.OperationError, r'Reset Failed.'):
      self.Run('compute tpus reset mytpu')

  def testResetWithZone(self, track):
    self._SetTrack(track)
    reset_response = self.GetOperationResponse('reset')
    self.mock_client.projects_locations_nodes.Reset.Expect(
        self.messages.TpuProjectsLocationsNodesResetRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/reset'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run(
            'compute tpus reset mytpu --zone {}'.format(self.zone)),
        reset_response)

  def testResetCancelled(self, track):
    self._SetTrack(track)
    self.WriteInput('N\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Reset aborted by user.'):
      self.Run('compute tpus reset mytpu')

  def testResetOutput(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    reset_response = self.GetOperationResponse('reset')
    self.mock_client.projects_locations_nodes.Reset.Expect(
        self.messages.TpuProjectsLocationsNodesResetRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/reset'.format(
                self.Project(),
                self.zone)),
        reset_response
    )
    self.WriteInput('Y\n')
    self.Run('compute tpus reset mytpu')
    self.AssertErrContains("""\
Your TPU [mytpu] will be reset.

Do you want to continue (Y/n)?
""", normalize_space=True)
    self.AssertErrContains('Waiting for [reset] to finish')
    self.AssertErrContains('Reset [mytpu].', normalize_space=True)


if __name__ == '__main__':
  test_case.main()
