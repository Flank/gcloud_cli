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

"""Base class for all gcloud ml video tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.video import util
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

from six.moves import range  # pylint: disable=redefined-builtin


class MlVideoTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for gcloud ml video command unit tests."""

  def _MockClients(self, video_api_version):
    """Creates mock client and adds Unmock on cleanup."""
    self.client = mock.Client(
        apis.GetClientClass(util.VIDEO_API, video_api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self._MockClients(util.VIDEO_API_VERSION)
    self.messages = apis.GetMessagesModule(
        util.VIDEO_API, util.VIDEO_API_VERSION)

    # shorten messages
    self.req_msg = (
        self.messages.GoogleCloudVideointelligenceV1AnnotateVideoRequest)
    self.context_msg = (
        self.messages.GoogleCloudVideointelligenceV1VideoContext)
    self.segment_msg = (
        self.messages.GoogleCloudVideointelligenceV1VideoSegment)
    self.detection_config = (
        self.messages.GoogleCloudVideointelligenceV1LabelDetectionConfig)
    self.label_detection_enum = (
        self.detection_config.LabelDetectionModeValueValuesEnum)
    self.feature_enum = self.req_msg.FeaturesValueListEntryValuesEnum

    # for waiting on operations
    self.StartPatch('time.sleep')

  def _GetResponseJsonForLabels(self, labels):
    """Build responses for the video client given a list of string labels.

    Args:
      labels: [str], the labels to be returned in the mocked response.

    Returns:
      (dict) a dict of results that can be substituted into the
        annotationResults field of the response.
    """
    response_json = []
    for label in labels:
      response_json.append(
          {
              'entity': {
                  'description': label,
                  'entityId': '/m/0jbk',
                  'languageCode': 'en-US'
              },
              'segments': [{
                  'confidence': 0.82209057,
                  'segment': {
                      'endTimeOffset': '100s',
                      'startTimeOffset': '0s'
                  }
              }]
          }
      )
    return {'segmentLabelAnnotations': response_json}

  def _GetOperationResponse(self, operation_id, results=None, error_json=None):
    """Helper function to build GoogleLongRunningOperation response."""
    if results:
      result = {
          'name': operation_id,
          'done': True,
          'response': {
              '@type': ('type.googleapis.com/google.cloud.videointelligence.'
                        'v1.AnnotateVideoResponse'),
              'annotationResults': results
          }
      }
      return encoding.PyValueToMessage(
          self.messages.GoogleLongrunningOperation,
          result)
    if error_json:
      result = {
          'name': operation_id,
          'done': True,
          'error': error_json
      }
      return encoding.PyValueToMessage(
          self.messages.GoogleLongrunningOperation,
          result)
    return self.messages.GoogleLongrunningOperation(name=operation_id)

  def ExpectWaitOperationRequest(self, operation_id, attempts=1,
                                 results=None, error_json=None):
    """Helper function to expect operations.Get polling.

    Either results or error_json should be given, but not both, depending
    on whether the operation completes successfully or not. If the final
    response should be an incomplete operation, both results and error_json
    should be None.

    Args:
      operation_id: str, the expected ID of the operation to request.
      attempts: int, the number of times to poll.
      results: [str] | None, a list of labels to return, if operation is
        expected to be completed successfully. Should be None if error_json
        is not None.
      error_json: dict | None, a json representation of expected error, if any.
        Should be None if results is not None.
    """
    for _ in range(0, attempts - 1):
      self.client.operations.Get.Expect(
          self.messages.VideointelligenceOperationsGetRequest(
              name=operation_id),
          self._GetOperationResponse(operation_id, results=None))
    self.client.operations.Get.Expect(
        self.messages.VideointelligenceOperationsGetRequest(
            name=operation_id),
        self._GetOperationResponse(operation_id, results=results,
                                   error_json=error_json))

  def ExpectAnnotateRequest(self, feature, input_uri=None, input_content=None,
                            output_uri=None, location_id=None,
                            segments=None, label_detection_mode=None,
                            operation_id=None):
    """Helper function to build expected Annotate request and response.

    Args:
      feature: messages.FeaturesValueListEntryValuesEnum, the feature to
        request.
      input_uri: str, the input URI for the expected request (if any).
      input_content: str, the video content to be directly put in the request
        (if any).
      output_uri: str, the output URI for the operation to write to (if any).
      location_id: str, the region where analysis should be requested (if any).
      segments: [str], list of video segments to add to request
      label_detection_mode: Label detection mode to add to label detection
        request.
      operation_id: str, the ID of the operation message to be returned.
    """
    config = (
        self.detection_config(labelDetectionMode=label_detection_mode)
        if label_detection_mode else None)
    if not segments and not config:
      context = None
    else:
      context = self.context_msg(
          segments=segments or [],
          labelDetectionConfig=config)
    self.client.videos.Annotate.Expect(
        request=self.req_msg(
            features=[feature],
            inputContent=input_content,
            inputUri=input_uri,
            outputUri=output_uri,
            locationId=location_id,
            videoContext=context),
        response=self.messages.GoogleLongrunningOperation(name=operation_id))
