# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for Composer storage util."""

from __future__ import absolute_import
from __future__ import unicode_literals
import posixpath
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util as gcs_util
from googlecloudsdk.command_lib.composer import parsers
from googlecloudsdk.command_lib.composer import storage_util
from googlecloudsdk.command_lib.composer import util as command_util
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock
import six


class StorageUtilTest(base.StorageApiCallingUnitTest,
                      base.GsutilShellingUnitTest):

  def testListSuccessful(self):
    """Tests successful List call."""
    responses = [
        self.storage_messages.Objects(
            items=[
                self.storage_messages.Object(name='subdir/file_' +
                                             six.text_type(next_page_token) +
                                             '_' + six.text_type(i))
                for i in range(5)
            ],
            nextPageToken=next_page_token)
        for next_page_token in ['foo', 'bar', None]
    ]
    expected_list_response = []
    for response in responses:
      expected_list_response += response.items

    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    self.ExpectObjectList(self.test_gcs_bucket, 'subdir/', responses=responses)

    actual_list_response = storage_util.List(env_ref, 'subdir')
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def testListEnvironmentGetFails(self):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.List(env_ref, 'subdir')
    self._EnvironmentGetFailsHelper(_Callback)

  def testListStorageListFails(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    self.ExpectObjectList(
        self.test_gcs_bucket,
        'subdir/',
        exception=http_error.MakeHttpError(
            code=403, message='PERMISSION_DENIED'))

    with self.AssertRaisesExceptionMatches(storage_api.UploadError, ''):
      list(storage_util.List(env_ref, 'subdir'))

  def testListEnvironmentWithoutGcsBucket(self):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.List(env_ref, 'subdir')
    self._EnvironmentWithoutGcsBucketHelper(_Callback)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportSuccessful(self, exec_mock):
    """Tests successful Import call."""
    sources = ['c/d']
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r']
            + sources
            + [self.test_gcs_bucket_path + '/subdir/']))

    storage_util.Import(env_ref, sources, 'subdir/')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportEnvironmentGetFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, [], 'subdir')
    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportGsutilFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, [], 'subdir')
    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportEnvironmentWithoutGcsBucket(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, [], 'subdir')
    self._EnvironmentWithoutGcsBucketHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportSuccessful(self, isdir_mock, exec_mock):
    """Tests successful Export call."""
    sources = ['a', 'b', 'c/d']
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r']
            + [posixpath.join(self.test_gcs_bucket_path, source)
               for source in sources]
            + ['subdir']))

    storage_util.Export(env_ref, sources, 'subdir')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportGcsDestinationHasSlashAdded(self, isdir_mock, exec_mock):
    """Tests that a trailing slash is automatically added to gs:// dests."""
    sources = ['a', 'b', 'c/d']
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r']
            + [posixpath.join(self.test_gcs_bucket_path, source)
               for source in sources]
            + ['gs://subdir/']))

    storage_util.Export(env_ref, sources, 'gs://subdir')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportEnvironmentGetFails(self, isdir_mock, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(env_ref, ['subdir/*'], 'subdir')
    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportGsutilFails(self, isdir_mock, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(env_ref, ['subdir/*'], 'subdir')
    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportEnvironmentWithoutGcsBucket(self, isdir_mock, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(env_ref, ['subdir/*'], 'subdir')
    self._EnvironmentWithoutGcsBucketHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=False)
  def testExportLocalDestinationIsNotDirectory(self, isdir_mock, exec_mock):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'must be a directory'):
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(env_ref, ['subdir/*'], 'subdir')

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteSuccessful(self, exec_mock):
    """Tests successful Delete call."""
    target = 'c/d'
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'rm', '-r',
             '{}/subdir/{}'.format(self.test_gcs_bucket_path, target)]))

    self.ExpectObjectGet(
        gcs_util.ObjectReference(self.test_gcs_bucket, 'subdir/'))

    storage_util.Delete(env_ref, target, 'subdir')
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteEnvironmentGetFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir')
    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteGsutilFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir')
    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteEnvironmentWithoutGcsBucket(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir')
    self._EnvironmentWithoutGcsBucketHelper(_Callback, exec_mock)

  def _EnvironmentGetFailsHelper(self, callback, exec_mock=None):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))

    with self.AssertRaisesExceptionMatches(
        apitools_exceptions.HttpNotFoundError, ''):
      callback()

    if exec_mock:
      self.assertFalse(exec_mock.called)

  def _GsutilFailsHelper(self, callback, exec_mock):
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    def _FailedGsutilCallback(unused_args, **unused_kwargs):
      return 1

    fake_exec.AddCallback(0, _FailedGsutilCallback)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'gsutil returned non-zero status code.'):
      callback()

    fake_exec.Verify()

  def _EnvironmentWithoutGcsBucketHelper(self, callback, exec_mock=None):
    env = self.MakeEnvironment(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        config=self.messages.EnvironmentConfig())

    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=env)

    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Could not retrieve Cloud Storage bucket'):
      callback()

    if exec_mock:
      self.assertFalse(exec_mock.called)


if __name__ == '__main__':
  test_case.main()
