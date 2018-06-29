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
"""Tests that exercise restoring backups."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.console import console_io
from tests.lib.surface.sql import base


class BackupsRestoreTest(base.SqlMockTestBeta):

  def testBackupsRestore(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.mocked_client.instances.RestoreBackup.Expect(
        request=self.messages.SqlInstancesRestoreBackupRequest(
            project=self.Project(),
            instance='restore-target',
            instancesRestoreBackupRequest=(
                self.messages.InstancesRestoreBackupRequest(
                    restoreBackupContext=self.messages.RestoreBackupContext(
                        backupRunId=12345, instanceId='backup-source')))),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql backups restore 12345 --restore-instance restore-target '
             '--backup-instance backup-source')
    self.assertEqual(prompt_mock.call_count, 1)

  def testBackupsRestoreSameInstance(self):
    self.mocked_client.instances.RestoreBackup.Expect(
        request=self.messages.SqlInstancesRestoreBackupRequest(
            project=self.Project(),
            instance='restore-target',
            instancesRestoreBackupRequest=(
                self.messages.InstancesRestoreBackupRequest(
                    restoreBackupContext=self.messages.RestoreBackupContext(
                        backupRunId=12345, instanceId='restore-target')))),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run('sql backups restore 12345 --restore-instance restore-target')

  def testRestoreNoConfirm(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=False)
    self.Run('sql backups restore 12345 --restore-instance restore-target')
    self.assertEqual(prompt_mock.call_count, 1)

  def testRestoreAsync(self):
    self.mocked_client.instances.RestoreBackup.Expect(
        request=self.messages.SqlInstancesRestoreBackupRequest(
            project=self.Project(),
            instance='restore-target',
            instancesRestoreBackupRequest=(
                self.messages.InstancesRestoreBackupRequest(
                    restoreBackupContext=self.messages.RestoreBackupContext(
                        backupRunId=12345, instanceId='restore-target')))),
        response=self.messages.Operation(name='opName'))
    self.mocked_client.operations.Get.Expect(
        request=self.messages.SqlOperationsGetRequest(
            project=self.Project(), operation='opName'),
        response=self.messages.Operation(name='opName', status='DONE'))
    self.Run(
        'sql backups restore 12345 --restore-instance restore-target --async')
