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

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class DatabasesPatchTest(base.SqlMockTestBeta):

  def testDatabasesPatch(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Get.Expect(
        sqladmin.SqlDatabasesGetRequest(
            instance='mock-instance',
            project=self.Project(),
            database='mock-db'),
        sqladmin.Database(
            # pylint:disable=line-too-long
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            charset='utf-8',
            collation='some-collation',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db'.
            format(self.Project()),
            etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
            kind=u'sql#database'))
    self.mocked_client.databases.Patch.Expect(
        sqladmin.SqlDatabasesPatchRequest(
            project=self.Project(),
            instance='mock-instance',
            database='mock-db',
            databaseResource=sqladmin.Database(
                project=self.Project(),
                instance='mock-instance',
                name='mock-db',
                collation='another-collation',
                kind=u'sql#database')),
        sqladmin.Operation(name=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5'))

    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5',
            project=self.Project(),),
        sqladmin.Operation(status=u'DONE'))
    self.mocked_client.databases.Get.Expect(
        sqladmin.SqlDatabasesGetRequest(
            instance='mock-instance',
            project=self.Project(),
            database='mock-db'),
        sqladmin.Database(
            # pylint:disable=line-too-long
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            charset='utf-8',
            collation='another-collation',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db'.
            format(self.Project()),
            etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
            kind=u'sql#database'))

    self.Run('sql databases patch mock-db --instance=mock-instance '
             '--collation=another-collation')
    self.AssertErrContains('Patching Cloud SQL database')
    self.AssertErrContains('Updated database [mock-db].')
    self.AssertOutputContains(
        # pylint:disable=line-too-long
        """\
charset: utf-8
collation: another-collation
etag: '\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"'
instance: mock-instance
kind: sql#database
name: mock-db
project: {0}
selfLink: https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db
""".format(self.Project()),
        normalize_space=True)

  def testDatabasesPatchWithDiff(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Get.Expect(
        sqladmin.SqlDatabasesGetRequest(
            instance='mock-instance',
            project=self.Project(),
            database='mock-db'),
        sqladmin.Database(
            # pylint:disable=line-too-long
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            charset='utf-8',
            collation='some-collation',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db'.
            format(self.Project()),
            etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
            kind=u'sql#database'))
    self.mocked_client.databases.Patch.Expect(
        sqladmin.SqlDatabasesPatchRequest(
            project=self.Project(),
            instance='mock-instance',
            database='mock-db',
            databaseResource=sqladmin.Database(
                project=self.Project(),
                instance='mock-instance',
                name='mock-db',
                charset='another-charset',
                collation='another-collation',
                kind=u'sql#database')),
        sqladmin.Operation(name=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5'))

    self.mocked_client.operations.Get.Expect(
        sqladmin.SqlOperationsGetRequest(
            operation=u'd11c5da9-8ca5-4add-8cfe-d564b57fe4c5',
            project=self.Project(),),
        sqladmin.Operation(status=u'DONE'))
    self.mocked_client.databases.Get.Expect(
        sqladmin.SqlDatabasesGetRequest(
            instance='mock-instance',
            project=self.Project(),
            database='mock-db'),
        sqladmin.Database(
            # pylint:disable=line-too-long
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            charset='another-charset',
            collation='another-collation',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db'.
            format(self.Project()),
            etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
            kind=u'sql#database'))

    self.Run('sql databases patch mock-db --instance=mock-instance '
             '--collation=another-collation --charset=another-charset --diff')
    self.AssertErrContains('Patching Cloud SQL database')
    self.AssertErrContains('Updated database [mock-db].')
    self.AssertOutputContains("""\
-charset: utf-8
-collation: some-collation
+charset: another-charset
+collation: another-collation
""", normalize_space=True)


if __name__ == '__main__':
  test_case.main()
