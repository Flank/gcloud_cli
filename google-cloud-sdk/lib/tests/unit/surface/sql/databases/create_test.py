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
"""Tests that exercise operations listing and executing."""

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class DatabasesInsertTest(base.SqlMockTestBeta):

  def testDatabasesInsert(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Insert.Expect(
        sqladmin.Database(
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            collation='another-collation',
            kind=u'sql#database'),
        sqladmin.Operation(name=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5'))

    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5',
            project=self.Project()),
        sqladmin.Operation(status=u'DONE'))

    self.Run('sql databases create mock-db --instance=mock-instance '
             '--collation=another-collation')
    self.AssertErrContains('Creating Cloud SQL database')
    self.AssertErrContains('Created database [mock-db].')
    self.AssertOutputContains("""\
collation: another-collation
instance: mock-instance
name: mock-db
project: {0}
""".format(self.Project()), normalize_space=True)

  def testDatabasesInsertAsync(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Insert.Expect(
        sqladmin.Database(
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            collation='another-collation',
            kind=u'sql#database'),
        sqladmin.Operation(name=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5'))

    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5',
            project=self.Project()),
        sqladmin.Operation(status=u'DONE'))

    self.Run('sql databases create mock-db --instance=mock-instance '
             '--collation=another-collation --async')
    self.AssertErrContains('Create in progress for database [mock-db].')
    self.AssertOutputContains('status: DONE')

  def testDatabasesInsertFailed(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Insert.Expect(
        sqladmin.Database(
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            kind=u'sql#database'),
        sqladmin.Operation(name='op1'))
    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation=u'op1',
            project=self.Project()),
        sqladmin.Operation(
            error=sqladmin.OperationErrors(errors=[
                sqladmin.OperationError(code='INTERNAL_ERROR')])))

    with self.assertRaises(exceptions.OperationError):
      self.Run('sql databases create mock-db --instance=mock-instance')


if __name__ == '__main__':
  test_case.main()
