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
"""Unit tests for environments storage data delete."""

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


@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
@mock.patch('googlecloudsdk.core.execution_utils.Exec')
class EnvironmentsStorageDataDeleteTest(base.GsutilShellingUnitTest,
                                        base.StorageApiCallingUnitTest,
                                        parameterized.TestCase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)

  def testDataDeleteTargetSpecified(self, track, exec_mock):
    """Tests successful data deleting for a specific file."""
    self.SetTrack(track)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'data/')
    self.ExpectObjectGet(subdir_ref)

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    target = 'subdir/file.txt'

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'rm', '-r',
             '{}/data/{}'.format(self.test_gcs_bucket_path, target)]))

    self.RunEnvironments('storage', 'data', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID,
                         target)
    fake_exec.Verify()

  def testDataDeleteTargetNotSpecified(self, track, exec_mock):
    """Tests successful deletion of the entire data directory."""
    self.SetTrack(track)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'data/')
    self.ExpectObjectGet(subdir_ref)

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'rm', '-r', '{}/data/*'.format(self.test_gcs_bucket_path)]))

    self.RunEnvironments('storage', 'data', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID)
    fake_exec.Verify()

  def testDataDeleteRestoresSubdir(self, track, exec_mock):
    """Tests that the data dir is restored if it's missing after deletion."""
    self.SetTrack(track)
    self.ExpectEnvironmentGet(
        self.TEST_PROJECT,
        self.TEST_LOCATION,
        self.TEST_ENVIRONMENT_ID,
        response=self.MakeEnvironmentWithBucket())

    subdir_ref = storage_util.ObjectReference(self.test_gcs_bucket, 'data/')
    self.ExpectObjectGet(subdir_ref,
                         exception=http_error.MakeHttpError(code=404))
    self.ExpectObjectInsert(subdir_ref)

    fake_exec = kubectl_util.FakeExec()
    exec_mock.side_effect = fake_exec

    fake_exec.AddCallback(
        0,
        self.MakeGsutilExecCallback(
            ['-m', 'rm', '-r', '{}/data/*'.format(self.test_gcs_bucket_path)]))

    self.RunEnvironments('storage', 'data', 'delete',
                         '--project', self.TEST_PROJECT,
                         '--location', self.TEST_LOCATION,
                         '--environment', self.TEST_ENVIRONMENT_ID)
    fake_exec.Verify()


if __name__ == '__main__':
  test_case.main()
