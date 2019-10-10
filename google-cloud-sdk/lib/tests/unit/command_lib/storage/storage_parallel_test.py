# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Unit tests for parallel Google Cloud Storage operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import parallel
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock
from six.moves import range


_UNICODE_STRING = 'いろはにほへとちりぬるを'


class FailureException(Exception):
  """Contrived exception to indicate a generic failure in tests."""
  pass


def MakeRepeatMock(num_tries):
  """Returns a function that errors a given number of times per set of params.

  Args:
    num_tries: int or None, the number of the attempt that the call should
      succeed on or None if the call should never succeed

  Returns:
    function, as described.
  """
  seen_args = collections.defaultdict(int)
  def RepeatMock(*args):
    seen_args[args] += 1
    attempt = seen_args[args]
    if num_tries is None or attempt < num_tries:
      raise FailureException(
          'Failure, attempt [{0}/{1}].\nAlso, have some unicode: {2}'.format(
              attempt, num_tries, _UNICODE_STRING))
  return RepeatMock


class TasksTest(sdk_test_base.SdkBase):
  """Tests that an individual task works correctly."""
  _TEST_BUCKET = 'my-bucket'

  def SetUp(self):
    # Use single threads for unit tests; e2e tests will test (and benchmark)
    # actual use of parallel operations.
    self.get_pool_mock = self.StartObjectPatch(
        parallel, 'GetPool', return_value=parallel.DummyPool())
    self.storage_client_mock = mock.Mock(storage_api.StorageClient)
    self.StartObjectPatch(storage_api, 'StorageClient',
                          return_value=self.storage_client_mock)

  def testUpload(self):
    self.upload_mock = self.storage_client_mock.CopyFileToGCS
    local = '/some/file'
    remote = storage_util.ObjectReference(self._TEST_BUCKET, 'remote/obj')
    task = storage_parallel.FileUploadTask(local, remote)
    storage_parallel.ExecuteTasks([task])
    self.upload_mock.assert_called_once_with(local, remote)

  def testDownload(self):
    self.download_mock = self.storage_client_mock.CopyFileFromGCS
    local = '/some/file'
    remote = storage_util.ObjectReference(self._TEST_BUCKET, 'remote/obj')
    task = storage_parallel.FileDownloadTask(remote, local)
    storage_parallel.ExecuteTasks([task])
    self.download_mock.assert_called_once_with(remote, local)

  def testCopy(self):
    self.copy_mock = self.storage_client_mock.Copy
    remote1 = storage_util.ObjectReference(self._TEST_BUCKET, 'remote/obj1')
    remote2 = storage_util.ObjectReference(self._TEST_BUCKET, 'remote/obj2')
    task = storage_parallel.FileRemoteCopyTask(remote1, remote2)
    storage_parallel.ExecuteTasks([task])
    self.copy_mock.assert_called_once_with(remote1, remote2)

  def testDelete(self):
    self.delete_mock = self.storage_client_mock.DeleteObject
    remote = storage_util.ObjectReference(self._TEST_BUCKET, 'remote/obj')
    task = storage_parallel.ObjectDeleteTask(remote)
    storage_parallel.ExecuteTasks([task])
    self.delete_mock.assert_called_once_with(remote)


class ParallelUploadTestBase(sdk_test_base.WithOutputCapture):

  _TEST_BUCKET = 'my-bucket'
  _DEFAULT_NUM_TASKS = 10

  def _MakeTestTasks(self, count):
    tasks = []
    for n in range(count):
      tasks.append(storage_parallel.FileUploadTask(
          'local{0}'.format(n), storage_util.ObjectReference(
              self._TEST_BUCKET, 'remote{0}'.format(n))))
    return tasks

  def SetUp(self):
    # Use single threads for unit tests; e2e tests will test (and benchmark)
    # actual use of parallel operations.
    self.get_pool_mock = self.StartObjectPatch(
        parallel, 'GetPool', return_value=parallel.DummyPool())
    storage_client_mock = mock.Mock(storage_api.StorageClient)
    self.StartObjectPatch(storage_api, 'StorageClient',
                          return_value=storage_client_mock)
    self.copy_file_mock = storage_client_mock.CopyFileToGCS


