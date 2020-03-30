# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseDatabasesListTest(object):

  def testDatabasesList(self):
    sqladmin = core_apis.GetMessagesModule('sql', 'v1beta4')
    self.mocked_client.databases.List.Expect(
        sqladmin.SqlDatabasesListRequest(
            project=self.Project(), instance='mock-instance'),
        sqladmin.DatabasesListResponse(
            kind='sql#databasesList',
            items=[
                sqladmin.Database(
                    # pylint:disable=line-too-long
                    project=self.Project(),
                    instance='clone-instance-7',
                    name='mock-db-1',
                    charset='utf-8',
                    collation='some-collation',
                    selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/databases/mock-db-name'
                    .format(self.Project()),
                    etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
                    kind='sql#database'),
                sqladmin.Database(
                    # pylint:disable=line-too-long
                    project=self.Project(),
                    instance='clone-instance-7',
                    name='mock-db-2',
                    charset='utf-8',
                    collation='some-collation',
                    selfLink='https://sqladmin.googleapis.com/sql/v1beta4/projects/{0}/databases/mock-db-name'
                    .format(self.Project()),
                    etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahe\"',
                    kind='sql#database'),
            ]),
    )

    self.Run('sql databases list --instance=mock-instance')
    self.AssertOutputContains("""\
NAME CHARSET COLLATION
mock-db-1 utf-8 some-collation
mock-db-2 utf-8 some-collation
""", normalize_space=True)


class DatabasesListGATest(_BaseDatabasesListTest, base.SqlMockTestGA):
  pass


class DatabasesListBetaTest(_BaseDatabasesListTest, base.SqlMockTestBeta):
  pass


class DatabasesListAlphaTest(_BaseDatabasesListTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
