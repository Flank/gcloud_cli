# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for compute diagnose sosreport command."""

from __future__ import absolute_import
from __future__ import print_function

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import test_case
from tests.lib.surface.compute import test_base

import mock

SOSREPORT_INSTALL_PATH = "/tmp/git-sosreport"
REPORTS_PATH = "/tmp/gcloud-sosreport"
RELEASE_TRACK = "alpha"
PYTHON_PATH = "/custom/python/path"

###########################################################
# Fake instance created in order to be queried over
###########################################################

MESSAGES = apis.GetMessagesModule("compute", "v1")
INSTANCE = MESSAGES.Instance(
    id=11111,
    name="instance-1",
    networkInterfaces=[
        MESSAGES.NetworkInterface(
            accessConfigs=[
                MESSAGES.AccessConfig(
                    name="external-nat", natIP="23.251.133.75"),
            ],),
    ],
    status=MESSAGES.Instance.StatusValueValuesEnum.RUNNING,
    selfLink=("https://www.googleapis.com/compute/v1/projects/my-project/"
              "zones/zone-1/instances/instance-1"),
    zone=("https://www.googleapis.com/compute/v1/projects/my-project/"
          "zones/zone-1"))


class MockSSHCalls(object):
  """Class to be used as a side_effects for mock.

  In this case is used to write into the temp file used
  by one SSH call to be able to read the output of an
  ssh command.
  """

  def SetReturnValue(self, value):
    self._return_value = value

  def __call__(self, *args, **kwargs):
    tmp_file = kwargs.get("explicit_output_file")
    if tmp_file:
      tmp_file.write(self._return_value)
    return 0


