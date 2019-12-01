# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import admin_api
from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.firestore import base
import six.moves.http_client


class ExportTestGA(base.FirestoreCommandUnitTest, sdk_test_base.WithLogCapture):
  """Tests the GA firestore export command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testExport(self):
    output_uri_prefix = 'gs://gcs_bucket'
    expected_request = admin_api.GetExportDocumentsRequest(
        self.DatabaseResourceName(), output_uri_prefix)
    operation_name = 'export operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)
    self.mock_firestore_v1.projects_databases.ExportDocuments.Expect(
        expected_request, response=mock_response)

    resp = self.RunExportTest(output_uri_prefix=output_uri_prefix)
    self.assertEqual(operation_name, resp.name)

  def testExportNonAsync(self):
    output_uri_prefix = 'gs://gcs_bucket'
    expected_request = admin_api.GetExportDocumentsRequest(
        self.DatabaseResourceName(), output_uri_prefix)
    operation_name = ('projects/{}/databases/(default)/'
                      'operations/exportoperationname').format(self.Project())
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_export_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)
    mock_get_response = operations.GetMessages().GoogleLongrunningOperation(
        done=False, name=operation_name)
    expected_operation_get = (
        operations.GetMessages()
        .FirestoreProjectsDatabasesOperationsGetRequest())
    expected_operation_get.name = operation_name

    # Expect several calls while done=False, then we get a response from the
    # command once the export is complete.
    self.mock_firestore_v1.projects_databases.ExportDocuments.Expect(
        expected_request, response=mock_export_response)
    self.mock_firestore_v1.projects_databases_operations.Get.Expect(
        expected_operation_get, response=mock_get_response)
    self.mock_firestore_v1.projects_databases_operations.Get.Expect(
        expected_operation_get, response=mock_get_response)

    mock_response = operations.GetMessages().GoogleLongrunningOperation(
        done=True, name=operation_name)

    self.mock_firestore_v1.projects_databases_operations.Get.Expect(
        expected_operation_get, response=mock_response)

    # Call RunDatastoreTest directly, because we don't want --async.
    resp = self.RunFirestoreTest('export {}'.format(output_uri_prefix))

    self.assertEqual(operation_name, resp.name)
    self.AssertErrContains('Waiting for [{}] to finish'.format(operation_name))

  def testExportWithCollectionIds(self):
    output_uri_prefix = 'gs://gcs_bucket'
    collection_ids = ['Customers', 'Orders']
    request = admin_api.GetExportDocumentsRequest(
        self.DatabaseResourceName(),
        output_uri_prefix,
        collection_ids=collection_ids)

    operation_name = 'export operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_firestore_v1.projects_databases.ExportDocuments.Expect(
        request, response=mock_response)

    actual = self.RunExportTest(
        collection_ids=collection_ids, output_uri_prefix=output_uri_prefix)
    self.assertEqual(operation_name, actual.name)

  def testExportFailureThrowsToolHttpException(self):
    output_uri_prefix = 'gs://gcs_bucket'
    request = admin_api.GetExportDocumentsRequest(self.DatabaseResourceName(),
                                                  output_uri_prefix)

    exception = http_error.MakeHttpError(
        six.moves.http_client.BAD_REQUEST, 'error_message', url='Fake url')

    self.mock_firestore_v1.projects_databases.ExportDocuments.Expect(
        request, exception=exception)

    with self.assertRaisesRegex(exceptions.HttpException, 'error_message'):
      self.RunExportTest(output_uri_prefix=output_uri_prefix)

  def testOutputUrlPrefixConversion(self):
    self.AssertValidOutputUrlPrefix('gs://gcs_bucket')
    self.AssertInvalidOutputUrlPrefix('gcs_bucket')
    self.AssertInvalidOutputUrlPrefix('b/gcs_bucket')
    self.AssertInvalidOutputUrlPrefix(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket')
    self.AssertInvalidOutputUrlPrefix('b/foobar')
    self.AssertValidOutputUrlPrefix('gs://gcs_bucket/gcs_object_prefix',
                                    'gs://gcs_bucket/gcs_object_prefix')
    self.AssertInvalidOutputUrlPrefix(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket/o/gcs_object_prefix')  # pylint: disable=line-too-long
    # Other resource
    self.AssertInvalidOutputUrlPrefix(
        'https://www.googleapis.com/datastore/v1/projects/foo/operations/bar')

  def RunExportTest(self, collection_ids=None, output_uri_prefix=''):
    return self.RunFirestoreTest('export --async {} {}'.format(
        '--collection-ids={}'.format(self.Serialize(collection_ids))
        if collection_ids else '', output_uri_prefix))

  def AssertValidOutputUrlPrefix(self,
                                 output_uri_prefix,
                                 expected='gs://gcs_bucket'):
    expected_request = admin_api.GetExportDocumentsRequest(
        self.DatabaseResourceName(), expected)
    operation_name = 'export operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_firestore_v1.projects_databases.ExportDocuments.Expect(
        expected_request, response=mock_response)

    resp = self.RunExportTest(output_uri_prefix=output_uri_prefix)
    self.assertEqual(operation_name, resp.name)

  def AssertInvalidOutputUrlPrefix(self, output_uri_prefix):
    with self.assertRaises(ValueError):
      self.RunExportTest(output_uri_prefix=output_uri_prefix)


class ExportTestBeta(ExportTestGA):
  """Tests the beta firestore export command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ExportTestAlpha(ExportTestBeta):
  """Tests the alpha firestore export command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
