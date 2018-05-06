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

"""Tests for googlecloudsdk.command_lib.util.ssh.containers."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.ssh import containers
from tests.lib import test_case


RUN_CONTAINER_COMMAND = ['sudo', 'docker', 'exec']


class ContainerTest(test_case.TestCase):
  """Test `remote_command` and `tty` parameters for SSHCommand."""

  def testNoContainerNoCommand(self):
    """Base case of no container and no command."""
    container = None
    command = None
    self.assertIsNone(containers.GetRemoteCommand(container, command), None)
    self.assertIsNone(containers.GetTty(container, command), None)

  def testWithContainerNoCommand(self):
    """With container but no command given."""
    container = 'my-container'
    command = None
    self.assertEqual(containers.GetRemoteCommand(container, command),
                     RUN_CONTAINER_COMMAND +
                     ['-it', 'my-container', '/bin/sh'])
    self.assertTrue(containers.GetTty(container, command), True)

  def testNoContainerWithCommand(self):
    """With command but no container given."""
    container = None
    command = ['echo', 'hello']
    self.assertEqual(containers.GetRemoteCommand(container, command),
                     ['echo', 'hello'])
    self.assertIsNone(containers.GetTty(container, command), None)

  def testWithContainerAndCommand(self):
    """With command and container given."""
    container = 'my-container'
    command = ['echo', 'hello']
    self.assertEqual(containers.GetRemoteCommand(container, command),
                     RUN_CONTAINER_COMMAND +
                     ['-i', 'my-container', 'echo', 'hello'])
    self.assertIsNone(containers.GetTty(container, command), None)


if __name__ == '__main__':
  test_case.main()
