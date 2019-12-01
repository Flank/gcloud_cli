# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Integration tests for connecting to instances with ssh."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.command_lib.util.ssh import ssh
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class _SSHCommandOutputCapture(ssh.SSHCommand):
  """Class used to inject an output file argument into SSHCommand.Run calls.

  Stdout cannot be easily captured as ssh is called in a subprocess without
  stdout/stderr mapped to pipes. This class is used as an alternative to avoid
  supporting test time file output in the command or ssh code.
  """

  stdout_capture = None

  def Run(self, *args, **kwargs):
    kwargs['explicit_output_file'] = self.stdout_capture
    return super(_SSHCommandOutputCapture, self).Run(*args, **kwargs)


class SSHTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.stdout_capture_path = self.Touch(self.temp_path)
    self.stdout_capture = io.open(self.stdout_capture_path, 'w+')
    _SSHCommandOutputCapture.stdout_capture = self.stdout_capture
    self.StartObjectPatch(ssh, 'SSHCommand', new=_SSHCommandOutputCapture)

  def TearDown(self):
    self.stdout_capture.close()

  def testSSH(self):
    self._TestInstanceCreation()
    self._TestUpdateMetadata()
    self._TestSSHCommand()
    self._TestSSHKeyManagement()
    # TODO(b/33475433): The serial port host doesn't seem to be reachable
    # self._TestConnectToSerialPort()

  def testSSHIapTunnel(self):
    self._TestInstanceCreation()
    self._TestUpdateMetadata()
    self._TestSSHCommandIapTunnel()

  @test_case.Filters.skipAlways('Timing out', 'b/144084650')
  def testSSHHostKeyPublishing(self):
    self._TestInstanceCreation(metadata={'enable-guest-attributes': 'true'})
    self._TestSSHCommandStrictHostKeyChecking()

  def _TestUpdateMetadata(self):
    # Store SSH keys in instance metadata, to minimize contention in the
    # project metadata.
    self.Run('compute instances add-metadata {0} --zone {1} '
             '--metadata block-project-ssh-keys=true,'
             'serial-port-enable=true'.format(self.instance_name, self.zone))

  @sdk_test_base.Retry(why='Eventual consistency is the new broken',
                       max_retrials=12, sleep_ms=5000)
  def _TestSSHCommand(self):
    self.Run('compute ssh --quiet {0} --zone {1} --command hostname'
             .format(self.instance_name, self.zone))

    self.AssertFileContains(self.instance_name, self.stdout_capture_path)

    # The key for the instance should be added to the known hosts file after
    # the first run, so we should be able to explicitly pass
    # --strict-host-key-checking=yes here and have the command succeed. (On
    # Windows, --strict-host-key-checking=yes is a noop.)
    self.Run('compute ssh --quiet {0} --zone {1} '
             '--strict-host-key-checking=yes --command "expr 12300 + 45"'
             .format(self.instance_name, self.zone))

    self.AssertFileContains('12345', self.stdout_capture_path)

    # If any stdout/err, delete it in case future code looks at stdout/err
    self.ClearOutput()
    self.ClearErr()

  @sdk_test_base.Retry(why=('ESv2 provides no SLO, thus AMDC and AP are not '
                            'completely reliable, and retrying might help '
                            'tolerate errors.'),
                       max_retrials=12, sleep_ms=5000)
  def _TestSSHCommandIapTunnel(self):
    self.Run('compute ssh --quiet {0} --zone {1} --tunnel-through-iap '
             '--command "expr 12300 + 45"'
             .format(self.instance_name, self.zone))

    # The output path is random on each test, so it's fine to reuse 12345 value
    self.AssertFileContains('12345', self.stdout_capture_path)

    # If any stdout/err, delete it in case future code looks at stdout/err
    self.ClearOutput()
    self.ClearErr()

  def _TestSSHKeyManagement(self):
    self.assertTrue(os.path.exists(self.private_key_file))

    with open(self.public_key_file) as pub_key:
      public_key = pub_key.read().strip()
    # Keys created on Windows have backslashes in the username that get escaped
    # in the JSON output.
    public_key = public_key.replace('\\', '\\\\')
    self.Run('compute instances describe {0} --zone {1} '
             '--format="value(metadata)"'.format(self.instance_name, self.zone))
    self.AssertNewOutputContains(public_key)

  def _TestConnectToSerialPort(self):
    # We can't actually interact with the serial port, so we simply check to
    # make sure that we successfully connect.
    self.Run('compute connect-to-serial-port {0} --zone {1} --quiet '
             '--port 2'.format(self.instance_name, self.zone))

    # Note, this function doesn't exist since cl/201700759
    self.AssertCommandOutputContains(
        'serialport: Connected to {0}.{1}.{2} port 2'.format(
            self.Project(), self.zone, self.instance_name))

    # If any stdout/err, delete it in case future code looks at stdout/err
    self.ClearOutput()
    self.ClearErr()

  def _TestSSHCommandStrictHostKeyChecking(self):
    # Make sure that we can connect to the instance using
    # --strict-host-key-checking=yes on the first connection, since the keys
    # should have been delivered via the guest attributes.
    message = 'Finished running startup scripts.'
    booted = self.WaitForBoot(self.instance_name, message, retries=10,
                              polling_interval=10)
    self.assertTrue(booted, msg='Instance failed to boot before timeout.')
    self.Run('compute ssh --quiet {0} --zone {1} '
             '--strict-host-key-checking=yes --command "expr 12300 + 45"'
             .format(self.instance_name, self.zone))

    self.AssertFileContains('12345', self.stdout_capture_path)

    self.AssertNewErrContains('Writing 3 keys to ')

    # If any stdout/err, delete it in case future code looks at stdout/err
    self.ClearOutput()
    self.ClearErr()


if __name__ == '__main__':
  e2e_test_base.main()
