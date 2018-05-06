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

"""gcloud ml speech operations describe unit tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.speech import base as speech_base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class DescribeTest(speech_base.MlSpeechTestBase):
  """Class to test `gcloud ml speech operations describe`."""

  def testDescribeOperation(self, track):
    """Test that describe operation command returns operation."""
    self.SetUpForTrack(track)
    self._ExpectGetOperationRequest('12345')
    result = self.Run('ml speech operations describe 12345')
    self.assertEqual(result, self.messages.Operation(name='12345'))


if __name__ == '__main__':
  test_case.main()
