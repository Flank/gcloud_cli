# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Classes for mocking out test conditions, to use w/ sql base test classes."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googlecloudsdk.api_lib.util import messages as helpers
from tests.lib.surface.sql import data


class MockEndpoints(object):
  """Mock endpoints class, for use with sql base test classes."""

  # Operation helpers.

  def GetPendingCreateOperation(self):
    return data.GetOperation(self.Project(), self.instance, 'CREATE', 'PENDING')

  def GetDoneCreateOperation(self):
    return data.GetOperation(self.Project(), self.instance, 'CREATE', 'DONE')

  def GetPendingUpdateOperation(self):
    return data.GetOperation(self.Project(), self.instance, 'UPDATE', 'PENDING')

  def GetDoneUpdateOperation(self):
    return data.GetOperation(self.Project(), self.instance, 'UPDATE', 'DONE')

  def GetDoneDeleteBackupOperation(self):
    return data.GetOperation(self.Project(),
                             self.GetRequestInstance(self.backup.instance),
                             'DELETE_BACKUP', 'DONE')

  def GetOperationGetRequest(self):
    return data.GetOperationGetRequest(self.Project())

  # Instance helpers.

  def GetRequestInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetRequestInstance(self.Project(), name)

  def GetPatchRequestInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetPatchRequestInstance(self.Project(), name)

  def GetV1Instance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetV1Instance(self.Project(), name)

  def GetV2Instance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetV2Instance(self.Project(), name)

  def GetPostgresInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetPostgresInstance(self.Project(), name)

  def GetInstanceGetRequest(self, instance):
    return data.GetInstanceGetRequest(self.Project(), instance)

  def GetInstancePatchRequest(self, instance):
    return data.GetInstancePatchRequest(self.Project(), instance)

  # Backup helpers.

  def GetSuccessfulBackup(self, instance, backup_id=data.DEFAULT_BACKUP_ID):
    return data.GetBackup(instance, backup_id, 'SUCCESSFUL')

  def GetBackupDeleteRequest(self, backup):
    return data.GetBackupDeleteRequest(self.Project(), backup)

  # Operation expect helpers.

  def ExpectDoneCreateOperationGet(self):
    self.mocked_client.operations.Get.Expect(self.GetOperationGetRequest(),
                                             self.GetDoneCreateOperation())

  def ExpectDoneUpdateOperationGet(self):
    self.mocked_client.operations.Get.Expect(self.GetOperationGetRequest(),
                                             self.GetDoneUpdateOperation())

  def ExpectRunningCreateOperationGet(self):
    self.mocked_client.operations.Get.Expect(self.GetOperationGetRequest(),
                                             self.GetRunningCreateOperation())

  def ExpectDoneDeleteBackupOperationGet(self):
    self.mocked_client.operations.Get.Expect(
        self.GetOperationGetRequest(), self.GetDoneDeleteBackupOperation())

  # Instance expect helpers.

  def ExpectInstanceGet(self, instance, diff=None):
    self.instance = helpers.UpdateMessage(instance, diff)
    self.mocked_client.instances.Get.Expect(
        self.GetInstanceGetRequest(self.instance), self.instance)

  def ExpectInstanceInsert(self, instance, diff=None):
    self.instance = helpers.UpdateMessage(instance, diff)
    self.mocked_client.instances.Insert.Expect(self.instance,
                                               self.GetPendingCreateOperation())

  def ExpectInstancePatch(self, instance, diff=None):
    self.instance = helpers.UpdateMessage(instance, diff)
    self.mocked_client.instances.Patch.Expect(
        self.GetInstancePatchRequest(self.instance),
        self.GetPendingUpdateOperation())

  # Backups expect helpers.

  def ExpectBackupDelete(self, backup, diff=None):
    self.backup = helpers.UpdateMessage(backup, diff)
    self.mocked_client.backupRuns.Delete.Expect(
        self.GetBackupDeleteRequest(backup),
        self.GetDoneDeleteBackupOperation())
