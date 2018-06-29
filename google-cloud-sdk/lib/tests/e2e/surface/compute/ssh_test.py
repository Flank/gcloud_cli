# Copyright 2016 Google Inc. All Rights Reserved.
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
from __future__ import unicode_literals
import os

from tests.lib import command_capture
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class SSHTest(e2e_instances_test_base.InstancesTestBase,
              command_capture.WithCommandCapture):

  def testSSH(self):
    self._TestInstanceCreation()
    self._TestUpdateMetadata()
    self._TestSSHCommand()
    self._TestSSHKeyManagement()
    # TODO(b/33475433): The serial port host doesn't seem to be reachable
    # self._TestConnectToSerialPort()

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

    self.AssertCommandOutputContains(self.instance_name)

    # The key for the instance should be added to the known hosts file after
    # the first run, so we should be able to explicitly pass
    # --strict-host-key-checking=yes here and have the command succeed. (On
    # Windows, --strict-host-key-checking=yes is a noop.)
    self.Run('compute ssh --quiet {0} --zone {1} '
             '--strict-host-key-checking=yes --command "echo qwerty" '
             .format(self.instance_name, self.zone))

    self.AssertCommandOutputContains('qwerty')

    # Update output seek values
    self.GetNewOutput()
    self.GetNewErr()

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

    self.AssertCommandOutputContains(
        'serialport: Connected to {0}.{1}.{2} port 2'.format(
            self.Project(), self.zone, self.instance_name))

    # Update output seek values
    self.GetNewOutput()
    self.GetNewErr()


if __name__ == '__main__':
  e2e_test_base.main()