class SosReportTest(test_base.BaseSSHTest, test_case.WithInput):

  ###################################
  # SETUP
  ###################################

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

    self.make_requests.side_effect = iter([
        [INSTANCE],
        [self.project_resource],
    ])

    # We mock the calls to the SSH helper
    ssh_command_patcher = mock.patch(
        ("googlecloudsdk.command_lib.compute.diagnose."
         "external_helper.RunSSHCommandToInstance"),
        autospec=True)
    self.addCleanup(ssh_command_patcher.stop)
    self.mock_ssh_command = ssh_command_patcher.start()
    self.mock_ssh_command.return_value = 0  # Success

    # We mock the CallSubprocess helper
    subprocess_patcher = mock.patch(
        ("googlecloudsdk.command_lib.compute.diagnose."
         "external_helper.CallSubprocess"),
        autospec=True)
    self.addCleanup(subprocess_patcher.stop)
    self.mock_run_subprocess = subprocess_patcher.start()
    self.mock_run_subprocess.return_value = None

  ###################################
  # ASSERTS
  ###################################

  def ObtainCommandListsFromCalls(self, calls):
    """Extracts the calls from a mock calls list.

    Args:
      calls: The call list expected to be checked

    Returns:
      Object with the command list and whether the call was a dry-run.
    """
    command_lists = []
    for call in calls:
      args, kwargs = call  # pyling: disable=unused-variable
      command_list = []
      if "command_list" in kwargs:
        command_list = list(kwargs["command_list"])
      else:
        command_list = list(args[1])  # second argument

      # We add whether it was a dry-run
      dry_run = kwargs.get("dry_run")

      # The object to return
      command_object = {
          "dry_run": dry_run,
          "command_list": command_list,
      }
      # A weird way to obtain what flags were effectivelly specified
      # to the command
      if "args" in kwargs:
        command_object["specified_args"] = kwargs["args"]

      command_lists.append(command_object)
    return command_lists

  def AssertSSHCall(self, command_list, is_dry_run=False):
    """Assert than a given SSH command was called.

    Args:
      command_list: The SSH command to use.
      is_dry_run: Whether the SSH call should be a dry-run.

    Returns:
      Object with information about the call. Contains the SSH call,
      the actual gcloud argument object and whether the call is dry_run.
    """

    # We obtain the actual SSH calls
    calls = self.mock_ssh_command.call_args_list
    call_objects = self.ObtainCommandListsFromCalls(calls)
    # We count the occurrences
    call_object = None
    for actual_call_object in call_objects:
      actual_command_list = actual_call_object["command_list"]
      if command_list == actual_command_list:
        call_object = actual_call_object
        break

    # We verify
    if not call_object:
      call_command_lists = [x["command_list"] for x in call_objects]
      self.fail("Expected {cmd} to be called. Command lists: {cmd_list}".format(
          cmd=command_list, cmd_list=call_command_lists))

    if is_dry_run != call_object["dry_run"]:
      msg = ("Expected {cmd} to be be called with dry_run {dry_run}. "
             "Instead got {dry_run_result}")
      self.fail(msg.format(cmd=command_list,
                           dry_run=call_object["dry_run"],
                           dry_run_result=is_dry_run))
    return call_object

  def AssertSSHCallCount(self, call_count):
    """Assert than certain amount of SSH calls were made."""
    calls = self.mock_ssh_command.call_args_list
    call_command_list = self.ObtainCommandListsFromCalls(calls)
    actual_call_count = len(call_command_list)
    if call_count != actual_call_count:
      self.fail("Expected %s ssh calls, got %s. Calls: %s" %
                (call_count, actual_call_count, call_command_list))

  def AssertSubProcessCalls(self, command_list, is_dry_run=False):
    """Assert than a given subprocess call was made."""
    # We obtain all the command lists (the actual command subprocessed)
    calls = self.mock_run_subprocess.call_args_list
    call_command_lists = self.ObtainCommandListsFromCalls(calls)

    # We count the occurrences
    call_object = None
    for call_command_object in call_command_lists:
      if command_list == call_command_object["command_list"]:
        call_object = call_command_object

    # We verify
    if not call_object:
      self.fail("Expected {cmd} to be called. Command lists: {cmd_list}".format(
          cmd=command_list, cmd_list=call_command_lists))

    if is_dry_run != call_object["dry_run"]:
      msg = ("Expected {cmd} to be be called with dry_run {dry_run}. "
             "Instead got {dry_run_result}")
      self.fail(msg.format(cmd=command_list,
                           dry_run=call_object["dry_run"],
                           dry_run_result=is_dry_run))

  def AssertSubProcessCallCount(self, call_count):
    """Assert than certain amount of subprocess calls were made."""
    calls = self.mock_run_subprocess.call_args_list
    call_command_list = self.ObtainCommandListsFromCalls(calls)
    actual_call_count = len(call_command_list)
    if call_count != actual_call_count:
      self.fail("Expected %s subprocess calls, got %s. Calls: %s" %
                (call_count, actual_call_count, call_command_list))

  def AssertSSHArgs(self, ssh_args, golden):

    self.assertTrue(hasattr(ssh_args, "force_key_file_overwrite"))
    self.assertTrue(ssh_args.force_key_file_overwrite)

    self.assertTrue(hasattr(ssh_args, "plain"))
    self.assertTrue(ssh_args.plain)

    self.assertTrue(hasattr(ssh_args, "ssh_flag"))
    self.assertIn(golden["ssh_flag"], ssh_args.ssh_flag)

    self.assertTrue(hasattr(ssh_args, "ssh_key_file"))
    self.assertEqual(ssh_args.ssh_key_file, golden["ssh_key_file"])

    self.assertTrue(hasattr(ssh_args, "strict_host_key_checking"))
    self.assertEqual(ssh_args.strict_host_key_checking,
                     golden["ssh_strict_host_key_checking"])

    self.assertTrue(hasattr(ssh_args, "user"))
    self.assertEqual(ssh_args.user, golden["ssh_user"])

  ###################################
  # TESTS
  ###################################

  def testNormalCase(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH

    # We need the first command to fail
    self.mock_ssh_command.side_effect = [1, 0, 0, 0, 0, 0, 0]  # Error

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name} --zone={zone}
             """.format(name=INSTANCE.name, zone=INSTANCE.zone))

    # VERIFY
    # We assert on the amount of calls
    self.AssertSSHCallCount(7)
    self.AssertSSHCall(["ls", os.path.join(install_path, "sosreport")])
    self.AssertSSHCall(["mkdir", "-p", install_path])
    self.AssertSSHCall(
        ["git", "clone", "https://github.com/sosreport/sos.git", install_path])
    self.AssertSSHCall(["mkdir", "-p", reports_path])
    self.AssertSSHCall([
        "sudo",
        os.path.join(install_path, "sosreport"), "--batch",
        "--compression-type", "gzip", "--config-file",
        os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
    ])
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")])
    self.AssertSSHCall([
        "ls", "-t",
        os.path.join(reports_path, "*.tar.gz"), "|", "head", "-n", "1"
    ])

  def testCustomPythonPath(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH
    python_path = PYTHON_PATH

    # We need the first command to fail
    self.mock_ssh_command.side_effect = [1, 0, 0, 0, 0, 0, 0]  # Error

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name}
             --zone={zone}
             --python-path={python_path}
             """.format(
                 name=INSTANCE.name,
                 zone=INSTANCE.zone,
                 python_path=python_path))

    # VERIFY
    # We assert on the amount of calls
    self.AssertSSHCallCount(7)
    self.AssertSSHCall(["ls", os.path.join(install_path, "sosreport")])
    self.AssertSSHCall(["mkdir", "-p", install_path])
    self.AssertSSHCall(
        ["git", "clone", "https://github.com/sosreport/sos.git", install_path])
    self.AssertSSHCall(["mkdir", "-p", reports_path])
    self.AssertSSHCall([
        "sudo", python_path,
        os.path.join(install_path, "sosreport"), "--batch",
        "--compression-type", "gzip", "--config-file",
        os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
    ])
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")])
    self.AssertSSHCall([
        "ls", "-t",
        os.path.join(reports_path, "*.tar.gz"), "|", "head", "-n", "1"
    ])

  def testWithSosReportAlreadyInstalled(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name} --zone={zone}
             """.format(name=INSTANCE.name, zone=INSTANCE.zone))

    # VERIFY
    # We assert on the amount of calls
    self.AssertSSHCallCount(5)
    self.AssertSSHCall(["ls", os.path.join(install_path, "sosreport")])
    self.AssertSSHCall(["mkdir", "-p", reports_path])
    self.AssertSSHCall([
        "sudo",
        os.path.join(install_path, "sosreport"), "--batch",
        "--compression-type", "gzip", "--config-file",
        os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
    ])
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")])
    self.AssertSSHCall([
        "ls", "-t",
        os.path.join(reports_path, "*.tar.gz"), "|", "head", "-n", "1"
    ])

  def testWithCustomPath(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = "/custom/install/path"
    reports_path = "/custom/report/path"

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name}
             --zone={zone}
             --sosreport-install-path="{install_path}"
             --reports-path="{reports_path}"
             """.format(
                 name=INSTANCE.name,
                 zone=INSTANCE.zone,
                 install_path=install_path,
                 reports_path=reports_path))

    # VERIFY
    # We assert on the amount of calls
    self.AssertSSHCallCount(5)
    self.AssertSSHCall(["ls", os.path.join(install_path, "sosreport")])
    self.AssertSSHCall(["mkdir", "-p", reports_path])
    self.AssertSSHCall([
        "sudo",
        os.path.join(install_path, "sosreport"), "--batch",
        "--compression-type", "gzip", "--config-file",
        os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
    ])
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")])
    self.AssertSSHCall([
        "ls", "-t",
        os.path.join(reports_path, "*.tar.gz"), "|", "head", "-n", "1"
    ])

  def testWithCopyOver(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH
    report_filepath = "/path/to/sosreport/file"
    download_dir = "/local/dir"

    # Create a side effect generator than will return (and run the
    # expected side effect!) for each moment
    ssh_mock = MockSSHCalls()
    ssh_mock.SetReturnValue(report_filepath)
    context = {"call_times": 0}

    def SideEffectGenerator(*args, **kwargs):
      call_times = context["call_times"]
      context["call_times"] += 1
      if call_times == 0:
        return 1
      if call_times in [1, 2, 3]:
        return 0
      return ssh_mock(*args, **kwargs)

    self.mock_ssh_command.side_effect = SideEffectGenerator

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name}
             --zone={zone}
             --download-dir="{download_dir}"
             """.format(
                 name=INSTANCE.name,
                 zone=INSTANCE.zone,
                 download_dir=download_dir))

    # VERIFY
    # We assert on the amount of calls
    self.AssertSSHCallCount(7)
    self.AssertSSHCall(["ls", os.path.join(install_path, "sosreport")])
    self.AssertSSHCall(["mkdir", "-p", install_path])
    self.AssertSSHCall(
        ["git", "clone", "https://github.com/sosreport/sos.git", install_path])
    self.AssertSSHCall(["mkdir", "-p", reports_path])
    self.AssertSSHCall([
        "sudo",
        os.path.join(install_path, "sosreport"), "--batch",
        "--compression-type", "gzip", "--config-file",
        os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
    ])
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")])
    self.AssertSSHCall([
        "ls", "-t",
        os.path.join(reports_path, "*.tar.gz"), "|", "head", "-n", "1"
    ])
    self.AssertSubProcessCalls([
        "gcloud", "compute", "scp", "--zone", INSTANCE.zone,
        INSTANCE.name + ":" + report_filepath,
        os.path.join(download_dir, "file")
    ])

  def testDryRun(self):
    # SETUP
    user = ssh.GetDefaultSshUsername()
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH

    # We need the first command to fail
    self.mock_ssh_command.side_effect = [1, 0, 0, 0, 0, 0, 0]  # Error

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name}
             --zone={zone}
             --dry-run
             """.format(name=INSTANCE.name, zone=INSTANCE.zone))

    # Dry run does not call SSH
    self.AssertSSHCallCount(6)

    self.AssertSSHCall(
        ["ls", os.path.join(install_path, "sosreport")], is_dry_run=True)
    self.AssertSSHCall(["mkdir", "-p", install_path], is_dry_run=True)
    self.AssertSSHCall(
        ["git", "clone", "https://github.com/sosreport/sos.git", install_path],
        is_dry_run=True)
    self.AssertSSHCall(["mkdir", "-p", reports_path], is_dry_run=True)
    self.AssertSSHCall(
        [
            "sudo",
            os.path.join(install_path, "sosreport"), "--batch",
            "--compression-type", "gzip", "--config-file",
            os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
        ],
        is_dry_run=True)
    self.AssertSSHCall(
        ["sudo", "chown", user,
         os.path.join(reports_path, "*")], is_dry_run=True)

  def testSSHArgs(self):
        # SETUP
    install_path = SOSREPORT_INSTALL_PATH
    reports_path = REPORTS_PATH
    ssh_flag = "-vvv"
    ssh_key_file = "/PATH/TO/KEY"
    ssh_strict_host_key_checking = "yes"
    ssh_user = "TEST_USER"

    # We need the first command to fail
    self.mock_ssh_command.side_effect = [1, 0, 0, 0, 0, 0, 0]  # Error

    # EXECUTE
    self.Run("""
             compute diagnose sosreport {name}
             --zone={zone}
             --dry-run

             --force-key-file-overwrite
             --plain
             --ssh-flag={ssh_flag}
             --ssh-key-file={ssh_key_file}
             --strict-host-key-checking={ssh_host_key_checking}
             --user={ssh_user}
             """.format(name=INSTANCE.name,
                        zone=INSTANCE.zone,
                        ssh_flag=ssh_flag,
                        ssh_key_file=ssh_key_file,
                        ssh_host_key_checking=ssh_strict_host_key_checking,
                        ssh_user=ssh_user
                       ))

    # Dry run does not call SSH
    self.AssertSSHCallCount(6)

    golden_ssh_args = {
        "ssh_flag": ssh_flag,
        "ssh_key_file": ssh_key_file,
        "ssh_strict_host_key_checking": ssh_strict_host_key_checking,
        "ssh_user": ssh_user,
    }

    res = self.AssertSSHCall(
        ["ls", os.path.join(install_path, "sosreport")], is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

    res = self.AssertSSHCall(["mkdir", "-p", install_path], is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

    res = self.AssertSSHCall(
        ["git", "clone", "https://github.com/sosreport/sos.git", install_path],
        is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

    res = self.AssertSSHCall(["mkdir", "-p", reports_path], is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

    res = self.AssertSSHCall(
        [
            "sudo",
            os.path.join(install_path, "sosreport"), "--batch",
            "--compression-type", "gzip", "--config-file",
            os.path.join(install_path, "sos.conf"), "--tmp-dir", reports_path
        ],
        is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

    res = self.AssertSSHCall(
        ["sudo", "chown", ssh_user,
         os.path.join(reports_path, "*")], is_dry_run=True)
    self.AssertSSHArgs(res["specified_args"], golden_ssh_args)

if __name__ == "__main__":
  test_case.main()
