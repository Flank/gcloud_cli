# -*- coding: utf-8 -*- #

# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.app.api.requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import requests
from tests.lib import test_case


class RequestsTest(test_case.TestCase):

  def testExtractErrorMessageBlank(self):
    error = {}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual('Error Response: [UNKNOWN] ', message)

  def testExtractErrorMessageSimple(self):
    error = {'code': 8, 'message': 'error message'}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual('Error Response: [8] error message', message)

  def testExtractErrorMessageUrl(self):
    error = {'code': 8,
             'message': 'error message',
             'url': 'http://example.com'}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual('Error Response: [8] error message\nhttp://example.com',
                     message)

  def testExtractErrorMessageDetails(self):
    error = {'code': 8,
             'message': 'error message',
             'details': {'data': 'data'}}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual(
        ('Error Response: [8] error message\n\n'
         'Details: [\n  {\n    "data": "data"\n  }\n]\n'), message)

  def testExtractErrorMessageUrlAndDetails(self):
    error = {'code': 8,
             'message': 'error message',
             'url': 'http://example.com',
             'details': {'data': 'data'}}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual(
        ('Error Response: [8] error message\n'
         'http://example.com\n\n'
         'Details: [\n  {\n    "data": "data"\n  }\n]\n'), message)

  def testExtractErrorMessageUrlAndDetailsUnicode(self):
    error = {'code': 8,
             'message': 'error Ṳᾔḯ¢◎ⅾℯ',
             'url': 'http://example.com/Ṳᾔḯ¢◎ⅾℯ',
             'details': {'data': 'Ṳᾔḯ¢◎ⅾℯ'}}
    message = requests.ExtractErrorMessage(error)
    self.assertEqual(
        ('Error Response: [8] error Ṳᾔḯ¢◎ⅾℯ\n'
         'http://example.com/Ṳᾔḯ¢◎ⅾℯ\n\n'
         'Details: [\n  {\n    "data": "Ṳᾔḯ¢◎ⅾℯ"\n  }\n]\n'), message)


if __name__ == '__main__':
  test_case.main()
