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
"""Tests of the 'import' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import admin_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.firestore import base
import six.moves.http_client


class ImportTestGA(base.FirestoreCommandUnitTest):
  """Tests the GA firestore import command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testImport(self):
    input_uri = 'gs://gcs_bucket/gcs_object'
    expected_request = admin_api.GetImportDocumentsRequest(
        self.DatabaseResourceName(), input_uri)

    operation_name = 'import operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_firestore_v1.projects_databases.ImportDocuments.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(input_uri=input_uri)
    self.assertEqual(operation_name, actual.name)

  def testInputUrlConversion(self):
    self.AssertInvalidInputUrl('b/gcs_bucket/gcs_object')
    self.AssertValidInputUrl('gs://gcs_bucket/gcs_object')
    self.AssertInvalidInputUrl(
        'https://www.googleapis.com/storage/v1/b/gcs_bucket/o/gcs_object')
    # No object
    self.AssertValidInputUrl('gs://gcs_bucket', 'gs://gcs_bucket')
    # Other reference
    self.AssertInvalidInputUrl(
        'https://www.googleapis.com/datastore/v1/projects/foo/operations/bar')

  def testImportWithCollectionIds(self):
    input_uri = 'gs://gcs_bucket/gcs_folder'
    collection_ids = ['Customers', 'Orders']
    expected_request = admin_api.GetImportDocumentsRequest(
        self.DatabaseResourceName(), input_uri, collection_ids=collection_ids)

    operation_name = 'import operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_firestore_v1.projects_databases.ImportDocuments.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(
        collection_ids=collection_ids, input_uri=input_uri)
    self.assertEqual(operation_name, actual.name)

  def testImportFailureThrowsToolHttpException(self):
    input_uri = 'gs://gcs_bucket/gcs_file'
    request = admin_api.GetImportDocumentsRequest(self.DatabaseResourceName(),
                                                  input_uri)

    exception = http_error.MakeHttpError(
        six.moves.http_client.BAD_REQUEST, 'error_message', url='fake url')

    self.mock_firestore_v1.projects_databases.ImportDocuments.Expect(
        request, exception=exception)

    with self.assertRaisesRegex(exceptions.HttpException, 'error_message'):
      self.RunImportTest(input_uri=input_uri)

  def RunImportTest(self, collection_ids=None, input_uri=''):
    return self.RunFirestoreTest('import --async {} {}'.format(
        '--collection-ids={}'.format(self.Serialize(collection_ids))
        if collection_ids else '', input_uri))

  def AssertValidInputUrl(self,
                          input_uri,
                          expected_location='gs://gcs_bucket/gcs_object'):
    expected_request = admin_api.GetImportDocumentsRequest(
        self.DatabaseResourceName(), expected_location)

    operation_name = 'import operation name'
    messages = self.mock_firestore_v1.MESSAGES_MODULE
    mock_response = messages.GoogleLongrunningOperation(
        done=False, name=operation_name)

    self.mock_firestore_v1.projects_databases.ImportDocuments.Expect(
        expected_request, response=mock_response)

    actual = self.RunImportTest(input_uri=input_uri)
    self.assertEqual(operation_name, actual.name)

  def AssertInvalidInputUrl(self, input_uri):
    with self.assertRaises(ValueError):
      self.RunImportTest(input_uri=input_uri)


class ImportTestBeta(ImportTestGA):
  """Tests the beta firestore import command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ImportTestAlpha(ImportTestBeta):
  """Tests the alpha firestore import command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
