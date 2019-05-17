# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the ML Predict library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.ml_engine import predict
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import resources
from googlecloudsdk.core.credentials import http as cred_http
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class PredictTestBase(object):

  _BASE_URL = 'https://ml.googleapis.com/v1/'

  def SetUp(self):
    self.mock_http = self.StartObjectPatch(http, 'Http').return_value
    self.StartObjectPatch(cred_http, 'Http').return_value = self.mock_http
    self.http_response = {'status': '200'}
    self.http_body = '{"predictions": [{"prediction": 1}, {"prediction": 2}]}'
    self.test_instances = [{'images': [0, 1], 'key': 3}]
    self.expected_body = '{"instances": [{"images": [0, 1], "key": 3}]}'
    self.version_ref = resources.REGISTRY.Create('ml.projects.models.versions',
                                                 projectsId=self.Project(),
                                                 modelsId='my_model',
                                                 versionsId='v1')
    self.model_ref = resources.REGISTRY.Create('ml.projects.models',
                                               projectsId=self.Project(),
                                               modelsId='my_model')

  def testPredictJsonInstances(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    result = predict.Predict(self.version_ref, self.test_instances)

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model/versions/v1:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url, method=method, body=self.expected_body, headers=headers)
    self.assertEqual(json.loads(self.http_body), result)

  def testPredictMultipleJsonInstances(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    test_instances = [{
        'images': [0, 1],
        'key': 3
    }, {
        'images': [2, 3],
        'key': 2
    }, {
        'images': [3, 1],
        'key': 1
    }]
    result = predict.Predict(self.version_ref, test_instances)

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model/versions/v1:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url,
        method=method,
        body=('{"instances": [{"images": [0, 1], "key": 3}, '
              '{"images": [2, 3], "key": 2}, '
              '{"images": [3, 1], "key": 1}]}'),
        headers=headers)
    self.assertEqual(json.loads(self.http_body), result)

  def testPredictNoVersion(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    result = predict.Predict(self.model_ref, self.test_instances)

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url, method=method, body=self.expected_body, headers=headers)
    self.assertEqual(json.loads(self.http_body), result)

  def testPredictInvalidResponse(self):
    invalid_http_body = 'abcd'  # invalid json dump
    self.mock_http.request.return_value = [self.http_response,
                                           invalid_http_body]

    with self.assertRaisesRegex(core_exceptions.Error,
                                'No JSON object could be decoded from the '
                                'HTTP response body: abcd'):
      predict.Predict(self.version_ref, self.test_instances)

  def testPredictFailedRequest(self):
    failed_response = {'status': '502'}
    failed_response_body = 'Error 502'
    self.mock_http.request.return_value = [failed_response,
                                           failed_response_body]

    with self.assertRaisesRegex(core_exceptions.Error,
                                'HTTP request failed. Response: Error 502'):
      predict.Predict(self.version_ref, self.test_instances)

  def testPredictTextInstances(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    result = predict.Predict(self.version_ref, ['2, 3'])

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model/versions/v1:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url, method=method, body='{"instances": ["2, 3"]}', headers=headers)
    self.assertEqual(json.loads(self.http_body), result)

  def testPredictTextInstancesWithJSON(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    result = predict.Predict(
        self.version_ref,
        instances=['{"images": [0, 1], "key": 3}',
                   '{"images": [0.3, 0.2], "key": 2}',
                   '{"images": [0.2, 0.1], "key": 1}'])

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model/versions/v1:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url,
        method=method,
        body=('{"instances": ["{\\"images\\": [0, 1], \\"key\\": 3}", '
              '"{\\"images\\": [0.3, 0.2], \\"key\\": 2}", '
              '"{\\"images\\": [0.2, 0.1], \\"key\\": 1}"]}'),
        headers=headers)
    self.assertEqual(json.loads(self.http_body), result)

  def testPredictNonUtf8Instances(self):
    with self.assertRaisesRegex(core_exceptions.Error,
                                'Instances cannot be JSON encoded'):
      predict.Predict(self.version_ref, [b'\x89PNG'])

  def testPredictionSignatureName(self):
    self.mock_http.request.return_value = [self.http_response, self.http_body]

    result = predict.Predict(self.version_ref, ['2, 3'],
                             signature_name='my-custom-signature')

    url = (self._BASE_URL + 'projects/fake-project/'
           'models/my_model/versions/v1:predict')
    method = 'POST'
    headers = {'Content-Type': 'application/json'}

    self.mock_http.request.assert_called_once_with(
        uri=url, method=method,
        body='{"instances": ["2, 3"], "signature_name": "my-custom-signature"}',
        headers=headers)
    self.assertEqual(json.loads(self.http_body), result)


class PredictGaTest(PredictTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(PredictGaTest, self).SetUp()


class PredictBetaTest(PredictTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(PredictBetaTest, self).SetUp()

if __name__ == '__main__':
  test_case.main()
