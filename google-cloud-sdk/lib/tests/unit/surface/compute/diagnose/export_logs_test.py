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
"""Tests for compute diagnose export-logs command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import datetime
import urllib

from apitools.base.py.exceptions import HttpError

from googlecloudsdk.api_lib.util import apis
from tests.lib.surface.compute import test_base

import mock

# The import string for the DiagnoseClient class, used for mocking its methods.
_DIAGNOSE_CLIENT_IMPORT = ('googlecloudsdk.api_lib.compute.diagnose.'
                           'diagnose_utils.DiagnoseClient')
# The import string for the Projects Api, used for mocking its methods.
_PROJECTS_API_IMPORT = ('googlecloudsdk.api_lib.cloudresourcemanager.'
                        'projects_api')
# The mock project number for each test to use
_PROJECT_NUM = 12345


class ExportLogsTest(test_base.BaseTest):

  def SetUp(self):
    """Called by base class's SetUp() method, which does additional mocking."""
    resource_messages = apis.GetMessagesModule('cloudresourcemanager', 'v1')
    iam_messages = apis.GetMessagesModule('iam', 'v1')
    storage_messages = apis.GetMessagesModule('storage', 'v1')

    # Mock any network calls to an API with a default value, preserving the
    # mocks for use within individual tests.
    list_accounts = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.ListServiceAccounts',
        return_value=[
            iam_messages.ServiceAccount(email='invalid-account@google.com'),
            iam_messages.ServiceAccount(
                email='gce-diagnostics-extract-logs@google.com')
        ],
        autospec=True)
    self.addCleanup(list_accounts.stop)
    self._mock_list_accounts = list_accounts.start()

    create_account = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.CreateServiceAccount', autospec=True)
    self.addCleanup(create_account.stop)
    self._mock_create_account = create_account.start()

    sign_blob = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.SignBlob', return_value='', autospec=True)
    self.addCleanup(sign_blob.stop)
    self._mock_sign_blob = sign_blob.start()

    find_bucket = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.FindBucket',
        return_value=storage_messages.Bucket(),
        autospec=True)
    self.addCleanup(find_bucket.stop)
    self._mock_find_bucket = find_bucket.start()

    insert_bucket = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.InsertBucket', autospec=True)
    self.addCleanup(insert_bucket.stop)
    self._mock_insert_bucket = insert_bucket.start()

    update_metadata = mock.patch(
        _DIAGNOSE_CLIENT_IMPORT + '.UpdateMetadata', autospec=True)
    self.addCleanup(update_metadata.stop)
    self._mock_update_metadata = update_metadata.start()

    add_iam_policy = mock.patch(
        _PROJECTS_API_IMPORT + '.AddIamPolicyBinding', autospec=True)
    self.addCleanup(add_iam_policy.stop)
    add_iam_policy.start()

    project_number = mock.patch(
        _PROJECTS_API_IMPORT + '.Get',
        return_value=resource_messages.Project(projectNumber=_PROJECT_NUM),
        autospec=True)
    self.addCleanup(project_number.stop)
    project_number.start()

    # Set today as 1/2/2014 at 3:4:5-000006
    real_datetime = datetime.datetime
    datetime.datetime = test_base.FakeDateTime

    def ResetDatetime():
      datetime.datetime = real_datetime

    self.addCleanup(ResetDatetime)

  def testNormalCase(self):
    log_path = 'instance-1-logs-2014-01-02-03-04-05-000006.zip'
    bucket = 'test-bucket'
    signature = 'test-signature'
    self._mock_find_bucket.return_value.name = bucket
    self._mock_sign_blob.return_value = signature

    encoded_signature = ''
    signature_b64 = base64.b64encode(signature.encode('utf-8'))
    if hasattr(urllib, 'quote_plus'):
      encoded_signature = urllib.quote_plus(signature_b64)
    else:
      encoded_signature = urllib.parse.quote_plus(signature_b64)

    result = self.Run('alpha compute diagnose export-logs '
                      '--zone us-west1-a instance-1')

    self.assertEquals('test-bucket', result['bucket'])
    self.assertEquals(log_path, result['logPath'])
    self.assertTrue(result['signedUrl'].endswith(encoded_signature))
    self.assertFalse(self._mock_create_account.called)
    self.assertFalse(self._mock_insert_bucket.called)
    self.assertIn('"trace": false', str(self._mock_update_metadata.call_args))

  def testTraceFlag(self):
    self.Run('alpha compute diagnose export-logs --zone us-west1-a instance-1 '
             '--collect-process-traces')

    self.assertIn('"trace": true', str(self._mock_update_metadata.call_args))

  def testServiceAccountNotCreated(self):
    self._mock_list_accounts.return_value = []

    self.Run('alpha compute diagnose export-logs --zone us-west1-a instance-1')

    self.assertTrue(self._mock_create_account.called)

  def testBucketNotCreated(self):
    self._mock_find_bucket.return_value = None

    results = self.Run('alpha compute diagnose export-logs '
                       '--zone us-west1-a instance-1')

    self.assertTrue(results['bucket'].endswith(str(_PROJECT_NUM)))
    self.assertTrue(self._mock_insert_bucket.called)

  def testBucketNameTaken(self):
    self._mock_find_bucket.return_value = None
    # Inserting a bucket will fail for the first 3 times saying a bucket with
    # that name already exists.
    error409 = HttpError({'status': 409}, None, None)
    self._mock_insert_bucket.side_effect = [error409, error409, error409, None]

    results = self.Run('alpha compute diagnose export-logs '
                       '--zone us-west1-a instance-1')

    # The _# suffix is added after the first failure, and counts up until the
    # bucket name is unique.
    suffix = '{}_2'.format(_PROJECT_NUM)
    self.assertTrue(results['bucket'].endswith(suffix))
    self.assertEqual(4, self._mock_insert_bucket.call_count)
