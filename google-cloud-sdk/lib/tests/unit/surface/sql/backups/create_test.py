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
"""Tests that exercise creating on-demand backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.sql import base


class _BaseBackupsCreateTest(object):

  def testBackupsCreate(self):
    self.ExpectInstanceGet(self.GetV2Instance('my-instance'))
    self.mocked_client.backupRuns.Insert.Expect(
        request=self.messages.SqlBackupRunsInsertRequest(
            project=self.Project(),
            instance='my-instance',
            backupRun=self.messages.BackupRun(
                description='my description',
                instance='my-instance',
                kind='sql#backupRun')),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql backups create --instance my-instance '
             '--description "my description"')
    # Ensure that the CMEK message is not showing up.
    self.AssertErrNotContains(
        'Your backup will be encrypted with this instance\'s customer-managed '
        'encryption key. If anyone destroys this key, all data encrypted with '
        'it will be permanently lost.')

  def testBackupsCreateAsync(self):
    self.ExpectInstanceGet(self.GetV2Instance('my-instance'))
    self.mocked_client.backupRuns.Insert.Expect(
        request=self.messages.SqlBackupRunsInsertRequest(
            project=self.Project(),
            instance='my-instance',
            backupRun=self.messages.BackupRun(
                description='my description',
                instance='my-instance',
                kind='sql#backupRun')),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql backups create --instance my-instance '
             '--description "my description" --async')

  def testBackupsCreateWithCmek(self):
    diff = {
        'name':
            'my-instance',
        'diskEncryptionConfiguration':
            self.messages.DiskEncryptionConfiguration(kmsKeyName='some-kms-key')
    }
    self.ExpectInstanceGet(self.GetV2Instance(), diff)
    self.mocked_client.backupRuns.Insert.Expect(
        request=self.messages.SqlBackupRunsInsertRequest(
            project=self.Project(),
            instance='my-instance',
            backupRun=self.messages.BackupRun(
                description='my description',
                instance='my-instance',
                kind='sql#backupRun')),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql backups create --instance my-instance '
             '--description "my description"')
    # Ensure that the CMEK message is showing up.
    self.AssertErrContains(
        'Your backup will be encrypted with this instance\'s customer-managed '
        'encryption key. If anyone destroys this key, all data encrypted with '
        'it will be permanently lost.')


class BackupsCreateGATest(_BaseBackupsCreateTest, base.SqlMockTestGA):
  pass


class BackupsCreateBetaTest(_BaseBackupsCreateTest, base.SqlMockTestBeta):
  pass


class BackupsCreateAlphaTest(_BaseBackupsCreateTest, base.SqlMockTestAlpha):
  pass
