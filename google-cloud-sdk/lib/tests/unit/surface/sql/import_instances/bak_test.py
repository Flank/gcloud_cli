# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise instance imports from bak."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


def get_mock_insert_time():
  """Create a datetime object for 2014-08-13T21:13:18.875Z."""
  return datetime.datetime(
      2014,
      8,
      13,
      21,
      13,
      18,
      875000,
      tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))).isoformat()


def get_mock_start_time():
  """Create a datetime object for 2014-08-13T21:13:18.925Z."""
  return datetime.datetime(
      2014,
      8,
      13,
      21,
      13,
      18,
      925000,
      tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))).isoformat()


def get_mock_end_time():
  """Create a datetime object for 2014-08-13T21:13:39.764Z."""
  return datetime.datetime(
      2014,
      8,
      13,
      21,
      13,
      39,
      764000,
      tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))).isoformat()


class InstancesImportBakGATest(base.SqlMockTestGA):
  # pylint:disable=g-tzinfo-datetime

  def get_mock_operation(self,
                         operation,
                         status,
                         error=None,
                         import_context=None):
    """Create a mock operation message given the supplied arguments."""
    return self.messages.Operation(
        # pylint:disable=line-too-long
        insertTime=get_mock_insert_time(),
        startTime=None,
        endTime=None,
        error=error,
        exportContext=None,
        importContext=import_context,
        targetId='testinstance',
        targetLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'
        .format(self.Project()),
        targetProject=self.Project(),
        kind='sql#operation',
        name=operation,
        selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/operations/ffa26eae-a675-47f1-a8c8-579849098aeb'
        .format(self.Project()),
        operationType=self.messages.Operation.OperationTypeValueValuesEnum
        .IMPORT,
        status=status,
        user='170350250316@developer.gserviceaccount.com')

  def expect_import(self, database, encrypted=False):
    # Generate BAK import context.
    import_context = self.messages.ImportContext(
        database=database,
        fileType=self.messages.ImportContext.FileTypeValueValuesEnum.BAK,
        kind='sql#importContext',
        uri='gs://speckletest/testinstance.bak')
    if encrypted:
      import_context.bakImportOptions = self.messages.ImportContext.BakImportOptionsValue(
          encryptionOptions=self.messages.ImportContext.BakImportOptionsValue
          .EncryptionOptionsValue(
              certPath='gs://speckletest/testcert.crt',
              pvkPath='gs://speckletest/testkey.pvk',
              pvkPassword='password'))

    # Mock out endpoints for import.
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=import_context),
            project=self.Project()),
        self.get_mock_operation(
            operation='ffa26eae-a675-47f1-a8c8-579849098aeb',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            import_context=import_context))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='ffa26eae-a675-47f1-a8c8-579849098aeb',
            project=self.Project()),
        self.get_mock_operation(
            operation='ffa26eae-a675-47f1-a8c8-579849098aeb',
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            import_context=import_context))

  def testImportMissingDatabases(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --database: Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak')

  def testFailedImport(self):
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=self.messages.ImportContext(
                    database='somedb',
                    fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                    .BAK,
                    kind='sql#importContext',
                    uri='gs://nosuchbucket/testinstance.bak')),
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://nosuchbucket/testinstance.bak')))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://nosuchbucket/testinstance.bak'),
            error=self.messages.OperationErrors(
                errors=[
                    self.messages.OperationError(
                        code='ERROR_RESOURCE_DOES_NOT_EXIST',
                        kind='sql#operationError'),
                ],
                kind='sql#operationErrors')))

    with self.assertRaises(exceptions.OperationError):
      self.Run('sql import bak testinstance '
               'gs://nosuchbucket/testinstance.bak --database=somedb')
    self.AssertErrContains('ERROR_RESOURCE_DOES_NOT_EXIST')

  def testImportNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql import bak testinstance '
               'gs://nosuchbucket/testinstance.bak --database=somedb')
    self.AssertErrContains(
        'Data from [gs://nosuchbucket/testinstance.bak] will be imported to '
        '[testinstance].')
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDatabaseImport(self):
    self.expect_import(database='somedb')
    self.WriteInput('y')

    self.Run('sql import bak testinstance '
             'gs://speckletest/testinstance.bak --database=somedb')

    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.bak] into '
                           '[https://sqladmin.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))

  def testDatabaseAbbrImport(self):
    self.expect_import(database='somedb')
    self.WriteInput('y')

    self.Run('sql import bak testinstance '
             'gs://speckletest/testinstance.bak -d somedb')

    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.bak] into '
                           '[https://sqladmin.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))

  def testImportEncryptedMissingCertPath(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --cert-path: Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --pvk-path=gs://speckletest/testkey.pvk '
               '--pvk-password=somepassword')

  def testImportEncryptedMissingPvkPath(self):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'argument --pvk-path: Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --cert-path=gs://speckletest/testcert.crt '
               '--pvk-password=somepassword')

  def testImportEncryptedMissingPvkPassword(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'argument \(--prompt-for-pvk-password \| --pvk-password\): '
        'Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --cert-path=gs://speckletest/testcert.crt '
               '--pvk-path=gs://speckletest/testkey.pvk')

  def testImportEncryptedMissingCertPathAndPvkPath(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --cert-path --pvk-path: Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --pvk-password=somepassword')

  def testImportEncryptedMissingCertPathAndPvkPassword(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError, 'argument --cert-path '
        r'\(--prompt-for-pvk-password \| --pvk-password\): Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --pvk-path=gs://speckletest/testkey.pvk')

  def testImportEncryptedMissingPvkPathAndPvkPassword(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'argument --pvk-path \(--prompt-for-pvk-password \| --pvk-password\): '
        'Must be specified.'):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --cert-path=gs://speckletest/testcert.crt')

  def testImportEncryptedMissingCert(self):
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=self.messages.ImportContext(
                    database='somedb',
                    fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                    .BAK,
                    kind='sql#importContext',
                    uri='gs://speckletest/testinstance.bak',
                    bakImportOptions=self.messages.ImportContext
                    .BakImportOptionsValue(
                        encryptionOptions=self.messages.ImportContext
                        .BakImportOptionsValue.EncryptionOptionsValue(
                            certPath='gs://nosuchbucket/testcert.crt',
                            pvkPath='gs://speckletest/testkey.pvk',
                            pvkPassword='password')))),
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://speckletest/testinstance.bak',
                bakImportOptions=self.messages.ImportContext
                .BakImportOptionsValue(
                    encryptionOptions=self.messages.ImportContext
                    .BakImportOptionsValue.EncryptionOptionsValue(
                        certPath='gs://nosuchbucket/testcert.crt',
                        pvkPath='gs://speckletest/testkey.pvk',
                        pvkPassword='password')))))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://speckletest/testinstance.bak',
                bakImportOptions=self.messages.ImportContext
                .BakImportOptionsValue(
                    encryptionOptions=self.messages.ImportContext
                    .BakImportOptionsValue.EncryptionOptionsValue(
                        certPath='gs://nosuchbucket/testcert.crt',
                        pvkPath='gs://speckletest/testkey.pvk',
                        pvkPassword='password'))),
            error=self.messages.OperationErrors(
                errors=[
                    self.messages.OperationError(
                        code='ERROR_RESOURCE_DOES_NOT_EXIST',
                        kind='sql#operationError'),
                ],
                kind='sql#operationErrors')))

    with self.assertRaises(exceptions.OperationError):
      self.Run(
          'sql import bak testinstance gs://speckletest/testinstance.bak '
          '--database=somedb --cert-path=gs://nosuchbucket/testcert.crt '
          '--pvk-path=gs://speckletest/testkey.pvk --pvk-password=password')
    self.AssertErrContains('ERROR_RESOURCE_DOES_NOT_EXIST')

  def testImportEncryptedMissingPvk(self):
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=self.messages.ImportContext(
                    database='somedb',
                    fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                    .BAK,
                    kind='sql#importContext',
                    uri='gs://speckletest/testinstance.bak',
                    bakImportOptions=self.messages.ImportContext
                    .BakImportOptionsValue(
                        encryptionOptions=self.messages.ImportContext
                        .BakImportOptionsValue.EncryptionOptionsValue(
                            certPath='gs://speckletest/testcert.crt',
                            pvkPath='gs://nosuchbucket/testkey.pvk',
                            pvkPassword='password')))),
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.PENDING,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://speckletest/testinstance.bak',
                bakImportOptions=self.messages.ImportContext
                .BakImportOptionsValue(
                    encryptionOptions=self.messages.ImportContext
                    .BakImportOptionsValue.EncryptionOptionsValue(
                        certPath='gs://speckletest/testcert.crt',
                        pvkPath='gs://nosuchbucket/testkey.pvk',
                        pvkPassword='password')))))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            project=self.Project()),
        self.get_mock_operation(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            status=self.messages.Operation.StatusValueValuesEnum.DONE,
            import_context=self.messages.ImportContext(
                database='somedb',
                fileType=self.messages.ImportContext.FileTypeValueValuesEnum
                .BAK,
                kind='sql#importContext',
                uri='gs://speckletest/testinstance.bak',
                bakImportOptions=self.messages.ImportContext
                .BakImportOptionsValue(
                    encryptionOptions=self.messages.ImportContext
                    .BakImportOptionsValue.EncryptionOptionsValue(
                        certPath='gs://speckletest/testcert.crt',
                        pvkPath='gs://nosuchbucket/testkey.pvk',
                        pvkPassword='password'))),
            error=self.messages.OperationErrors(
                errors=[
                    self.messages.OperationError(
                        code='ERROR_RESOURCE_DOES_NOT_EXIST',
                        kind='sql#operationError'),
                ],
                kind='sql#operationErrors')))

    with self.assertRaises(exceptions.OperationError):
      self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
               '--database=somedb --cert-path=gs://speckletest/testcert.crt '
               '--pvk-path=gs://nosuchbucket/testkey.pvk '
               '--pvk-password=password')
    self.AssertErrContains('ERROR_RESOURCE_DOES_NOT_EXIST')

  # TODO(b/141915394): test for invalid password and resources if/when backend
  # supports it

  def testDatabaseImportEncrypted(self):
    self.expect_import(database='somedb', encrypted=True)
    self.WriteInput('y')

    self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
             '--database=somedb --cert-path=gs://speckletest/testcert.crt '
             '--pvk-path=gs://speckletest/testkey.pvk --pvk-password=password')

    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.bak] into '
                           '[https://sqladmin.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))

  def testDatabaseAbbrImportEncrypted(self):
    self.expect_import(database='somedb', encrypted=True)
    self.WriteInput('y')

    self.Run('sql import bak testinstance gs://speckletest/testinstance.bak '
             '-d somedb --cert-path=gs://speckletest/testcert.crt '
             '--pvk-path=gs://speckletest/testkey.pvk --pvk-password=password')

    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.bak] into '
                           '[https://sqladmin.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))

  def testDatabaseImportEncryptedPrompt(self):
    self.expect_import(database='somedb', encrypted=True)
    self.WriteInput('password')
    self.WriteInput('y')

    self.Run(
        'sql import bak testinstance gs://speckletest/testinstance.bak '
        '--database=somedb --cert-path=gs://speckletest/testcert.crt '
        '--pvk-path=gs://speckletest/testkey.pvk --prompt-for-pvk-password')

    self.AssertErrContains('Private Key Password:')
    self.AssertErrContains('PROMPT_CONTINUE')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.bak] into '
                           '[https://sqladmin.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))


class InstancesImportBakBetaTest(InstancesImportBakGATest,
                                 base.SqlMockTestBeta):
  pass


class InstancesImportBakAlphaTest(InstancesImportBakBetaTest,
                                  base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