class ParallelUploadProgressBarTest(ParallelUploadTestBase):

  def SetUp(self):
    self.progress_bar_states = []
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    def CheckProgressBarState(*args):
      del args  # Unused
      self.AssertErrEquals(self.progress_bar_states.pop(0))
    self.copy_file_mock.side_effect = CheckProgressBarState

  def testProgressBar(self):
    tasks = self._MakeTestTasks(2)
    self.progress_bar_states = [
        ('#============================================================#\n'
         '#= Uploading 2 files to Google Cloud Storage                =#\n'
         '#'),
        ('#============================================================#\n'
         '#= Uploading 2 files to Google Cloud Storage                =#\n'
         '#=============================='),
    ]
    storage_parallel.UploadFiles(tasks, num_threads=1, show_progress_bar=True)

    self.assertEqual(self.copy_file_mock.call_count, 2)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Uploading 2 files to Google Cloud Storage                =#\n'
        '#============================================================#\n'
    )

  def testProgressBar_OneTask(self):
    tasks = self._MakeTestTasks(1)
    self.progress_bar_states = [
        ('#============================================================#\n'
         '#= Uploading 1 file to Google Cloud Storage                 =#\n'
         '#'),
    ]
    storage_parallel.UploadFiles(tasks, num_threads=1, show_progress_bar=True)

    self.assertEqual(self.copy_file_mock.call_count, 1)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Uploading 1 file to Google Cloud Storage                 =#\n'
        '#============================================================#\n'
    )

  def testProgressBar_NoTasks(self):
    storage_parallel.UploadFiles([], num_threads=1, show_progress_bar=True)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Uploading 0 files to Google Cloud Storage                =#\n'
        '#============================================================#\n'
    )
    self.copy_file_mock.assert_not_called()


class ParallelUploadTest(ParallelUploadTestBase):

  def _RunTestWithGivenParallelism(self, num_threads):
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    storage_parallel.UploadFiles(tasks, num_threads=num_threads)
    for n in range(self._DEFAULT_NUM_TASKS):
      self.copy_file_mock.assert_any_call(
          'local{0}'.format(n),
          storage_util.ObjectReference(self._TEST_BUCKET,
                                       'remote{0}'.format(n)))
    self.assertEqual(self.copy_file_mock.call_count, self._DEFAULT_NUM_TASKS)
    self.get_pool_mock.assert_called_once_with(num_threads)

  def testUploadFile_NotParallel(self):
    self._RunTestWithGivenParallelism(1)

  def testUploadFile_MultiThread(self):
    self._RunTestWithGivenParallelism(16)

  def _RunTestWithSuccessAfterNumTries(self, num_tries):
    self.copy_file_mock.side_effect = MakeRepeatMock(num_tries)
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    storage_parallel.UploadFiles(tasks)
    calls = []
    self.assertEqual(self.copy_file_mock.call_count,
                     self._DEFAULT_NUM_TASKS * num_tries)
    for n in range(self._DEFAULT_NUM_TASKS):
      for _ in range(num_tries):
        calls.append(mock.call(
            'local{0}'.format(n),
            storage_util.ObjectReference(self._TEST_BUCKET,
                                         'remote{0}'.format(n))))
    self.copy_file_mock.assert_has_calls(calls, any_order=True)
    self.get_pool_mock.assert_called_once_with(16)

  def testUploadFile_SucceedFirstTry(self):
    self._RunTestWithSuccessAfterNumTries(1)

  def testUploadFile_SucceedSecondTry(self):
    self._RunTestWithSuccessAfterNumTries(2)

  def testUploadFile_SucceedThirdTry(self):
    self._RunTestWithSuccessAfterNumTries(3)

  def testUploadFile_SucceedFourthTry(self):
    self._RunTestWithSuccessAfterNumTries(4)

  def testUploadFile_FailFourTimes(self):
    # max_retrials=3 as set in _UploadFile means that there can be up to 4
    # attempts
    self.copy_file_mock.side_effect = MakeRepeatMock(5)
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    with self.assertRaises(parallel.MultiError):
      storage_parallel.UploadFiles(tasks)

  def testUploadFile_NoFiles(self):
    storage_parallel.UploadFiles([])
    self.copy_file_mock.assert_not_called()
    self.get_pool_mock.assert_called_once_with(16)

  def testUploadFile_OneFile(self):
    tasks = self._MakeTestTasks(1)
    storage_parallel.UploadFiles(tasks)
    self.copy_file_mock.assert_called_once_with(
        'local0',
        storage_util.ObjectReference(self._TEST_BUCKET, 'remote0'))
    self.get_pool_mock.assert_called_once_with(16)


class ParallelDeleteTestBase(sdk_test_base.WithOutputCapture):

  _TEST_BUCKET = 'my-bucket'
  _DEFAULT_NUM_TASKS = 100

  def _MakeTestTasks(self, count):
    tasks = []
    for n in range(count):
      tasks.append(storage_parallel.ObjectDeleteTask(
          storage_util.ObjectReference(
              self._TEST_BUCKET, 'remote{0}'.format(n))))
    return tasks

  def SetUp(self):
    # Use single threads for unit tests; e2e tests will test (and benchmark)
    # actual use of parallel operations.
    self.get_pool_mock = self.StartObjectPatch(
        parallel, 'GetPool', return_value=parallel.DummyPool())
    storage_client_mock = mock.Mock(storage_api.StorageClient)
    self.StartObjectPatch(storage_api, 'StorageClient',
                          return_value=storage_client_mock)
    self.delete_object_mock = storage_client_mock.DeleteObject


