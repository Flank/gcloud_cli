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

from __future__ import absolute_import
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ml.video import util
from tests.lib import cli_test_base


class VideoUtilTest(cli_test_base.CliTestBase):

  NAMESPACE = collections.namedtuple('Namespace', ['input_path'])

  def SetUp(self):
    messages = apis.GetMessagesModule(util.VIDEO_API, util.VIDEO_API_VERSION)
    self.request = messages.GoogleCloudVideointelligenceV1AnnotateVideoRequest()
    self.sample_file = self.Resource(
        'tests', 'unit', 'command_lib', 'ml', 'video', 'testdata', 'toy.mp4')

  def testValidateOutputURI(self):
    """Test that client validates and raises error for malformatted uri."""
    bad_uri = 'http://fakebucket/fakefile'
    expression = ('[http://fakebucket/fakefile] is not a valid format for '
                  'result output. Must be a Google Cloud Storage URI '
                  '(format: gs://bucket/file).')
    with self.AssertRaisesExceptionMatches(util.VideoUriFormatError,
                                           expression):
      util.ValidateOutputUri(bad_uri)

  def testValidateInputURI(self):
    """Test that client validates and raises error for malformatted uri."""
    bad_uri = 'http://fakebucket/fakefile'
    expression = ('[http://fakebucket/fakefile] is not a valid format for '
                  'video input. Must be a local path or a Google Cloud Storage '
                  'URI (format: gs://bucket/file).')
    with self.AssertRaisesExceptionMatches(util.VideoUriFormatError,
                                           expression):
      n = VideoUtilTest.NAMESPACE(input_path=bad_uri)
      util.UpdateRequestWithInput(None, n, self.request)

  def testGetContent_ContentFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    with open(self.sample_file, 'rb') as input_file:
      contents = input_file.read()
    n = VideoUtilTest.NAMESPACE(input_path=self.sample_file)
    util.UpdateRequestWithInput(None, n, self.request)
    self.assertEqual(self.request.inputContent, contents)

  def testGetContent_GCSFile(self):
    """Test client SingleFeatureAnnotate method with TextContentSource."""
    n = VideoUtilTest.NAMESPACE(input_path='gs://bucket/object')
    util.UpdateRequestWithInput(None, n, self.request)
    self.assertEqual(self.request.inputUri, 'gs://bucket/object')

  def testValidSegments(self):
    """Test segments are parsed."""
    segments = ['0:100', '200:300']  # Default Case
    segments_message = util.ValidateAndParseSegments(segments)
    self.assertEqual(2, len(segments_message))
    self.assertEqual(segments_message[0].startTimeOffset, '0.0s')
    self.assertEqual(segments_message[0].endTimeOffset, '0.0001s')
    self.assertEqual(segments_message[1].startTimeOffset, '0.0002s')
    self.assertEqual(segments_message[1].endTimeOffset, '0.0003s')
    self.AssertErrContains("WARNING: Time unit missing ('s', 'm','h') for "
                           "segment timestamp")

    segments = ['0:1m40s', '3m50s:600.2322s']
    segments_message = util.ValidateAndParseSegments(segments)
    self.assertEqual(2, len(segments_message))
    self.assertEqual(segments_message[0].startTimeOffset, '0.0s')
    self.assertEqual(segments_message[0].endTimeOffset, '100.0s')
    self.assertEqual(segments_message[1].startTimeOffset, '230.0s')
    self.assertEqual(segments_message[1].endTimeOffset, '600.2322s')

  def testInvalidSegments(self):
    """Test segments are parsed."""
    segments = ['0-100', '200-300']
    expected_msg = ('Could not get video segments from [0-100,200-300]. Please '
                    'make sure you give the desired segments in the form: '
                    'START1:END1,START2:END2, etc.')
    with self.AssertRaisesExceptionMatches(util.SegmentError, expected_msg):
      util.ValidateAndParseSegments(segments)

    segments = ['1', '200:300']
    expected_msg = ('[1,200:300]')
    with self.AssertRaisesExceptionMatches(util.SegmentError, expected_msg):
      util.ValidateAndParseSegments(segments)

    segments = ['100', '200', '300']
    expected_msg = ('[100,200,300]')
    with self.AssertRaisesExceptionMatches(util.SegmentError, expected_msg):
      util.ValidateAndParseSegments(segments)

    segments = ['0s:100s', '-5:5h500s']
    expected_msg = r'Could not get video segments from [0s:100s,-5:5h500s]'
    with self.AssertRaisesExceptionMatches(util.SegmentError, expected_msg):
      util.ValidateAndParseSegments(segments)

    segments = ['0s:100s', '400s:-500s']
    expected_msg = r'Could not get video segments from [0s:100s,400s:-500s]'
    with self.AssertRaisesExceptionMatches(util.SegmentError, expected_msg):
      util.ValidateAndParseSegments(segments)


if __name__ == '__main__':
  cli_test_base.main()
