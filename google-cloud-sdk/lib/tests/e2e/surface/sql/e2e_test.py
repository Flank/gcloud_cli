# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class MysqlE2ETest(base.MysqlIntegrationTestBase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)

  @test_case.Filters.skip('network auth issues', 'b/144013563')
  def testSQLCommands(self):
    self.CreateInstance('D1')
    self.DoTestBackupList()
    self.DoTestInstanceOperations()
    self.DoTestConnect()
    # Test connect again to ensure that the formatting issue doesn't crop up.
    self.DoTestConnect()
    self.DoTestOperations()

  def testConnectWithProxy(self):
    self.CreateInstance('db-g1-small')
    self.DoTestConnectWithProxy()

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestBackupList(self):
    self.Run('sql backups list --instance={0}'.format(self.test_instance))

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestInstanceOperations(self):
    self.Run('sql instances list')
    self.Run('sql instances describe {0}'.format(self.test_instance))

    self.Run('sql instances reset-ssl-config {0}'.format(self.test_instance))
    self.Run('sql instances restart {0}'.format(self.test_instance))
    self.Run('sql instances patch {0} --tier=D0'.format(self.test_instance))

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestConnect(self):
    # Mock the fact that we have mysql in path.
    mocked_mysql_path = 'mysql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mysql_path)

    # Mock the fact that our machine has ipv6 connectivity.
    self.StartPatch(
        'googlecloudsdk.api_lib.sql.network.GetIpVersion', return_value=6)

    # Mock the actual execution of mysql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    self.Run('sql connect {0} --user root'.format(self.test_instance))

    self.assertTrue(exec_patched.called)

  def DoTestConnectWithProxy(self):
    # Mock the fact that we have mysql in path.
    mocked_mysql_path = 'mysql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_mysql_path)

    # Mock the actual execution of mysql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)
    self.Run('beta sql connect {0} --user root --port 9476 --quiet'.format(
        self.test_instance))

    self.assertTrue(exec_patched.called)

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestOperations(self):
    self.ClearOutput()
    self.Run('sql operations list --instance={0}'.format(self.test_instance))
    out = self.GetOutput()
    lines = out.split('\n')

    # First line is a header, next lines are the actual operations.
    # If we have less than 2 lines it means we have just a header.
    self.assertGreater(
        len(lines), 1, 'No operations available for this instance {0}'.format(
            self.test_instance))

    # Grab first listed operation and describe it.
    operation_id = lines[1].split()[0]
    self.Run('sql operations describe {0}'.format(operation_id))


class PsqlE2ETest(base.PsqlIntegrationTestBase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.CreateInstance('db-g1-small')

  @test_case.Filters.skip('network auth issues', 'b/144013563')
  @test_case.Filters.RunOnlyWithEnv('KOKORO_ROOT', 'Needs to be run with ipv4.')
  @test_case.Filters.DoNotRunOnMac('Most Macs used by Kokoro are IPv6; '
                                   'Cloud SQL only supports IPv4.')
  # b/141325243 expands on the above DoNotRun.
  def testSQLCommands(self):
    self.DoTestConnect()

  @sdk_test_base.Filters.RunOnlyInBundle
  def testConnectWithProxy(self):
    self.DoTestConnectWithProxy()

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestConnect(self):
    # Mock the fact that we have psql in path.
    mocked_psql_path = 'psql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_psql_path)

    # Mock the fact that our machine has ipv4 connectivity.
    self.StartPatch(
        'googlecloudsdk.api_lib.sql.network.GetIpVersion', return_value=4)

    # Mock the actual execution of psql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)

    self.Run('sql connect {0} --user root'.format(self.test_instance))

    self.assertTrue(exec_patched.called)

  def DoTestConnectWithProxy(self):
    # Mock the fact that we have psql in path.
    mocked_psql_path = 'psql'
    self.StartPatch(
        'googlecloudsdk.core.util.files.FindExecutableOnPath',
        return_value=mocked_psql_path)

    # Mock the actual execution of psql and assert it's called at the end.
    exec_patched = self.StartPatch(
        'googlecloudsdk.core.execution_utils.Exec', return_value=True)

    self.Run('beta sql connect {0} --user root --port 9477 --quiet'.format(
        self.test_instance))

    self.assertTrue(exec_patched.called)


if __name__ == '__main__':
  test_case.main()
