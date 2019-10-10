# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for the Run flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.run import exceptions
from tests.lib import test_case


DEFAULT_URL = 'http://google.com/cloud/foo/bar'


class KubernetesExceptionParserTest(test_case.TestCase):

  def NewKubernetesExceptionParser(
      self, response_dict, content_dict, url=DEFAULT_URL):
    http_error = apitools_exceptions.HttpError(
        response_dict, json.dumps(content_dict), url)
    return exceptions.KubernetesExceptionParser(http_error)

  def testStatusCode(self):
    e = self.NewKubernetesExceptionParser({'status': 200}, {})
    self.assertEqual(e.status_code, 200)

  def testStatusCodeMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.status_code, None)

  def testUrl(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.url, DEFAULT_URL)

  def testApiVersion(self):
    e = self.NewKubernetesExceptionParser({}, {'apiVersion': 'v1alpha1'})
    self.assertEqual(e.api_version, 'v1alpha1')

  def testApiVersionMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.api_version, None)

  def testApiName(self):
    e = self.NewKubernetesExceptionParser({}, {'details': {'group': 'sue'}})
    self.assertEqual(e.api_name, 'sue')

  def testApiNameMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.api_name, None)

    e = self.NewKubernetesExceptionParser({}, {'details': {}})
    self.assertEqual(e.api_name, None)

  def testResourceName(self):
    e = self.NewKubernetesExceptionParser({}, {'details': {'name': 'bill'}})
    self.assertEqual(e.resource_name, 'bill')

  def testResourceNameMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.resource_name, None)

    e = self.NewKubernetesExceptionParser({}, {'details': {}})
    self.assertEqual(e.resource_name, None)

  def testResourceKind(self):
    e = self.NewKubernetesExceptionParser({}, {'details': {'kind': 'alpha'}})
    self.assertEqual(e.resource_kind, 'alpha')

  def testResourceKindMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.resource_kind, None)

    e = self.NewKubernetesExceptionParser({}, {'details': {}})
    self.assertEqual(e.resource_kind, None)

  def testDefaultMessage(self):
    e = self.NewKubernetesExceptionParser({}, {'message': 'hI pAl'})
    self.assertEqual(e.default_message, 'hI pAl')

  def testDefaultMessageMissing(self):
    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.default_message, None)

  def testCauses(self):
    causes = [
        {'message': 'bb', 'info': 'bbi'},
        {'message': 'aa', 'info': 'aai'}]
    e = self.NewKubernetesExceptionParser(
        {}, {'details': {'causes': causes}})
    self.assertEqual(
        e.causes,
        [
            {'message': 'aa', 'info': 'aai'},
            {'message': 'bb', 'info': 'bbi'},
        ])

  def testCausesMissing(self):
    e = self.NewKubernetesExceptionParser({}, {'details': {'causes': []}})
    self.assertEqual(e.causes, [])

    e = self.NewKubernetesExceptionParser({}, {'details': {}})
    self.assertEqual(e.causes, [])

    e = self.NewKubernetesExceptionParser({}, {})
    self.assertEqual(e.causes, [])
