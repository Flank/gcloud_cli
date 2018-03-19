# Copyright 2016 Google Inc. All Rights Reserved.
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
"""ml-engine local train tests."""
import os

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ml_engine import local_train
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class LocalTrainTestBase(object):

  def SetUp(self):
    self.run_mock = self.StartObjectPatch(local_train, 'RunDistributed',
                                          return_value=0)
    self.make_proc_mock = self.StartObjectPatch(local_train, 'MakeProcess',
                                                return_value=0)

  def testLocalTrainDistributed(self):
    self.Run('ml-engine local train --module-name test_package.test_task '
             '--package-path test_package/ --distributed '
             '--job-dir gs://foo/bar')

    self.run_mock.assert_called_once_with(
        'test_package.test_task',
        os.getcwd(),
        2,
        2,
        27182,
        user_args=['--job-dir', 'gs://foo/bar'])

  def testLocalTrainExitNonZero(self):
    self.run_mock.return_value = 1

    with self.assertRaises(exceptions.ExitCodeNoError):
      self.Run('ml-engine local train --module-name test_package.test_task '
               '--package-path test_package/ --distributed')

    self.run_mock.assert_called_once_with(
        'test_package.test_task',
        os.getcwd(),
        2,
        2,
        27182,
        user_args=[])

  def testLocalTrainSingleWorker(self):
    self.Run('ml-engine local train --module-name test_package.test_task '
             '--package-path test_package/ --job-dir gs://foo/bar/ -- foo')

    self.make_proc_mock.assert_called_once_with(
        'test_package.test_task',
        os.getcwd(),
        args=['foo', '--job-dir', 'gs://foo/bar/'],
        task_type='master')

  def testLocalTrainSingleWorkerExitNonZero(self):
    self.make_proc_mock.return_value = 1

    with self.assertRaises(exceptions.ExitCodeNoError):
      self.Run('ml-engine local train --module-name test_package.test_task '
               '--package-path test_package/ -- foo')

    self.make_proc_mock.assert_called_once_with(
        'test_package.test_task',
        os.getcwd(),
        args=['foo'],
        task_type='master')

  def testLocalTrainSingleWorkerLocalJobDir(self):
    self.Run('ml-engine local train --module-name test_package.test_task '
             '--package-path test_package/ --job-dir {} -- foo'.format(
                 self.temp_path))

    self.make_proc_mock.assert_called_once_with(
        'test_package.test_task',
        os.getcwd(),
        args=['foo', '--job-dir', self.temp_path],
        task_type='master')


class LocalTrainGaTest(LocalTrainTestBase, base.MlGaPlatformTestBase):

  def SetUp(self):
    super(LocalTrainGaTest, self).SetUp()


class LocalTrainBetaTest(LocalTrainTestBase, base.MlBetaPlatformTestBase):

  def SetUp(self):
    super(LocalTrainBetaTest, self).SetUp()


if __name__ == '__main__':
  test_case.main()
