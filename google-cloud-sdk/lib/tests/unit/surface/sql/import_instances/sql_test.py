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
"""Tests that exercise instance imports from sql."""

from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesImportSqlTest(object):
  # pylint:disable=g-tzinfo-datetime

  def _ExpectImport(self, database=None, user=None):
    # Generate SQL import context.
    import_context = self.messages.ImportContext(
        database=database,
        fileType='SQL',
        kind='sql#importContext',
        uri='gs://speckletest/testinstance.gz',
        importUser=user)

    # Mock out endpoints for import.
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=import_context),
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                875000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=import_context,
            targetId='testinstance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='ffa26eae-a675-47f1-a8c8-579849098aeb',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/ffa26eae-a675-47f1-a8c8-579849098aeb'.
            format(self.Project()),
            operationType='IMPORT',
            status='PENDING',
            user='170350250316@developer.gserviceaccount.com'))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='ffa26eae-a675-47f1-a8c8-579849098aeb',
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                875000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                925000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                39,
                764000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=import_context,
            targetId='testinstance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='ffa26eae-a675-47f1-a8c8-579849098aeb',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/ffa26eae-a675-47f1-a8c8-579849098aeb'.
            format(self.Project()),
            operationType='IMPORT',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com'))

  def testSimpleImport(self):
    self._ExpectImport()
    self.WriteInput('y')

    self.Run('sql import sql testinstance '
             'gs://speckletest/testinstance.gz')

    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrContains(
        'Imported data from '
        '[gs://speckletest/testinstance.gz] into '
        '[https://www.googleapis.com/sql/v1beta4'
        '/projects/{0}/instances/testinstance].'.format(self.Project()))

  def testSimpleImportAsync(self):
    self._ExpectImport()
    self.WriteInput('y')

    self.Run('sql import sql testinstance '
             'gs://speckletest/testinstance.gz --async')

    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrNotContains(
        'Imported data from '
        '[gs://speckletest/testinstance.gz] into '
        '[https://www.googleapis.com/sql/v1beta4'
        '/projects/{0}/instances/testinstance].'.format(self.Project()))

  def testFailedImport(self):
    self.mocked_client.instances.Import.Expect(
        self.messages.SqlInstancesImportRequest(
            instance='testinstance',
            instancesImportRequest=self.messages.InstancesImportRequest(
                importContext=self.messages.ImportContext(
                    database=None,
                    fileType='SQL',
                    kind='sql#importContext',
                    uri='gs://nosuchbucket/testinstance.gz')),
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                875000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=None,
            endTime=None,
            error=None,
            exportContext=None,
            importContext=self.messages.ImportContext(
                database=None,
                fileType='SQL',
                kind='sql#importContext',
                uri='gs://nosuchbucket/testinstance.gz'),
            targetId='testinstance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/bf159e2a-fe9b-4eaa-9d88-00d801fe9e04'.
            format(self.Project()),
            operationType='IMPORT',
            status='PENDING',
            user='170350250316@developer.gserviceaccount.com'))
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            project=self.Project()),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                875000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                18,
                925000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                13,
                21,
                13,
                39,
                764000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=self.messages.OperationErrors(
                errors=[
                    self.messages.OperationError(
                        code='ERROR_RESOURCE_DOES_NOT_EXIST',
                        kind='sql#operationError'),
                ],
                kind='sql#operationErrors'),
            exportContext=None,
            importContext=self.messages.ImportContext(
                database=None,
                fileType='SQL',
                kind='sql#importContext',
                uri='gs://nosuchbucket/testinstance.gz'),
            targetId='testinstance',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/testinstance'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='bf159e2a-fe9b-4eaa-9d88-00d801fe9e04',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/bf159e2a-fe9b-4eaa-9d88-00d801fe9e04'.
            format(self.Project()),
            operationType='IMPORT',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com'))

    with self.assertRaises(exceptions.OperationError):
      self.Run('sql import sql testinstance '
               'gs://nosuchbucket/testinstance.gz')
    self.AssertErrContains('ERROR_RESOURCE_DOES_NOT_EXIST')

  def testImportNoConfirmCancels(self):
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('sql import sql testinstance '
               'gs://nosuchbucket/testinstance.gz')
    self.AssertErrContains(
        'Data from [gs://nosuchbucket/testinstance.gz] will be imported to '
        '[testinstance].')
    self.AssertErrContains('Do you want to continue (Y/n)?')

  def testDatabaseImport(self):
    self._ExpectImport(database='somedb')
    self.WriteInput('y')

    self.Run('sql import sql testinstance '
             'gs://speckletest/testinstance.gz --database=somedb')

    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrContains('Imported data from '
                           '[gs://speckletest/testinstance.gz] into '
                           '[https://www.googleapis.com/sql/v1beta4'
                           '/projects/{0}/instances/testinstance].'.format(
                               self.Project()))

  def testImportWithUser(self):
    self._ExpectImport(user='someuser')
    self.WriteInput('y')

    self.Run('sql import sql testinstance '
             'gs://speckletest/testinstance.gz --user=someuser')

    self.AssertErrContains('Do you want to continue (Y/n)?')
    self.AssertErrContains(
        'Imported data from '
        '[gs://speckletest/testinstance.gz] into '
        '[https://www.googleapis.com/sql/v1beta4'
        '/projects/{0}/instances/testinstance].'.format(self.Project()))


class InstancesImportSqlBetaTest(_BaseInstancesImportSqlTest,
                                 base.SqlMockTestBeta):
  pass


class InstancesImportSqlGATest(_BaseInstancesImportSqlTest, base.SqlMockTestGA):
  pass


if __name__ == '__main__':
  test_case.main()