class ParallelDeleteProgressBarTest(ParallelDeleteTestBase):

  def SetUp(self):
    self.progress_bar_states = []
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL.name)
    def CheckProgressBarState(*args):
      del args  # Unused
      self.AssertErrEquals(self.progress_bar_states.pop(0))
    self.delete_object_mock.side_effect = CheckProgressBarState

  def testProgressBar(self):
    tasks = self._MakeTestTasks(2)
    self.progress_bar_states = [
        ('#============================================================#\n'
         '#= Deleting 2 objects from Google Cloud Storage             =#\n'
         '#'),
        ('#============================================================#\n'
         '#= Deleting 2 objects from Google Cloud Storage             =#\n'
         '#=============================='),
    ]
    storage_parallel.DeleteObjects(tasks, num_threads=1, show_progress_bar=True)

    self.assertEqual(self.delete_object_mock.call_count, 2)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Deleting 2 objects from Google Cloud Storage             =#\n'
        '#============================================================#\n'
    )

  def testProgressBar_OneTask(self):
    tasks = self._MakeTestTasks(1)
    self.progress_bar_states = [
        ('#============================================================#\n'
         '#= Deleting 1 object from Google Cloud Storage              =#\n'
         '#'),
    ]
    storage_parallel.DeleteObjects(tasks, num_threads=1, show_progress_bar=True)

    self.assertEqual(self.delete_object_mock.call_count, 1)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Deleting 1 object from Google Cloud Storage              =#\n'
        '#============================================================#\n'
    )

  def testProgressBar_NoTasks(self):
    storage_parallel.DeleteObjects([], num_threads=1, show_progress_bar=True)
    self.AssertErrEquals(
        '#============================================================#\n'
        '#= Deleting 0 objects from Google Cloud Storage             =#\n'
        '#============================================================#\n'
    )
    self.delete_object_mock.assert_not_called()


class ParallelDeleteTest(ParallelDeleteTestBase):

  def _RunTestWithGivenParallelism(self, num_threads):
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    storage_parallel.DeleteObjects(tasks, num_threads=num_threads)
    for n in range(self._DEFAULT_NUM_TASKS):
      self.delete_object_mock.assert_any_call(
          storage_util.ObjectReference(
              self._TEST_BUCKET, 'remote{0}'.format(n)))
    self.assertEqual(self.delete_object_mock.call_count,
                     self._DEFAULT_NUM_TASKS)
    self.get_pool_mock.assert_called_once_with(num_threads)

  def testDeleteObject_NotParallel(self):
    self._RunTestWithGivenParallelism(1)

  def testDeleteObject_MultiThread(self):
    self._RunTestWithGivenParallelism(16)

  def _RunTestWithSuccessAfterNumTries(self, num_tries):
    self.delete_object_mock.side_effect = MakeRepeatMock(num_tries)
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    storage_parallel.DeleteObjects(tasks)
    calls = []
    self.assertEqual(self.delete_object_mock.call_count,
                     self._DEFAULT_NUM_TASKS * num_tries)
    for n in range(self._DEFAULT_NUM_TASKS):
      for _ in range(num_tries):
        calls.append(mock.call(
            storage_util.ObjectReference(
                self._TEST_BUCKET, 'remote{0}'.format(n))))
    self.delete_object_mock.assert_has_calls(calls, any_order=True)
    self.get_pool_mock.assert_called_once_with(16)

  def testDeleteObject_SucceedFirstTry(self):
    self._RunTestWithSuccessAfterNumTries(1)

  def testDeleteObject_SucceedSecondTry(self):
    self._RunTestWithSuccessAfterNumTries(2)

  def testDeleteObject_SucceedThirdTry(self):
    self._RunTestWithSuccessAfterNumTries(3)

  def testDeleteObject_SucceedFourthTry(self):
    self._RunTestWithSuccessAfterNumTries(4)

  def testDeleteObject_FailFourTimes(self):
    # max_retrials=3 as set in _DeleteObject means that there can be up to 4
    # attempts
    self.delete_object_mock.side_effect = MakeRepeatMock(5)
    tasks = self._MakeTestTasks(self._DEFAULT_NUM_TASKS)
    with self.assertRaises(parallel.MultiError):
      storage_parallel.DeleteObjects(tasks)

  def testDeleteObject_NoFiles(self):
    storage_parallel.DeleteObjects([])
    self.delete_object_mock.assert_not_called()
    self.get_pool_mock.assert_called_once_with(16)

  def testDeleteObject_OneFile(self):
    tasks = self._MakeTestTasks(1)
    storage_parallel.DeleteObjects(tasks)
    self.delete_object_mock.assert_called_once_with(
        storage_util.ObjectReference(self._TEST_BUCKET, 'remote0'))
    self.get_pool_mock.assert_called_once_with(16)


if __name__ == '__main__':
  test_case.main()
