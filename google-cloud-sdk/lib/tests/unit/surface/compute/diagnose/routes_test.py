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
"""Tests for compute diagnose routes command."""

from __future__ import absolute_import
from __future__ import print_function
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.core import log
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class InvalidSSHMethodException(Exception):
  pass


class MockSSHCalls(object):
  """Class to be used as a side_effects for mock."""

  # Array of pairs (command_list, call_obj)
  # That override defaults calls
  def __init__(self):
    self._expected = []

  def AddExpected(self, command_list, call_obj):
    """Add an expected rule for the mock.

    This could be used for adding traceroutes to specific VMs.
    Args:
      command_list: The command list to expect
      call_obj: Object that can be called without arguments.
        Should return what the actual method returns and provoke
        the needed side effects.
    """
    self._expected.append((command_list, call_obj))

  def __call__(self, *args, **kwargs):
    command_list = []
    if 'command_list' in kwargs:
      command_list = kwargs['command_list']
    else:
      command_list = args[1]  # second argument

    # We check for any overrides
    for exp in self._expected:
      if command_list == exp[0]:
        return exp[1]

    # We see what kind of command we're mocking
    if command_list == TracerouteTest.CmdCheckTraceroute():
      return 0
    elif command_list == TracerouteTest.CmdObtainSelfIp():
      tmp_file = kwargs['explicit_output_file']
      if tmp_file:
        tmp_file.write('127.0.0.1 55555 22')
      return 0
    elif command_list == TracerouteTest.CmdReverseTraceroute():
      return 0
    else:
      log.warning('Unexpected ssh method called: %s' % command_list)
      return 1


