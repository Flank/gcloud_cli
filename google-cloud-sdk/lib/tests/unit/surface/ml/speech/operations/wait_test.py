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
"""gcloud ml speech operations wait unit tests."""

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.speech import base as speech_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class WaitTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech operations wait`."""

  def testWait(self, track):
    self.track = track
    self._ExpectPollOperationRequests('12345', attempts=1,
                                      results=['Hello world.'])
    result = self.Run('ml speech operations wait 12345')
    expected = {'@type': ('type.googleapis.com/google.cloud.speech.v1.'
                          'LongRunningRecognizeResponse'),
                'results': [{'alternatives': [{'confidence': 0.8,
                                               'transcript': 'Hello world.'}]}]}
    self.assertEqual(expected, resource_projector.MakeSerializable(result))

  def testWait_PollsOperation(self, track):
    self.track = track
    self._ExpectPollOperationRequests('12345', attempts=3,
                                      results=['Hello world.'])
    result = self.Run('ml speech operations wait 12345')
    expected = {'@type': ('type.googleapis.com/google.cloud.speech.v1.'
                          'LongRunningRecognizeResponse'),
                'results': [{'alternatives': [{'confidence': 0.8,
                                               'transcript': 'Hello world.'}]}]}
    self.assertEqual(expected, resource_projector.MakeSerializable(result))

  def testWait_Error(self, track):
    self.track = track
    error_json = {'code': 400, 'message': 'Error message.'}
    self._ExpectPollOperationRequests('12345', attempts=3,
                                      error_json=error_json)
    with self.assertRaises(waiter.OperationError):
      self.Run('ml speech operations wait 12345')


if __name__ == '__main__':
  test_case.main()
