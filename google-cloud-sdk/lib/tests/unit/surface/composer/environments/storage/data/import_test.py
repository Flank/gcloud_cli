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
"""Unit tests for environments storage data import."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock


class EnvironmentsStorageDataImportGATest(base.GsutilShellingUnitTest,
                                          parameterized.TestCase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  @parameterized.parameters([True, False])
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDataImport(self, use_gsutil, exec_mock):
    """Tests successful data importing."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    source = 'subdir/file.txt'

    if use_gsutil:
      self._SetUpGsutil()
      fake_exec = kubectl_util.FakeExec()
      exec_mock.side_effect = fake_exec
      fake_exec.AddCallback(
          0,
          self.MakeGsutilExecCallback(
              ['-m', 'cp', '-r', source, self.test_gcs_bucket_path + '/data/']))
    else:
      self._SetUpStorageApi()

    self.RunEnvironments('storage', 'data', 'import',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         '--source', source)

    if use_gsutil:
      fake_exec.Verify()
    else:
      self.import_mock.assert_called_once_with(
          storage_util.BucketReference(self.test_gcs_bucket), source, 'data/')

  @parameterized.parameters([
      'subdir/*.txt', 'subdir/??.txt', 'subdir/[b-g].txt', 'subdir/[a-m]??.j*g'
  ])
  @mock.patch('googlecloudsdk.core.execution_utils.Exec')
  def testDataImportWarning(self, source, exec_mock):
    """Tests successful data importing."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())
    source = 'subdir/*.txt'

    self._SetUpGsutil()
    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec
    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'cp', '-r', source, self.test_gcs_bucket_path + '/data/']))

    self.RunEnvironments('storage', 'data', 'import',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         '--source', source)

    fake_exec.Verify()
    self.AssertErrContains(
        'Use of gsutil wildcards is no longer supported in --source. '
        'Set the storage/use_gsutil property to get the old behavior '
        'back temporarily. However, this property will eventually be '
        'removed.')


class EnvironmentsStorageDataImportBetaTest(
    EnvironmentsStorageDataImportGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class EnvironmentsStorageDataImportAlphaTest(
    EnvironmentsStorageDataImportBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
