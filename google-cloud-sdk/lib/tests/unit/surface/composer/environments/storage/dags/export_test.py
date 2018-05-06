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
"""Unit tests for environments storage dags export."""

from __future__ import absolute_import
from __future__ import unicode_literals
import posixpath
from tests.lib import test_case
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock


@mock.patch('googlecloudsdk.core.execution_utils.Exec')
class EnvironmentsStorageDagsExportTest(base.GsutilShellingUnitTest):

  @mock.patch('os.path.isdir', return_value=True)
  def testDagsExport(self, isdir_mock, exec_mock):
    """Tests successful DAG exporting."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    source = 'subdir/file.txt'
    destination = 'destdir'

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r',
             posixpath.join(self.test_gcs_bucket_path, 'dags', source),
             destination]))

    self.RunEnvironments(
        'storage', 'dags', 'export',
        '--project', self.TEST_PROJECT,
        '--location', self.TEST_LOCATION,
        '--environment', self.TEST_ENVIRONMENT_ID,
        '--source', source,
        '--destination', destination)
    fake_exec.Verify()

  @mock.patch('os.path.isdir', return_value=True)
  def testDagsExportWildcardSource(self, isdir_mock, exec_mock):
    """Tests that when no SOURCE is provided, the entire folder is exported."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    destination = 'destdir'

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r',
             posixpath.join(self.test_gcs_bucket_path, 'dags', '*'),
             destination]))

    self.RunEnvironments('storage', 'dags', 'export',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         '--destination', destination)
    fake_exec.Verify()


if __name__ == '__main__':
  test_case.main()
