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
"""gcloud ml video operations describe unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.video import base


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA),
    ('GA', calliope_base.ReleaseTrack.GA))
class WaitTest(base.MlVideoTestBase):

  def testBasicOutputComplete(self, track):
    """Test that command correctly outputs json of results."""
    self.track = track
    self.ExpectWaitOperationRequest(
        '123',
        attempts=3,
        results=self._GetResponseJsonForLabels(['mug', 'coffee']))
    result = self.Run('ml video operations wait 123')
    self.AssertErrContains('Waiting for operation [123] to complete')
    self.AssertOutputContains(textwrap.dedent("""\
    {
      "@type": "type.googleapis.com/google.cloud.videointelligence.v1.AnnotateVideoResponse",
      "annotationResults": {
        "segmentLabelAnnotations": [
          {
            "entity": {
              "description": "mug",
              "entityId": "/m/0jbk",
              "languageCode": "en-US"
            },
            "segments": [
              {
                "confidence": 0.82209057,
                "segment": {
                  "endTimeOffset": "100s",
                  "startTimeOffset": "0s"
                }
              }
            ]
          },
          {
            "entity": {
              "description": "coffee",
              "entityId": "/m/0jbk",
              "languageCode": "en-US"
            },
            "segments": [
              {
                "confidence": 0.82209057,
                "segment": {
                  "endTimeOffset": "100s",
                  "startTimeOffset": "0s"
                }
              }
            ]
          }
        ]
      }
    }
    """))
    annotation_results = encoding.MessageToPyValue(
        result)['annotationResults']['segmentLabelAnnotations']
    self.assertEqual(
        ['mug', 'coffee'],
        [r['entity']['description']
         for r in annotation_results])

  def testError(self, track):
    """Test when operation contains an error."""
    self.track = track
    error_json = {'code': 400, 'message': 'Error message.'}
    self.ExpectWaitOperationRequest('123', attempts=3, error_json=error_json)
    with self.assertRaisesRegex(waiter.OperationError, 'Error message.'):
      self.Run('ml video operations wait 123')


if __name__ == '__main__':
  test_case.main()
