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
"""Unit tests for environments storage dags delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.composer import base
from tests.lib.surface.composer import kubectl_util
import mock


@parameterized.parameters([True, False])
@mock.patch('googlecloudsdk.core.execution_utils.Exec')
class EnvironmentsStorageDagsDeleteGATest(base.GsutilShellingUnitTest,
                                          base.StorageApiCallingUnitTest,
                                          parameterized.TestCase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.GA)

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(False)

  def testDagsDeleteTargetSpecified(self, use_gsutil, exec_mock):
    """Tests successful DAG deleting for a specific file."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'dags/')
    self.ExpectObjectGet(subdir_ref)
    target = 'subdir/file.txt'

    if use_gsutil:
      self._SetUpGsutil()
      fake_exec = kubectl_util.FakeExec()
      exec_mock.side_effect = fake_exec
      fake_exec.AddCallback(
          0,
          self.MakeGsutilExecCallback(
              ['-m', 'rm', '-r',
               '{}/dags/{}'.format(self.test_gcs_bucket_path, target)]))
    else:
      self._SetUpStorageApi()

    self.RunEnvironments('storage', 'dags', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         target)

    if use_gsutil:
      fake_exec.Verify()
    else:
      self.delete_mock.assert_called_once_with(
          storage_util.BucketReference(self.test_gcs_bucket), target, 'dags')

  def testDagsDeleteTargetNotSpecified(self, use_gsutil, exec_mock):
    """Tests successful deletion of the entire DAGs directory."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'dags/')
    self.ExpectObjectGet(subdir_ref)

    if use_gsutil:
      self._SetUpGsutil()
      fake_exec = kubectl_util.FakeExec()
      exec_mock.side_effect = fake_exec
      fake_exec.AddCallback(
          0,
          self.MakeGsutilExecCallback(
              ['-m', 'rm', '-r', '{}/dags/*'.format(
                  self.test_gcs_bucket_path)]))
    else:
      self._SetUpStorageApi()

    self.RunEnvironments('storage', 'dags', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID)

    if use_gsutil:
      fake_exec.Verify()
    else:
      self.delete_mock.assert_called_once_with(
          storage_util.BucketReference(self.test_gcs_bucket), '*', 'dags')

  def testDagsDeleteRestoresSubdir(self, use_gsutil, exec_mock):
    """Tests that the DAGs dir is restored if it's missing after deletion."""
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'dags/')
    self.ExpectObjectGet(subdir_ref,
                         exception=http_error.MakeHttpError(code=404))
    self.ExpectObjectInsert(subdir_ref)

    if use_gsutil:
      self._SetUpGsutil()
      fake_exec = kubectl_util.FakeExec()
      exec_mock.side_effect = fake_exec
      fake_exec.AddCallback(
          0,
          self.MakeGsutilExecCallback(
              ['-m', 'rm', '-r', '{}/dags/*'.format(
                  self.test_gcs_bucket_path)]))
    else:
      self._SetUpStorageApi()

    self.RunEnvironments('storage', 'dags', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID)

    if use_gsutil:
      fake_exec.Verify()
    else:
      self.delete_mock.assert_called_once_with(
          storage_util.BucketReference(self.test_gcs_bucket), '*', 'dags')


class EnvironmentsStorageDagsDeleteBetaTest(
    EnvironmentsStorageDagsDeleteGATest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)


class EnvironmentsStorageDagsDeleteAlphaTest(
    EnvironmentsStorageDagsDeleteBetaTest):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.ALPHA)


if __name__ == '__main__':
  test_case.main()
