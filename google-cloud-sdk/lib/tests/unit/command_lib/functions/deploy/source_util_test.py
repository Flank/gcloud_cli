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
"""Test of the functions surface deploy.source_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import http_wrapper
from apitools.base.py import transfer

from googlecloudsdk.command_lib.functions.deploy import source_util
from googlecloudsdk.core import http as http_utils
from tests.lib import test_case
from tests.lib.surface.functions import base
import mock
from mock import Mock

import six
from six.moves import http_client


class UploadFileTest(base.FunctionsTestBase):

  class TestFunctionRef:

    def __init__(self, projectsId, locationsId):
      self.projectsId = projectsId  # pylint: disable=invalid-name
      self.locationsId = locationsId  # pylint: disable=invalid-name

  def SetUp(self):
    self.mock_http_client = Mock()
    self.mock_http_client.redirect_codes = []
    self.mock_http_client.connections = {}

    self.test_location = 'projects/{}/locations/{}'.format(
        self.Project(), self.GetRegion())
    self.function_ref = self.TestFunctionRef(self.Project(), self.GetRegion())
    self.upload_url = 'http://www.uploads.com'
    self.success_response = http_wrapper.Response(
        info={
            'status': http_client.OK,
            'location': self.upload_url
        },
        content='',
        request_url=self.upload_url)

  def _FakeUpload(self):
    self.sample_data = b'abc' * 30
    self.sample_stream = six.BytesIO(self.sample_data)
    return transfer.Upload(
        stream=self.sample_stream,
        mime_type='text/plain',
        total_size=len(self.sample_data),
        close_stream=False,
        gzip_encoded=True)

  def testUploadFileToGeneratedUrl_OnSuccess_ReturnsTheUrl(self):
    self.mock_client.projects_locations_functions.GenerateUploadUrl.Expect(
        self.messages
        .CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest(
            parent=self.test_location, generateUploadUrlRequest=None),
        self.messages.GenerateUploadUrlResponse(uploadUrl=self.upload_url))
    with mock.patch.object(transfer.Upload, 'FromFile') as mock_result:
      with mock.patch.object(http_wrapper, 'MakeRequest') as make_request:
        source = 'fake source'
        mock_result.return_value = self._FakeUpload()
        make_request.return_value = self.success_response

        generated_url = source_util.UploadFile(
            source, None, self.messages,
            self.mock_client.projects_locations_functions, self.function_ref)
        self.assertEqual(generated_url, self.upload_url)

  def testUploadFileToGeneratedUrl_OnPermissionPropagationDelay_Retries(self):
    permission_propagation_delayed_response = http_wrapper.Response(
        info={
            'status': http_client.FORBIDDEN,
            'location': self.upload_url
        },
        content='service-123@gcf-admin-robot.iam.gserviceaccount.com does not have storage.objects.create access to gcf-bucket/upload.zip.',
        request_url=self.upload_url)
    self.mock_client.projects_locations_functions.GenerateUploadUrl.Expect(
        self.messages
        .CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest(
            parent=self.test_location, generateUploadUrlRequest=None),
        self.messages.GenerateUploadUrlResponse(uploadUrl=self.upload_url))

    with mock.patch.object(transfer.Upload, 'FromFile') as mock_result, \
      mock.patch.object(http_utils, 'Http', return_value=self.mock_http_client), \
          mock.patch.object(self.mock_http_client, 'request') as make_request:
      source = 'fake source'
      mock_result.return_value = self._FakeUpload()
      make_request.side_effect = [[
          permission_propagation_delayed_response.info,
          permission_propagation_delayed_response.content
      ], [self.success_response.info, self.success_response.content]]

      source_util.UploadFile(source, None, self.messages,
                             self.mock_client.projects_locations_functions,
                             self.function_ref)
      self.assertEqual(2, make_request.call_count)


if __name__ == '__main__':
  test_case.main()
