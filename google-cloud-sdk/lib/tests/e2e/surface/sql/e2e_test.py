# Copyright 2014 Google Inc. All Rights Reserved.
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

from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.sql import base


class MysqlE2ETest(base.MysqlIntegrationTestBase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)

  def testSQLCommands(self):
    self.CreateInstance()
    self.DoTestBackupList()
    self.DoTestInstanceOperations()
    self.DoTestConnect()
    self.DoTestOperations()

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

    # The first index of call_args is a list of ordered arguments the mock was
    # called with. The second index is a dict of keyword arguments.
    # Exec is called with just a single argument, a list of args to pass on to
    # the subprocess.
    exec_ordered_argumnents = exec_patched.call_args[0]
    subprocess_args = exec_ordered_argumnents[0]
    (actual_mysql_path, actual_host_flag, actual_ip_address, actual_user_flag,
     actual_username, actual_pass_flag) = subprocess_args
    self.assertEqual(mocked_mysql_path, actual_mysql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv6 address. IPv4 uses '.' instead of ':'.
    self.assertIn(':', actual_ip_address)
    self.assertEqual('-u', actual_user_flag)
    self.assertEqual('root', actual_username)
    self.assertEqual('-p', actual_pass_flag)

  @sdk_test_base.Retry(why=('Because sql backend service is flaky.'))
  def DoTestOperations(self):
    self.ClearOutput()
    self.Run('sql operations list --instance={0}'.format(self.test_instance))
    out = self.GetOutput()
    lines = out.split('\n')

    # First line is a header, next lines are the actual operations.
    # If we have less than 2 lines it means we have just a header.
    self.assertGreater(lines, 1,
                       'No operations available for this instance {0}'.format(
                           self.test_instance))

    # Grab first listed operation and describe it.
    operation_id = lines[1].split()[0]
    self.Run('sql operations describe {0}'.format(operation_id))


class PsqlE2ETest(base.PsqlIntegrationTestBase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(True)

  @test_case.Filters.RunOnlyWithEnv('KOKORO_ROOT', 'Needs to be run with ipv4.')
  def testSQLCommands(self):
    self.CreateInstance()
    self.DoTestConnect()

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

    # The first index of call_args is a list of ordered arguments the mock was
    # called with. The second index is a dict of keyword arguments.
    # Exec is called with just a single argument, a list of args to pass on to
    # the subprocess.
    exec_ordered_argumnents = exec_patched.call_args[0]
    subprocess_args = exec_ordered_argumnents[0]
    (actual_psql_path, actual_host_flag, actual_ip_address, actual_user_flag,
     actual_username, actual_pass_flag) = subprocess_args
    self.assertEqual(mocked_psql_path, actual_psql_path)
    self.assertEqual('-h', actual_host_flag)
    # Basic check that it's an IPv4 address. IPv4 uses '.' instead of ':'.
    self.assertIn('.', actual_ip_address)
    self.assertEqual('-U', actual_user_flag)
    self.assertEqual('root', actual_username)
    self.assertEqual('-W', actual_pass_flag)


if __name__ == '__main__':
  test_case.main()
