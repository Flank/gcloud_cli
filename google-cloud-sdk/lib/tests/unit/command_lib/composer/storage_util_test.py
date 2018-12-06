# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

import os
import posixpath
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util as gcs_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.composer import parsers
from googlecloudsdk.command_lib.composer import storage_util
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock
import six
from six.moves import range


class StorageUtilTest(base.StorageApiCallingUnitTest,
                      base.GsutilShellingUnitTest, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self._SetUpGsutil()
    self.SetTrack(self.track)

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

    actual_list_response = storage_util.List(
        env_ref, 'subdir', release_track=self.track)
    six.assertCountEqual(self, expected_list_response, actual_list_response)

  def testListEnvironmentGetFails(self):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.List(env_ref, 'subdir', release_track=self.track)

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

    with self.AssertRaisesExceptionMatches(
        storage_api.ListBucketError,
        r'403 Could not list bucket [{}]: PERMISSION_DENIED'.format(
            self.test_gcs_bucket)):
      list(storage_util.List(env_ref, 'subdir', release_track=self.track))

  def testListEnvironmentWithoutGcsBucket(self):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.List(env_ref, 'subdir', release_track=self.track)

    self._EnvironmentWithoutGcsBucketHelper(_Callback)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportSuccessful(self, exec_mock):
    """Tests successful Import call."""
    source = 'c/d'
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
            + [source]
            + [self.test_gcs_bucket_path + '/subdir/']))

    storage_util.Import(env_ref, source, 'subdir/', release_track=self.track)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportEnvironmentGetFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, '', 'subdir', release_track=self.track)

    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportGsutilFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, '', 'subdir', release_track=self.track)

    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testImportEnvironmentWithoutGcsBucket(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Import(env_ref, '', 'subdir', release_track=self.track)

    self._EnvironmentWithoutGcsBucketHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportSuccessful(self, isdir_mock, exec_mock):
    """Tests successful Export call."""
    source = 'c/d'
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
            + [posixpath.join(self.test_gcs_bucket_path, source)]
            + ['subdir']))

    storage_util.Export(env_ref, source, 'subdir', release_track=self.track)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportGcsDestinationHasSlashAdded(self, isdir_mock, exec_mock):
    """Tests that a trailing slash is automatically added to gs:// dests."""
    source = 'c/d'
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
            + [posixpath.join(self.test_gcs_bucket_path, source)]
            + ['gs://subdir/']))

    storage_util.Export(
        env_ref, source, 'gs://subdir', release_track=self.track)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportEnvironmentGetFails(self, isdir_mock, exec_mock):

    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(
          env_ref, 'subdir/*', 'subdir', release_track=self.track)

    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportGsutilFails(self, isdir_mock, exec_mock):

    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(
          env_ref, 'subdir/*', 'subdir', release_track=self.track)

    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  @mock.patch('os.path.isdir', return_value=True)
  def testExportEnvironmentWithoutGcsBucket(self, isdir_mock, exec_mock):

    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Export(
          env_ref, 'subdir/*', 'subdir', release_track=self.track)

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
      storage_util.Export(
          env_ref, 'subdir/*', 'subdir', release_track=self.track)

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

    storage_util.Delete(env_ref, target, 'subdir', release_track=self.track)
    fake_exec.Verify()

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteEnvironmentGetFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir', release_track=self.track)

    self._EnvironmentGetFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteGsutilFails(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir', release_track=self.track)

    self._GsutilFailsHelper(_Callback, exec_mock)

  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDeleteEnvironmentWithoutGcsBucket(self, exec_mock):
    def _Callback():
      env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
      storage_util.Delete(env_ref, 'file', 'subdir', release_track=self.track)

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


class StorageUtilTestBeta(StorageUtilTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class StorageApiUtilTest(base.StorageApiCallingUnitTest):

  def SetUp(self):
    properties.VALUES.storage.use_gsutil.Set(False)
    self.SetTrack(calliope_base.ReleaseTrack.GA)
    self.source_dir = 'source'
    self.export_dir = os.path.join(self.temp_path, 'dest')
    self.other_bucket_path = 'gs://other-bucket'
    self.other_bucket = 'other-bucket'
    os.makedirs(self.export_dir)
    self.file = self.Touch(
        self.temp_path, os.path.join(self.source_dir, 'a.txt'), makedirs=True)
    self.file_in_dir = self.Touch(self.temp_path, os.path.join(
        self.source_dir, 'b', 'c.txt'), makedirs=True)
    self.objects = [self.storage_messages.Object(name=name) for name in (
        'dags/source/a.txt', 'dags/source/b/c.txt')]
    self.list_response = self.storage_messages.Objects(
        items=self.objects)
    self.object_refs = [
        gcs_util.ObjectReference(self.test_gcs_bucket, obj.name) for obj in
        self.objects]

  def _ExpectFailedGet(self, bucket, target):
    self.ExpectObjectGet(
        gcs_util.ObjectReference(bucket, target),
        exception=http_error.MakeHttpError(code=404, message='NOT_FOUND'))

  def _ExpectEnsureSubdirExists(self):
    self.ExpectObjectGet(gcs_util.ObjectReference(
        self.test_gcs_bucket, 'dags/'))

  def _ExpectCopyFileFromGcs(self, object_ref):
    self.ExpectObjectGet(object_ref, self.storage_messages.Object())
    # Second get call to verify size is correct.
    # TODO(b/33202933): Currently apitools only supports downloading files of
    # size 0 in mocked clients.
    self.ExpectObjectGet(object_ref, self.storage_messages.Object(size=0))

  def testImportSourceIsLocalFile(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectInsert(
        gcs_util.ObjectReference(self.test_gcs_bucket, 'dags/subdir/a.txt'),
        file_size=0)
    storage_util.Import(env_ref, self.file, 'dags/subdir/')

  def testImportSourceIsLocalDir(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectInsert(
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/source/a.txt'),
        file_size=0)
    self.ExpectObjectInsert(
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/source/b/c.txt'),
        file_size=0)
    storage_util.Import(
        env_ref, os.path.join(self.temp_path, self.source_dir), 'dags/subdir/')

  def testImportSourceIsGcsObject(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    other_bucket_object = gcs_util.ObjectReference(
        self.other_bucket, 'dags/source/a.txt')
    self.ExpectObjectGet(other_bucket_object)
    self.ExpectCopy(
        other_bucket_object,
        gcs_util.ObjectReference(self.test_gcs_bucket, 'dags/subdir/a.txt'))
    storage_util.Import(env_ref, other_bucket_object.ToUrl(), 'dags/subdir/')

  def testImportSourceIsGcsDirectory(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self._ExpectFailedGet(self.other_bucket, 'dags/source')
    self.ExpectObjectList(
        self.other_bucket, 'dags/source/', responses=[self.list_response])
    self.ExpectCopy(
        gcs_util.ObjectReference(self.other_bucket, 'dags/source/a.txt'),
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/source/a.txt'))
    self.ExpectCopy(
        gcs_util.ObjectReference(self.other_bucket, 'dags/source/b/c.txt'),
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/source/b/c.txt'))

    storage_util.Import(
        env_ref, self.other_bucket_path + '/dags/source/', 'dags/subdir/')

  def testImportSourceIsGcsDirectoryWithAsterisk(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectList(
        self.other_bucket, 'dags/source/', responses=[self.list_response])
    self.ExpectCopy(
        gcs_util.ObjectReference(self.other_bucket, 'dags/source/a.txt'),
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/a.txt'))
    self.ExpectCopy(
        gcs_util.ObjectReference(self.other_bucket, 'dags/source/b/c.txt'),
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/b/c.txt'))

    storage_util.Import(
        env_ref, self.other_bucket_path + '/dags/source/*', 'dags/subdir/')

  def testImportSourceIsDirWithGcloudIgnore(self):
    self.Touch(self.temp_path,
               os.path.join(self.source_dir, '.gcloudignore'),
               contents='.gcloudignore\nc.txt\n')
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectInsert(
        gcs_util.ObjectReference(
            self.test_gcs_bucket, 'dags/subdir/source/a.txt'),
        file_size=0)
    storage_util.Import(
        env_ref, os.path.join(self.temp_path, self.source_dir), 'dags/subdir/')

  def testDeleteStar(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    # Star has a special meaning and tells the delete function to not try
    # and get the object. This is necessary because subdirs in the GCS buckets
    # are created as objects to ensure they exist.
    self.ExpectObjectList(
        self.test_gcs_bucket, 'dags/', responses=[self.list_response])
    for obj_ref in self.object_refs:
      self.ExpectObjectDelete(obj_ref)
    self._ExpectEnsureSubdirExists()
    storage_util.Delete(env_ref, '*', 'dags')

  def testDeleteTargetIsDir(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self._ExpectFailedGet(self.test_gcs_bucket, 'dags/source/b')
    self.ExpectObjectList(
        self.test_gcs_bucket, 'dags/source/b/',
        responses=[self.storage_messages.Objects(items=[self.objects[1]])])
    self.ExpectObjectDelete(self.object_refs[1])
    self._ExpectEnsureSubdirExists()
    storage_util.Delete(env_ref, 'source/b', 'dags')

  def testDeleteTargetIsFile(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectGet(self.object_refs[0])
    self.ExpectObjectDelete(self.object_refs[0])
    self._ExpectEnsureSubdirExists()
    storage_util.Delete(env_ref, 'source/a.txt', 'dags')

  def testExportSourceIsFileDestIsLocal(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectGet(self.object_refs[0])
    self._ExpectCopyFileFromGcs(self.object_refs[0])
    storage_util.Export(
        env_ref, 'dags/source/a.txt', self.export_dir)

  def testExportSourceIsDirDestIsLocal(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    self.list_response.items.append(
        self.storage_messages.Object(name='dags/'))
    self.ExpectObjectList(
        self.test_gcs_bucket, 'dags/', responses=[self.list_response])
    for obj_ref in self.object_refs:
      self._ExpectCopyFileFromGcs(obj_ref)
    storage_util.Export(
        env_ref, 'dags/*', self.export_dir)

  def testExportSourceIsDirDestAlreadyExists(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    self.list_response.items.append(
        self.storage_messages.Object(name='dags/'))
    self.ExpectObjectList(
        self.test_gcs_bucket, 'dags/', responses=[self.list_response])
    for obj_ref in self.object_refs:
      self._ExpectCopyFileFromGcs(obj_ref)

    # Create a file that will be overwritten.
    self.file = self.Touch(
        self.temp_path,
        os.path.join('dest', self.source_dir, 'a.txt'),
        makedirs=True)
    storage_util.Export(
        env_ref, 'dags/*', self.export_dir)

  def testExportSourceIsFileDestIsGcs(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self.ExpectObjectGet(self.object_refs[0])
    self.ExpectCopy(
        self.object_refs[0],
        gcs_util.ObjectReference(self.other_bucket, 'dest/a.txt'))
    storage_util.Export(
        env_ref, 'dags/source/a.txt', self.other_bucket_path + '/dest')

  def testExportSourceIsDirDestIsGcs(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    self._ExpectFailedGet(self.test_gcs_bucket, 'dags/source')
    self.ExpectObjectList(
        self.test_gcs_bucket, 'dags/source/', responses=[self.list_response])
    self.ExpectCopy(
        self.object_refs[0],
        gcs_util.ObjectReference(self.other_bucket, 'dest/source/a.txt'))
    self.ExpectCopy(
        self.object_refs[1],
        gcs_util.ObjectReference(self.other_bucket, 'dest/source/b/c.txt'))
    storage_util.Export(
        env_ref, 'dags/source', self.other_bucket_path + '/dest')

  def testExportDestDoesNotExist(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Destination for export must be a directory.'):
      storage_util.Export(
          env_ref, 'dags/source', '/my/fake/path')

  def testImportSourceDoesNotExist(self):
    env_ref = parsers.ParseEnvironment(self.TEST_ENVIRONMENT_NAME)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    with self.AssertRaisesExceptionMatches(
        command_util.Error, 'Source for import does not exist.'):
      storage_util.Import(
          env_ref, '/my/fake/path', 'dags/subdir')

if __name__ == '__main__':
  test_case.main()
