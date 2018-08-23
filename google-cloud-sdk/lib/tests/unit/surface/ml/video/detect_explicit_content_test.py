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

"""gcloud ml video detect-explicit-content unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.video import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class DetectExplicitContentTest(base.MlVideoTestBase):

  def _GetResponseJsonExplicitContent(self, findings):
    """Build responses for the client from list of explicit content findings.

    Args:
      findings: [str], the explicit content findings to be returned in the
        mocked response, in the form of a list of timeoffset duration strings.

    Returns:
      (dict) a dict of results that can be substituted into the
        annotationResults field of the response.
    """
    response_json = []
    for offset in findings:
      response_json.append(
          {
              'pornographyLikelihood': 'UNLIKELY',
              'timeOffset': '{}'.format(offset)
          }
      )
    return [{'explicitAnnotation': {'frames': response_json}}]

  def _InitTest(self, track):
    """Pseudo SetUp method for use with parameterized tests."""
    self.track = track
    self.feature = self.feature_enum.EXPLICIT_CONTENT_DETECTION

  def testBasicOutputAsync(self, track):
    """Test that command correctly outputs json of operation."""
    self._InitTest(track)
    self.ExpectAnnotateRequest(
        self.feature,
        input_uri='gs://bucket/object',
        operation_id='10000')
    self.Run('ml video detect-explicit-content gs://bucket/object --async')
    self.AssertOutputEquals(textwrap.dedent("""\
    {
      "name": "10000"
    }
    """))

  def testBasicOutputComplete(self, track):
    """Test that command correctly outputs json of results."""
    self._InitTest(track)
    self.ExpectAnnotateRequest(
        self.feature,
        input_uri='gs://bucket/object',
        operation_id='10000')
    self.ExpectWaitOperationRequest(
        operation_id='10000',
        attempts=3,
        results=self._GetResponseJsonExplicitContent(
            ['0.456s', '13.006s', '14.5s']))
    self.Run('ml video detect-explicit-content gs://bucket/object')
    self.AssertErrContains('Waiting for operation [10000] to complete')
    self.AssertOutputContains(textwrap.dedent("""\
    {
      "@type": "type.googleapis.com/google.cloud.videointelligence.v1.AnnotateVideoResponse",
      "annotationResults": [
        {
          "explicitAnnotation": {
            "frames": [
              {
                "pornographyLikelihood": "UNLIKELY",
                "timeOffset": "0.456s"
              },
              {
                "pornographyLikelihood": "UNLIKELY",
                "timeOffset": "13.006s"
              },
              {
                "pornographyLikelihood": "UNLIKELY",
                "timeOffset": "14.5s"
              }
            ]
          }
        }
      ]
    }
    """))

  def testBasicResultAsync(self, track):
    """Test that results return correctly."""
    self._InitTest(track)
    self.ExpectAnnotateRequest(
        self.feature,
        input_uri='gs://bucket/object',
        operation_id='10000')
    result = self.Run(
        'ml video detect-explicit-content gs://bucket/object --async')
    self.assertEqual(
        result, self.messages.GoogleLongrunningOperation(
            name='10000'))

  def testBasicResultComplete(self, track):
    """Test that results return correctly with operation polling."""
    self._InitTest(track)
    self.ExpectAnnotateRequest(
        self.feature,
        input_uri='gs://bucket/object',
        operation_id='10000')
    self.ExpectWaitOperationRequest(
        operation_id='10000',
        attempts=3,
        results=self._GetResponseJsonExplicitContent(
            ['0.456s', '13.006s', '14.5s']))
    result = self.Run('ml video detect-explicit-content gs://bucket/object')
    annotation_result = encoding.MessageToPyValue(
        result)['annotationResults'][0]['explicitAnnotation']
    self.assertEqual(
        ['0.456s', '13.006s', '14.5s'],
        [r['timeOffset'] for r in annotation_result['frames']])

  def testWithFlags(self, track):
    """Test that flags correctly modify the request."""
    self._InitTest(track)

    self.ExpectAnnotateRequest(
        self.feature,
        input_uri='gs://bucket/object',
        output_uri='gs://bucket/output',
        segments=[
            self.segment_msg(startTimeOffset='0.0s', endTimeOffset='100.0s'),
            self.segment_msg(startTimeOffset='400.0s', endTimeOffset='500.0s')],
        location_id='us-east1',
        operation_id='123'
    )
    result = self.Run('ml video detect-explicit-content gs://bucket/object '
                      '--output-uri gs://bucket/output '
                      '--segments 0s:100s,400s:500s '
                      '--region us-east1 '
                      '--async')
    self.assertEqual(
        self.messages.GoogleLongrunningOperation(name='123'),
        result)

  def testLocalVideo(self, track):
    """Test that the command correctly sends contents of local file."""
    self._InitTest(track)
    video_path = self.Touch(
        self.root_path, name='videofile', contents=b'video content')
    self.ExpectAnnotateRequest(
        self.feature,
        input_content=b'video content',
        operation_id='10000'
    )
    result = self.Run(
        'ml video detect-explicit-content {} --async'.format(video_path))
    self.assertEqual(
        self.messages.GoogleLongrunningOperation(name='10000'),
        result)


if __name__ == '__main__':
  test_case.main()