class TracerouteTest(test_base.BaseSSHTest, test_case.WithInput):

  ###################################
  # SETUP
  ###################################

  def SetUp(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResources',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = test_resources.INSTANCES_V1

    # We mock the RunSubprocess
    subprocess_patcher = mock.patch(
        ('googlecloudsdk.command_lib.compute.diagnose.'
         'external_helper.RunSubprocess'),
        autospec=True)
    self.addCleanup(subprocess_patcher.stop)
    self.mock_run_subprocess = subprocess_patcher.start()
    self.mock_run_subprocess.return_value = None

    # We mock the SSH Commands
    ssh_command_patcher = mock.patch(
        ('googlecloudsdk.command_lib.compute.diagnose.'
         'external_helper.RunSSHCommandToInstance'),
        autospec=True)
    self.addCleanup(ssh_command_patcher.stop)
    self.mock_ssh_command = ssh_command_patcher.start()
    self.mock_ssh_command.return_value = 0  # Success

  ###################################
  # HELPER METHODS
  ###################################

  @staticmethod
  def FilterInstances(instances, names):
    new_instances = []
    for name in names:
      for instance in instances:
        if name == instance.name:
          new_instances.append(instance)
          break
    return new_instances

  ###################################
  # CMD FUNCTIONS
  ###################################

  @staticmethod
  def CmdCheckTraceroute():
    return ['which', 'traceroute']

  @staticmethod
  def CmdObtainSelfIp():
    return ['echo', '$SSH_CLIENT']

  @staticmethod
  def CmdTraceroute(instance):
    return ['traceroute', ssh_utils.GetExternalIPAddress(instance)]

  @staticmethod
  def CmdReverseTraceroute():
    return ['traceroute', '127.0.0.1']

  ###################################
  # ASSERTS
  ###################################

  def AssertZonalResources(self, filter_expr=None):
    self.mock_get_zonal_resources.assert_called_once_with(
        service=self.compute_v1.instances,
        project='my-project',
        requested_zones=[],
        filter_expr=filter_expr,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def AssertSubProcessCalls(self, command_list, times):
    # We obtain all the command lists (the actual command subprocessed)
    calls = self.mock_run_subprocess.call_args_list
    call_command_lists = TracerouteTest.ObtainCommandListsFromCalls(calls)
    # We count the ocurrences
    call_count = 0
    for call_command_list in call_command_lists:
      if command_list == call_command_list:
        call_count += 1
    # We verify
    if call_count != times:
      self.fail(
          'Expected %s to be called %s times, got %s instead. Command lists: %s'
          % (command_list, times, call_count, call_command_lists))

  def AssertSSHCalls(self, command_list, times):
    # We obtain the actual SSH calls
    calls = self.mock_ssh_command.call_args_list
    call_command_lists = TracerouteTest.ObtainCommandListsFromCalls(calls)
    # We count the occurrences
    call_count = 0
    for call_command_list in call_command_lists:
      if command_list == call_command_list:
        call_count += 1
    # We verify
    if call_count != times:
      self.fail(
          'Expected %s to be called %s times, got %s instead. Command lists: %s'
          % (command_list, times, call_count, call_command_lists))

  @staticmethod
  def ObtainCommandListsFromCalls(calls):
    command_lists = []
    for call in calls:
      args, kwargs = call  # pyling: disable=unused-variable
      command_list = []
      if 'command_list' in kwargs:
        command_list = kwargs['command_list']
      else:
        command_list = args[1]  # second argument
      command_lists.append(command_list)
    return command_lists

  ###################################
  # TESTS
  ###################################

  def testNormalCase(self):
    self.Run('compute diagnose routes')
    self.AssertZonalResources()
    # We check that we tracerouted once for each
    instances = test_resources.INSTANCES_V1
    for instance in instances:
      self.AssertSubProcessCalls(
          TracerouteTest.CmdTraceroute(instance), times=1)

  def testNameFiltering(self):
    instances_names = ['instance-1', 'instance-3']
    instances_str = ' '.join(instances_names)
    self.Run('compute diagnose routes {instances}'.format(
        instances=instances_str))
    self.AssertZonalResources()
    # Only instances 1 and 3 get tracerouted
    instances = test_resources.INSTANCES_V1
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[0]), times=1)
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[1]), times=0)
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[2]), times=1)

  def testRegexFiltering(self):
    regexp = 'instance-[12]'
    regex_instances = TracerouteTest.FilterInstances(
        test_resources.INSTANCES_V1, ['instance-1', 'instance-2'])
    self.mock_get_zonal_resources.return_value = regex_instances
    self.Run(
        'compute diagnose routes --regexp="{regexp}"'.format(regexp=regexp))
    self.AssertZonalResources(filter_expr='name eq {regexp}'.format(
        regexp=regexp))
    # Only instances 1 and 2 get tracerouted
    instances = test_resources.INSTANCES_V1
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[0]), times=1)
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[1]), times=1)
    self.AssertSubProcessCalls(
        TracerouteTest.CmdTraceroute(instances[2]), times=0)

  def testReverseTraceroute(self):
    self.mock_ssh_command.side_effect = MockSSHCalls()
    self.Run('compute diagnose routes --reverse-traceroute')
    self.AssertZonalResources()
    # Instances were tracerouted
    instances = test_resources.INSTANCES_V1
    for instance in instances:
      self.AssertSubProcessCalls(
          TracerouteTest.CmdTraceroute(instance), times=1)
    # Instances were checked
    self.AssertSSHCalls(TracerouteTest.CmdCheckTraceroute(), times=3)
    # Instances tracerouted back
    self.AssertSSHCalls(TracerouteTest.CmdReverseTraceroute(), times=3)

  def testNoTracerouteReverse(self):
    m = MockSSHCalls()
    # No traceroute found
    m.AddExpected(TracerouteTest.CmdCheckTraceroute(), lambda: 1)
    self.mock_ssh_command.side_effect = m
    self.Run('compute diagnose routes --reverse-traceroute')
    self.AssertZonalResources()
    # Instances were tracerouted
    instances = test_resources.INSTANCES_V1
    for instance in instances:
      self.AssertSubProcessCalls(
          TracerouteTest.CmdTraceroute(instance), times=1)
    # Instances were checked
    self.AssertSSHCalls(TracerouteTest.CmdCheckTraceroute(), times=3)
    # Instances tracerouted back
    self.AssertSSHCalls(TracerouteTest.CmdReverseTraceroute(), times=0)

  # ####################################
  # # DRY RUN TESTS
  # ####################################

  def testDryRun(self):
    dry_run_variant = '--dry-run'
    self.Run('compute diagnose routes {dry_run_variant}'.format(
        dry_run_variant=dry_run_variant))
    self.AssertZonalResources()
    self.mock_run_subprocess.assert_not_called()

  def testDryReverse(self):
    dry_run_variant = '--dry-run --reverse-traceroute'
    self.Run('compute diagnose routes {dry_run_variant}'.format(
        dry_run_variant=dry_run_variant))
    self.AssertZonalResources()
    self.mock_run_subprocess.assert_not_called()


if __name__ == '__main__':
  test_case.main()
