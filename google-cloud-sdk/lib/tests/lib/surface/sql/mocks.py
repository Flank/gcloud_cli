# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import messages as helpers
from tests.lib.surface.sql import data

sqladmin_v1beta4 = core_apis.GetMessagesModule('sql', 'v1beta4')


class MockEndpoints(object):
  """Mock endpoints class, for use with sql base test classes."""

  # Operation helpers.

  def GetOperation(self, op_type, op_status, error=None):
    return data.GetOperation(self.Project(), self.instance, op_type, op_status,
                             error)

  def GetPendingCreateOperation(self):
    return self.GetOperation(
        sqladmin_v1beta4.Operation.OperationTypeValueValuesEnum.CREATE,
        sqladmin_v1beta4.Operation.StatusValueValuesEnum.PENDING)

  def GetDoneCreateOperation(self):
    return self.GetOperation(
        sqladmin_v1beta4.Operation.OperationTypeValueValuesEnum.CREATE,
        sqladmin_v1beta4.Operation.StatusValueValuesEnum.DONE)

  def GetPendingUpdateOperation(self):
    return self.GetOperation(
        sqladmin_v1beta4.Operation.OperationTypeValueValuesEnum.UPDATE,
        sqladmin_v1beta4.Operation.StatusValueValuesEnum.PENDING)

  def GetDoneUpdateOperation(self):
    return self.GetOperation(
        sqladmin_v1beta4.Operation.OperationTypeValueValuesEnum.UPDATE,
        sqladmin_v1beta4.Operation.StatusValueValuesEnum.DONE)

  def GetDoneDeleteBackupOperation(self):
    return data.GetOperation(
        self.Project(), self.GetRequestInstance(self.backup.instance),
        sqladmin_v1beta4.Operation.OperationTypeValueValuesEnum.DELETE_BACKUP,
        sqladmin_v1beta4.Operation.StatusValueValuesEnum.DONE)

  def GetOperationGetRequest(self):
    return data.GetOperationGetRequest(self.Project())

  # Instance helpers.

  def GetRequestInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetRequestInstance(self.Project(), name)

  def GetExternalMasterRequestInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetExternalMasterRequestInstance(self.Project(), name)

  def GetPatchRequestInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetPatchRequestInstance(self.Project(), name)

  def GetV1Instance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetV1Instance(self.Project(), name)

  def GetV2Instance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetV2Instance(self.Project(), name)

  def GetPostgresInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetPostgresInstance(self.Project(), name)

  def GetSqlServerInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetSqlServerInstance(self.Project(), name)

  def GetExternalMasterInstance(self, name=data.DEFAULT_INSTANCE_NAME):
    return data.GetExternalMasterInstance(self.Project(), name)

  def GetInstanceGetRequest(self, instance):
    return data.GetInstanceGetRequest(self.Project(), instance)

  def GetInstancePatchRequest(self, instance):
    return data.GetInstancePatchRequest(self.Project(), instance)

  # Backup helpers.

  def GetSuccessfulBackup(self, instance, backup_id=data.DEFAULT_BACKUP_ID):
    return data.GetBackup(
        instance, backup_id,
        sqladmin_v1beta4.BackupRun.StatusValueValuesEnum.SUCCESSFUL)

  def GetBackupDeleteRequest(self, backup):
    return data.GetBackupDeleteRequest(self.Project(), backup)

  # Operation expect helpers.

  def ExpectOperationGet(self, operation):
    self.mocked_client.operations.Get.Expect(self.GetOperationGetRequest(),
                                             operation)

  def ExpectDoneCreateOperationGet(self):
    self.ExpectOperationGet(self.GetDoneCreateOperation())

  def ExpectDoneUpdateOperationGet(self):
    self.ExpectOperationGet(self.GetDoneUpdateOperation())

  def ExpectRunningCreateOperationGet(self):
    self.ExpectOperationGet(self.GetRunningCreateOperation())

  def ExpectDoneDeleteBackupOperationGet(self):
    self.ExpectOperationGet(self.GetDoneDeleteBackupOperation())

  # Instance expect helpers.

  def ExpectInstanceGet(self, instance, diff=None, no_response=False):
    self.instance = helpers.UpdateMessage(instance, diff)
    response = None if no_response else self.instance
    self.mocked_client.instances.Get.Expect(
        self.GetInstanceGetRequest(self.instance), response)

  def ExpectInstanceInsert(self, instance, diff=None, no_response=False):
    self.instance = helpers.UpdateMessage(instance, diff)
    response = None if no_response else self.GetPendingCreateOperation()
    self.mocked_client.instances.Insert.Expect(self.instance, response)

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
