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
"""Tests of the 'import' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import admin_api
from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.datastore import base
import six.moves.http_client


class ImportTest(base.DatastoreCommandUnitTest):
  """Tests the datastore import command."""

  def testImport(self):
    input_url = 'gs://gcs_bucket/gcs_object'
    expected_request = admin_api.GetImportEntitiesRequest(
        self.Project(), input_url)

    operation_name = 'import operation name'
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Import.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(input_url=input_url)
    self.assertEqual(operation_name, actual.name)

  def testInputUrlConversion(self):
    self.AssertValidInputUrl('b/gcs_bucket/o/gcs_object')
    self.AssertValidInputUrl('gs://gcs_bucket/gcs_object')
    self.AssertValidInputUrl(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket/o/gcs_object')
    self.AssertValidInputUrl('b/foo/o/bar', 'gs://foo/bar')
    # No object
    self.AssertInvalidInputUrl('gs://gcs_bucket')
    # Other reference
    self.AssertInvalidInputUrl(
        'https://www.googleapis.com/datastore/v1/projects/foo/operations/bar')

  def testImportWithEntitySpecAndLabels(self):
    input_url = 'gs://gcs_bucket/gcs_file'
    labels = {'a_key': 'a_value', 'b_key': 'b_value'}
    kinds = ['Customer', 'Orders']
    namespaces = ['APAC', 'EMEA', '(default)']
    expected_namespaces = ['APAC', 'EMEA', '']
    expected_request = admin_api.GetImportEntitiesRequest(
        self.Project(),
        input_url,
        labels=labels,
        kinds=kinds,
        namespaces=expected_namespaces)

    operation_name = 'import operation name'
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Import.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(
        labels=labels, kinds=kinds, namespaces=namespaces, input_url=input_url)
    self.assertEqual(operation_name, actual.name)

  def testImportFailureThrowsToolHttpException(self):
    input_url = 'gs://gcs_bucket/gcs_file'
    request = admin_api.GetImportEntitiesRequest(self.Project(), input_url)

    exception = http_error.MakeHttpError(
        six.moves.http_client.BAD_REQUEST, 'error_message', url='fake url')

    self.mock_datastore_v1.projects.Import.Expect(request, exception=exception)

    with self.assertRaisesRegex(exceptions.HttpException, 'error_message'):
      self.RunImportTest(input_url=input_url)

  def RunImportTest(self,
                    labels=None,
                    kinds=None,
                    namespaces=None,
                    input_url=''):
    return self.RunDatastoreTest('import --async {} {} {} {}'.format(
        '--operation-labels={}'.format(self.Serialize(labels))
        if labels else '', '--kinds={}'.format(self.Serialize(kinds))
        if kinds else '', '--namespaces={}'.format(self.Serialize(namespaces))
        if namespaces else '', input_url))

  def AssertValidInputUrl(self,
                          input_url,
                          expected_location='gs://gcs_bucket/gcs_object'):
    expected_request = admin_api.GetImportEntitiesRequest(
        self.Project(), expected_location)

    operation_name = 'import operation name'
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Import.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(input_url=input_url)
    self.assertEqual(operation_name, actual.name)

  def AssertInvalidInputUrl(self, input_url):
    with self.assertRaises(resources.UserError):
      self.RunImportTest(input_url=input_url)


if __name__ == '__main__':
  test_case.main()
