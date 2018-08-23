# -*- coding: utf-8 -*- #
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

"""Unit tests for SQL flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import instances
from googlecloudsdk.command_lib.sql import flags
from tests.lib import cli_test_base
from tests.lib import completer_test_base
from tests.lib import parameterized
from tests.lib.calliope import util
from tests.lib.surface.sql import base
from tests.lib.surface.sql import data


class CompleterTest(base.SqlMockTestBeta, completer_test_base.CompleterBase):

  def testDatabaseCompletion(self):
    self.mocked_client.databases.List.Expect(
        self.messages.SqlDatabasesListRequest(
            project=self.Project(), instance='mock-instance'),
        self.messages.DatabasesListResponse(
            kind='sql#databasesList',
            items=[
                self.messages.Database(
                    # pylint:disable=line-too-long
                    project=self.Project(),
                    instance='clone-instance-7',
                    name='mock-db-1',
                    charset='utf-8',
                    collation='some-collation',
                    selfLink=
                    'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db-1'.
                    format(self.Project()),
                    etag=
                    '\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahg\"',
                    kind='sql#database'),
                self.messages.Database(
                    # pylint:disable=line-too-long
                    project=self.Project(),
                    instance='clone-instance-7',
                    name='mock-db-2',
                    charset='utf-8',
                    collation='some-collation',
                    selfLink=
                    'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/mock-instance/databases/mock-db-2'.
                    format(self.Project()),
                    etag=
                    '\"cO45wbpDRrmLAoMK32AI7It1bHE/kawIL3mk4XzLj-zNOtoR5bf2Ahe\"',
                    kind='sql#database'),
            ]),
    )
    completer = self.Completer(
        flags.DatabaseCompleter,
        args={'--instance': 'mock-instance'},
        cli=self.cli)
    self.assertCountEqual(['mock-db-1', 'mock-db-2'],
                          completer.Complete('', self.parameter_info))

  def testInstanceCompletion(self):
    instances_list = data.GetDatabaseInstancesListOfTwo(
    ) + data.GetDatabaseInstancesListOfOne()
    self.StartObjectPatch(
        instances._BaseInstances,
        'GetDatabaseInstances',
        return_value=instances_list)
    completer = self.Completer(
        flags.InstanceCompleter,
        cli=self.cli)
    self.assertCountEqual(
        ['backupless-instance1', 'backupless-instance2', 'testinstance'],
        completer.Complete('', self.parameter_info))

  def testUserCompletion(self):
    self.mocked_client.users.List.Expect(
        self.messages.SqlUsersListRequest(
            project=self.Project(), instance='my_instance'),
        self.messages.UsersListResponse(items=[
            self.messages.User(
                project=self.Project(),
                instance='my_instance',
                name='my_username',
                host='my_host')
        ]))
    completer = self.Completer(
        flags.UserCompleter,
        args={'--instance': 'my_instance'},
        cli=self.cli)
    self.assertCountEqual(['my_username'],
                          completer.Complete('', self.parameter_info))


class FlagsTest(cli_test_base.CliTestBase, parameterized.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    flags.AddAuthorizedNetworks(self.parser)

  @parameterized.parameters(
      ('1.2.3.4/32',),
      ('0.0.0.0/0',),
      ('1.2.3.4',),
      ('255.255.255.255',),
  )
  def testCidr_Good(self, networks):
    result = self.parser.parse_args(['--authorized-networks', networks])
    self.assertEqual(result.authorized_networks, networks.split(','))

  @parameterized.parameters(
      ('1.2.3.256/32',),
      ('1.2.3.4/-1',),
      ('0.0.0.0/',),
      ('0.0.0.0/33',),
      ('0.0.0.0/255',),
      ('abcd',),
      ('abcd-foobar',),
  )
  def testCidr_Bad(self, networks):
    with self.AssertRaisesArgumentErrorMatches(
        'Must be specified in CIDR notation'):
      self.parser.parse_args(['--authorized-networks', networks])


if __name__ == '__main__':
  completer_test_base.main()
