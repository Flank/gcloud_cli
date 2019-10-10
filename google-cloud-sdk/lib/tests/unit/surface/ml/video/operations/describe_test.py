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
"""gcloud ml video operations describe unit tests."""

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
class DescribeTest(base.MlVideoTestBase):

  def SetUp(self):
    self.operation_name = ('projects/{}/locations/us-east1/operations/123'
                           .format(self.Project()))

  def testBasicOutput(self, track):
    """Test that command correctly outputs json of operation."""
    self.track = track
    self.ExpectWaitOperationRequest(self.operation_name)
    result = self.Run('ml video operations describe {}'.format(
        self.operation_name))
    self.AssertOutputEquals(textwrap.dedent("""\
    {
      "name": "%s"
    }
    """ % self.operation_name))
    self.assertEqual(result,
                     self.messages.GoogleLongrunningOperation(
                         name=self.operation_name))

  def testBasicOutputComplete(self, track):
    """Test that command correctly outputs json of results."""
    self.track = track
    self.ExpectWaitOperationRequest(
        self.operation_name,
        attempts=1,
        results=self._GetResponseJsonForLabels(['mug', 'coffee']))
    result = self.Run('ml video operations describe {}'.format(
        self.operation_name))
    self.AssertOutputContains(textwrap.dedent("""\
    {
      "done": true,
      "name": "%s",
      "response": {
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
    }
    """ % self.operation_name))
    results = []
    annotation_results = encoding.MessageToPyValue(
        result)['response']['annotationResults']['segmentLabelAnnotations']
    for r in annotation_results:
      results.append(r['entity']['description'])
    self.assertEqual(['mug', 'coffee'], results)

  def testError(self, track):
    """Test when operation contains an error."""
    self.track = track
    error_json = {'code': 400, 'message': 'Error message.'}
    self.ExpectWaitOperationRequest(self.operation_name, error_json=error_json)
    self.Run('ml video operations describe {}'.format(self.operation_name))
    self.AssertOutputEquals(textwrap.dedent("""\
    {
      "done": true,
      "error": {
        "code": 400,
        "message": "Error message."
      },
      "name": "%s"
    }
    """ % self.operation_name))


if __name__ == '__main__':
  test_case.main()
