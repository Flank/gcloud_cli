# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests that exercise operations listing and executing."""
from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base


class BackupsDeleteTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testDeleteNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql backups delete 12345 --instance=mock-instance')

  def testDelete(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.ExpectBackupDelete(
        self.GetSuccessfulBackup(self.GetV2Instance('mock-instance'), 12345))
    self.ExpectDoneDeleteBackupOperationGet()

    self.Run('sql backups delete 12345 --instance=mock-instance')
    self.AssertErrContains('Deleted backup run [{0}].'.format(12345))
    self.assertEqual(prompt_mock.call_count, 1)

  def testAsyncDelete(self):
    prompt_mock = self.StartObjectPatch(
        console_io, 'PromptContinue', return_value=True)
    self.ExpectBackupDelete(
        self.GetSuccessfulBackup(self.GetV2Instance('mock-instance'), 12345))
    self.ExpectDoneDeleteBackupOperationGet()

    self.Run('sql backups delete 12345 --instance=mock-instance --async')

    # Ensure that the status output is not produced when async is used.
    self.AssertErrNotContains('Deleted backup')
    self.assertEqual(prompt_mock.call_count, 1)

  def testDeleteNotExist(self):
    self.StartObjectPatch(console_io, 'PromptContinue', return_value=True)
    self.mocked_client.backupRuns.Delete.Expect(
        self.messages.SqlBackupRunsDeleteRequest(
            id=12345,
            instance='mock-instance',
            project=self.Project(),),
        exception=http_error.MakeHttpError(
            message='The backup run status is not valid for the given request.',
            reason='invalidBackupRunStatus'))

    # TODO(b/36050876): Figure out why this HttpError output does not match
    # gcloud output.
    with self.AssertRaisesHttpExceptionRegexp(
        r'The backup run status is not valid for the given request.'):
      self.Run('sql backups delete 12345 --instance=mock-instance')


if __name__ == '__main__':
  test_case.main()
