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
"""Tests for the machine-types list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DatastoreTest(test_base.BaseTest):

  def testIpv6Port(self):
    host, port = self._RunHostPortTest('[::1]:12345')

    self.assertEqual('::1', host)
    self.assertEqual('12345', port)

  def testNoPort(self):
    host, port = self._RunHostPortTest('10.10.10.10')
    self.assertEqual('10.10.10.10', host)
    self.assertEqual('8081', port)

  def testNoHost(self):
    host, port = self._RunHostPortTest(':1234')
    self.assertEqual('localhost', host)
    self.assertEqual('1234', port)

  def _RunHostPortTest(self, hostport):
    """Runs a test with the provided --host-port.

    Args:
      hostport: The value to send to --host-port.
    Returns:
      a tuple of host, port that was used.
    """
    self.StartObjectPatch(java, 'RequireJavaInstalled')
    self.StartObjectPatch(util, 'EnsureComponentIsInstalled')

    ret = {}
    def SideEffect(arg):
      ret['host'] = arg.host_port.host
      ret['port'] = arg.host_port.port

    prepare_mock = self.StartObjectPatch(datastore_util, 'PrepareGCDDataDir')
    prepare_mock.side_effect = SideEffect
    self.StartObjectPatch(datastore_util, 'StartGCDEmulator')
    self.StartObjectPatch(datastore_util, 'WriteGCDEnvYaml')
    self.StartObjectPatch(util, 'PrefixOutput')

    self.Run('beta emulators datastore start --host-port=%s' % hostport)

    return ret['host'], ret['port']


if __name__ == '__main__':
  test_case.main()
