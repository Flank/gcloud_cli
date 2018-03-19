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
"""Tests of the 'export' command."""

import httplib

from googlecloudsdk.api_lib.datastore import admin_api
from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.datastore import base


class ExportTest(base.DatastoreCommandUnitTest, sdk_test_base.WithLogCapture):
  """Tests the datastore export command."""

  def testExport(self):
    output_url_prefix = 'gs://gcs_bucket'
    expected_request = admin_api.GetExportEntitiesRequest(
        self.Project(), output_url_prefix)
    operation_name = 'export operation name'
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Export.Expect(
        expected_request, response=mock_response)

    resp = self.RunExportTest(output_url_prefix=output_url_prefix)
    self.assertEqual(operation_name, resp.name)

  def testExportNonAsync(self):
    output_url_prefix = 'gs://gcs_bucket'
    expected_request = admin_api.GetExportEntitiesRequest(
        self.Project(), output_url_prefix)
    operation_name = 'projects/{}/operations/exportoperationname'.format(
        self.Project())
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)
    expected_operation_get = (
        operations.GetMessages().DatastoreProjectsOperationsGetRequest())
    expected_operation_get.name = operation_name

    # Expect several calls while done=False, then we get a response from the
    # command once the export is complete.
    self.mock_datastore_v1.projects.Export.Expect(
        expected_request, response=mock_response)
    self.mock_datastore_v1.projects_operations.Get.Expect(
        expected_operation_get, response=mock_response)
    self.mock_datastore_v1.projects_operations.Get.Expect(
        expected_operation_get, response=mock_response)

    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=True, name=operation_name)

    self.mock_datastore_v1.projects_operations.Get.Expect(
        expected_operation_get, response=mock_response)

    # Call RunDatastoreTest directly, because we don't want --async.
    resp = self.RunDatastoreTest('export {}'.format(output_url_prefix))

    self.assertEqual(operation_name, resp.name)
    self.AssertErrContains('Waiting for [{}] to finish'.format(operation_name))

  def testExportWithEntitySpecAndLabels(self):
    output_url_prefix = 'gs://gcs_bucket'
    labels = {'a_key': 'a_value', 'b_key': 'b_value'}
    kinds = ['Customer', 'Orders']
    namespaces = ['APAC', 'EMEA', '(default)']
    expected_namespaces = ['APAC', 'EMEA', '']
    request = admin_api.GetExportEntitiesRequest(
        self.Project(),
        output_url_prefix,
        labels=labels,
        kinds=kinds,
        namespaces=expected_namespaces)

    operation_name = 'export operation name'
    response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Export.Expect(request, response=response)

    actual = self.RunExportTest(
        labels=labels,
        kinds=kinds,
        namespaces=namespaces,
        output_url_prefix=output_url_prefix)
    self.assertEqual(operation_name, actual.name)

  def testExportFailureThrowsToolHttpException(self):
    output_url_prefix = 'gs://gcs_bucket'
    request = admin_api.GetExportEntitiesRequest(self.Project(),
                                                 output_url_prefix)

    exception = http_error.MakeHttpError(
        httplib.BAD_REQUEST, 'error_message', url='Fake url')

    self.mock_datastore_v1.projects.Export.Expect(request, exception=exception)

    with self.assertRaisesRegexp(exceptions.HttpException, 'error_message'):
      self.RunExportTest(output_url_prefix=output_url_prefix)

  def testOutputUrlPrefixConversion(self):
    self.AssertValidOutputUrlPrefix('gs://gcs_bucket')
    self.AssertValidOutputUrlPrefix('gcs_bucket')
    self.AssertValidOutputUrlPrefix('b/gcs_bucket')
    self.AssertValidOutputUrlPrefix(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket')
    self.AssertValidOutputUrlPrefix('b/foobar', 'gs://foobar')
    self.AssertValidOutputUrlPrefix('gs://gcs_bucket/gcs_object_prefix',
                                    'gs://gcs_bucket/gcs_object_prefix')
    self.AssertValidOutputUrlPrefix(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket/o/gcs_object_prefix',  # pylint: disable=line-too-long
        'gs://gcs_bucket/gcs_object_prefix')
    # Other resource
    self.AssertInvalidOutputUrlPrefix(
        'https://www.googleapis.com/datastore/v1/projects/foo/operations/bar')

  def RunExportTest(self,
                    labels=None,
                    kinds=None,
                    namespaces=None,
                    output_url_prefix=''):
    return self.RunDatastoreTest('export --async {} {} {} {}'.format(
        '--operation-labels={}'.format(self.Serialize(labels))
        if labels else '', '--kinds={}'.format(self.Serialize(kinds))
        if kinds else '', '--namespaces={}'.format(self.Serialize(namespaces))
        if namespaces else '', output_url_prefix))

  def AssertValidOutputUrlPrefix(self,
                                 output_url_prefix,
                                 expected='gs://gcs_bucket'):
    expected_request = admin_api.GetExportEntitiesRequest(
        self.Project(), expected)
    operation_name = 'export operation name'
    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_datastore_v1.projects.Export.Expect(
        expected_request, response=mock_response)

    resp = self.RunExportTest(output_url_prefix=output_url_prefix)
    self.assertEqual(operation_name, resp.name)

  def AssertInvalidOutputUrlPrefix(self, output_url_prefix):
    with self.assertRaises(resources.UserError):
      self.RunExportTest(output_url_prefix=output_url_prefix)


if __name__ == '__main__':
  test_case.main()
