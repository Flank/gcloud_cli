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

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class DatabasesDescribeTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testDatabasesDescribe(self):
    sqladmin = core_apis.GetMessagesModule('sqladmin', 'v1beta4')
    self.mocked_client.databases.Get.Expect(
        sqladmin.SqlDatabasesGetRequest(
            project=self.Project(),
            instance='mock-instance',
            database='mock-db'),
        sqladmin.Database(
            # pylint:disable=line-too-long
            project=self.Project(),
            instance='mock-instance',
            name='mock-db',
            charset='utf8',
            collation='some-collation',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db'.
            format(self.Project()),
            etag='\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
            kind='sql#database'))

    self.Run('sql databases describe mock-db --instance=mock-instance')
    self.AssertOutputContains(
        # pylint:disable=line-too-long
        """\
charset: utf8
collation: some-collation
etag: '\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"'
instance: mock-instance
kind: sql#database
name: mock-db
project: {0}
selfLink: https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db
""".format(self.Project()),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
