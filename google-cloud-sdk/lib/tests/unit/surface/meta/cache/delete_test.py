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

"""Tests for the `gcloud meta cache delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import stat

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instances import test_resources
from six.moves import range


def GetOpenFds():
  """Returns the set of mini-stat info for open fds from 0 to 63."""
  fds = set()
  for fd in range(64):
    try:
      st = os.fstat(fd)
    except OSError:
      continue
    mode = st.st_mode
    typ = '?'
    for kind, fun in (('d', stat.S_ISDIR),
                      ('c', stat.S_ISCHR),
                      ('b', stat.S_ISBLK),
                      ('p', stat.S_ISFIFO),
                      ('l', stat.S_ISLNK),
                      ('s', stat.S_ISSOCK),
                      ('-', stat.S_ISREG)):
      if fun(mode):
        typ = kind
        break
    fds.add('{typ}-{fd}-{mode:03o}'.format(typ=typ, fd=fd, mode=mode & 0o777))
  return fds


class DeleteCommandTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self._original_open_fds = GetOpenFds()

  def TearDown(self):
    open_fds = GetOpenFds()
    self.assertEqual(self._original_open_fds, open_fds)

  def Cmd(self, command_line):
    self.Run(command_line)
    open_fds = GetOpenFds()
    # This assertion checks for fd leaks in command_line and its libraries.
    self.assertEqual(self._original_open_fds, open_fds)

  def RunDeleteCache(self, command, response=None, error=None, exception=None):
    self.ClearErr()
    if response:
      self.WriteInput(response)

    if self.IsOnWindows():

      try:
        self.Cmd(command)
      except console_io.OperationCancelledError as e:
        if response != 'n':
          self.fail('Exception [%s] not expected.' % e)
      except OSError as e:  # WindowsError derives from OSError.
        # Windows file in use error. GetOpenFds() ensures it's not an fd leak.
        # That implicates a handle leak. This may become a bigger problem when
        # command completion is enabled on windows.
        if e.winerror == 32:
          return
        raise
      except exception:
        pass
      except BaseException as e:  # pylint: disable=broad-except
        self.fail('Exception [%s] not expected.' % e)

    else:

      try:
        self.Cmd(command)
      except exception:
        pass
      except console_io.OperationCancelledError as e:
        if response != 'n':
          self.fail('Exception [%s] not expected.' % e)
      except BaseException as e:  # pylint: disable=broad-except
        self.fail('Exception [%s] not expected.' % e)

    if error:
      self.AssertErrContains(error)
    elif error is not None:
      self.AssertErrEquals(error)

  def testDeleteCache(self):
    self.Cmd('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:InstancesCompleter '
             '--format=none --zone=zone-1 i')

    self.ClearErr()
    self.WriteInput('n')
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.Cmd('meta cache delete')
    self.AssertErrContains('resource://] cache will be deleted.')

    self.RunDeleteCache(
        command='meta cache delete',
        response='y',
        error='resource://] cache will be deleted.')

    self.RunDeleteCache(
        command='meta cache delete',
        error='resource.cache] not found.',
        exception=cache_util.Error)

  def testDeleteCacheWithSqlToFileSwitch(self):
    os.environ['CLOUDSDK_CACHE_IMPLEMENTATION'] = 'sql'
    self.Cmd('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:InstancesCompleter '
             '--format=none --zone=zone-1 i')

    self.RunDeleteCache(
        command='meta cache delete',
        response='n',
        error='resource://] cache will be deleted.',
        exception=console_io.OperationCancelledError)

    os.environ['CLOUDSDK_CACHE_IMPLEMENTATION'] = 'file'
    self.RunDeleteCache(command='meta cache delete --quiet')
    del os.environ['CLOUDSDK_CACHE_IMPLEMENTATION']

    self.RunDeleteCache(
        command='meta cache delete',
        error='resource.cache] not found.',
        exception=cache_util.Error)

  def testDeleteCacheWithFileToSqlSwitch(self):
    os.environ['CLOUDSDK_CACHE_IMPLEMENTATION'] = 'file'
    self.Cmd('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:InstancesCompleter '
             '--format=none --zone=zone-1 i')

    self.RunDeleteCache(
        command='meta cache delete',
        response='n',
        error='resource://] cache will be deleted.',
        exception=console_io.OperationCancelledError)

    os.environ['CLOUDSDK_CACHE_IMPLEMENTATION'] = 'sql'
    self.RunDeleteCache(command='meta cache delete --quiet')
    del os.environ['CLOUDSDK_CACHE_IMPLEMENTATION']

    self.RunDeleteCache(
        command='meta cache delete',
        error='resource.cache] not found.',
        exception=cache_util.Error)

  def testDeleteTable(self):
    self.Cmd('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:InstancesCompleter '
             '--format=none --zone=zone-1 i')
    self.StartObjectPatch(
        lister, 'GetGlobalResourcesDicts', return_value=[])
    self.Cmd('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:ZonesCompleter '
             '--format=none --verbosity=info i')

    self.ClearOutput()
    self.Cmd('meta cache list')
    self.AssertOutputEquals("""\
+------------------------------+-----+-----+---------+---------+
|             NAME             | COL | KEY | TIMEOUT | EXPIRED |
+------------------------------+-----+-----+---------+---------+
| compute.instances.my-project | 3   | 3   | 3600    | False   |
| compute.zones.my-project     | 2   | 2   | 28800   | False   |
+------------------------------+-----+-----+---------+---------+
""")

    with self.AssertRaisesExceptionMatches(
        cache_util.NoTablesMatched,
        'No tables matched [instances.compute].'):
      self.Cmd('meta cache delete instances.compute')

    self.ClearErr()
    self.WriteInput('y')
    self.Cmd('meta cache delete compute.*')
    self.AssertErrContains(
        'compute.instances.my-project,compute.zones.my-project] '
        'will be deleted.')

    self.ClearOutput()
    self.Cmd('meta cache list')
    self.AssertOutputEquals('')

    self.RunDeleteCache(command='meta cache delete --quiet')


if __name__ == '__main__':
  test_base.main()
