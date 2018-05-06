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
"""Unit tests for environments storage plugins import."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock


@mock.patch('googlecloudsdk.core.execution_utils.Exec')
class EnvironmentsStoragePluginsImportTest(base.GsutilShellingUnitTest):

  def testPluginsImport(self, exec_mock):
    """Tests successful plugin importing."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    source = 'subdir/file.txt'

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r', source,
             self.test_gcs_bucket_path + '/plugins/']))

    self.RunEnvironments('storage', 'plugins', 'import',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         '--source', source)
    fake_exec.Verify()


if __name__ == '__main__':
  test_case.main()
