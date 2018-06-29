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

"""Unit tests for the calliope/display module."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import copy
import datetime
import inspect
import logging
import operator

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import display
from googlecloudsdk.calliope import display_info
from googlecloudsdk.calliope import display_taps
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import calliope_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

from six.moves import range  # pylint: disable=redefined-builtin


_MOCK_RESOURCE = [
    {
        'kind': 'service#entity',
        'status': 'DONE',
        'selfLink': 'http://foo.bar',
    },
    {
        'kind': 'compute#instance',
        'status': 'ERROR',
        'selfLink': 'http://bar.foo',
    },
]


_MOCK_CORRUPT_RESOURCE = [
    {
        'kind': 'compute#instance',
        'status': 'DONE',
        'selfLink': 'http://foo.bar',
    },
    {
        'status': 'ERROR',
    },
]

_MOCK_PRINT_RESOURCE = [
    {
        'name': 'resource#1',
        'status': 101,
        'devices': [
            {
                'cpus': [
                    {
                        'name': 'cpu#1#1',
                        'speed': 1,
                    },
                    {
                        'name': 'cpu#1#2',
                        'speed': 10,
                    },
                    {
                        'name': 'cpu#1#3',
                        'speed': 100,
                    },
                ],
                'disks': [
                    {
                        'name': 'disk#1#1',
                        'size': 1,
                    },
                    {
                        'name': 'disk#1#2',
                        'size': 10,
                    },
                    {
                        'name': 'disk#1#3',
                        'size': 100,
                    },
                ],
                'networks': [
                    {
                        'name': 'nic#1#1',
                        'ip': '10.20.1.1',
                    },
                    {
                        'name': 'nic#1#2',
                        'ip': '10.20.1.2',
                    },
                    {
                        'name': 'nic#1#3',
                        'ip': '10.20.1.3',
                    },
                ],
            },
        ],
    },
    {
        'name': 'resource#2',
        'status': 101,
        'devices': [
            {
                'cpus': [
                    {
                        'name': 'cpu#2#1',
                        'speed': 1,
                    },
                    {
                        'name': 'cpu#2#2',
                        'speed': 10,
                    },
                    {
                        'name': 'cpu#2#3',
                        'speed': 100,
                    },
                ],
                'disks': [
                    {
                        'name': 'disk#2#1',
                        'size': 1,
                    },
                    {
                        'name': 'disk#2#2',
                        'size': 10,
                    },
                    {
                        'name': 'disk#2#3',
                        'size': 100,
                    },
                ],
                'networks': [
                    {
                        'name': 'nic#2#1',
                        'ip': '10.20.2.1',
                    },
                    {
                        'name': 'nic#2#2',
                        'ip': '10.20.2.2',
                    },
                    {
                        'name': 'nic#2#3',
                        'ip': '10.20.2.3',
                    },
                ],
            },
        ],
    },
    {
        'name': 'resource#3',
        'status': 101,
        'devices': [
            {
                'cpus': [
                    {
                        'name': 'cpu#3#1',
                        'speed': 1,
                    },
                    {
                        'name': 'cpu#3#2',
                        'speed': 10,
                    },
                    {
                        'name': 'cpu#3#3',
                        'speed': 100,
                    },
                ],
                'disks': [
                    {
                        'name': 'disk#3#1',
                        'size': 1,
                    },
                    {
                        'name': 'disk#3#2',
                        'size': 10,
                    },
                    {
                        'name': 'disk#3#3',
                        'size': 100,
                    },
                ],
                'networks': [
                    {
                        'name': 'nic#3#1',
                        'ip': '10.20.3.1',
                    },
                    {
                        'name': 'nic#3#2',
                        'ip': '10.20.3.2',
                    },
                    {
                        'name': 'nic#3#3',
                        'ip': '10.20.3.3',
                    },
                ],
            },
        ],
    },
]


def _ResourceGenerator(n):
  for i in range(n):
    print('Yield(%d)' % i)
    yield {'index': i}


class MockResourceInfo(object):
  """Mock collection => resource information mapping support."""

  def __init__(self, async_collection=None, bypass_cache=False,
               cache_command=None, list_format=None, simple_format=None,
               defaults=None, transforms=None):
    self.collection = None  # memoized by Get().
    self.async_collection = async_collection
    self.bypass_cache = bypass_cache
    self.cache_command = cache_command
    self.list_format = list_format
    self.simple_format = simple_format
    self.defaults = defaults
    self.transforms = transforms  # memoized by GetTransforms().

  def GetTransforms(self):
    return None


class _MockParser(object):
  """Mock ArgParse parser, just enough for calliope/display."""

  def __init__(self):
    self.display_info = display_info.DisplayInfo()

  # pylint: disable=invalid-name, Must match signature.
  def add_argument(self, *args, **kwargs):
    pass


class _MockArgs(object):
  """Mock ArgParse args info, just enough for calliope/display."""

  # pylint: disable=redefined-builtin, args.filter and args.format required.
  def __init__(self, command=None, is_async=None, filter=None, flatten=None,
               format=None, limit=None, page_size=None, simple_format=None,
               sort_by=None, uri=None):
    self._command = command
    self.async = is_async
    self.filter = filter
    self.flatten = flatten if flatten is None else flatten.split(',')
    self.format = format
    self.limit = limit
    self.page_size = page_size
    self.simple_format = simple_format
    self.sort_by = sort_by
    self.uri = uri
    self._parser = _MockParser()

  def IsSpecified(self, dest):
    return getattr(self, dest, None) is not None

  def GetDisplayInfo(self):
    return self._parser.display_info

  def _GetCommand(self):
    return self._command


class _MockCommand(base.Command):
  """Mock ListCommand."""

  def __init__(self):
    pass

  def Run(self, unused_args):
    return None

  def GetPath(self):
    return ['test']


def _MockCommandArgs(command_class, **kwargs):
  command = command_class()
  args = _MockArgs(command=command, **kwargs)
  for cls in reversed(inspect.getmro(command_class)):
    if hasattr(cls, '_Flags'):
      cls._Flags(args._parser)
    if hasattr(cls, 'Args'):
      cls.Args(args._parser)
  return command, args


class _MockCommandWithDisplay(_MockCommand):
  """Mock Command with Display() method."""

  def Display(self, unused_args, resource):
    self.display_resource = list(resource)
    print('Display().')


class _MockCreateCommand(base.CreateCommand):
  """Mock CreateCommand."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def Run(self, unused_args):
    return None


class _MockDeleteCommand(base.DeleteCommand):
  """Mock DeleteCommand."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def Run(self, unused_args):
    return None


class _MockDescribeCommand(base.DescribeCommand):
  """Mock DescribeCommand."""

  def __init__(self):
    pass

  def Run(self, unused_args):
    return None


class _MockSilentCommand(base.SilentCommand):
  """Mock SilentCommand."""

  def __init__(self):
    pass

  def Run(self, unused_args):
    return None


class _MockListCommand(base.ListCommand):
  """Mock ListCommand."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(good,async)')
    parser.display_info.AddFilter('-status:OBSOLETE')
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def Run(self, unused_args):
    return None


class _MockListCommandWithEpilog(_MockListCommand):
  """Mock ListCommand with Epilog()."""

  def Epilog(self, resources_were_displayed=True):
    print('Epilog({0}).'.format(resources_were_displayed))


class _MockBypassListCommand(_MockListCommand):
  """Mock ListCommand with no cache updater."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddCacheUpdater(None)


class _MockRestoreCommand(base.RestoreCommand):
  """Mock RestoreCommand."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def Run(self, unused_args):
    return None


class _MockUpdateCommand(base.UpdateCommand):
  """Mock UpdateCommand."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')

  def Run(self, unused_args):
    return None


class _MockBypassCreateCommand(base.CreateCommand):
  """Mock CreateCommand with no cache updater."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, unused_args):
    return None


class _MockBypassDeleteCommand(base.DeleteCommand):
  """Mock DeleteCommand with no cache updater."""

  def __init__(self):
    pass

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('none')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, unused_args):
    return None


class DisplayTest(sdk_test_base.WithOutputCapture):

  cached_uris = ['http://foo.bar', 'http://bar.foo']

  def MockIsUserOutputEnabled(self):
    return self.user_output_enabled

  def MockPrint(self, printer, resource, out=None, defaults=None,
                single=None):
    if 'disable' in printer.attributes:
      self.print_resource = resource
      printer._empty = False
    else:
      self.print_resource = list(resource)
      printer._empty = not self.print_resource
      fmt = [printer.column_attributes.Name()]
      if printer.attributes:
        fmt.append('[{0}]'.format(','.join(printer.attributes)))
      columns = printer.column_attributes.Columns()
      if columns:
        fmt.append('({0})'.format(','.join([resource_lex.GetKeyName(col.key)
                                            for col in columns])))
      print('Print({0}).'.format(''.join(fmt)))

  def MockUpdateCache(self, obj):
    if obj._uris:
      self.uri_update_cache_op = obj._update_cache_op.__class__.__name__
      self.uris = obj._uris

  def DisableUserOutput(self):
    self.user_output_enabled = False

  def SetUp(self):
    log.SetVerbosity(logging.INFO)
    self.display_resource = None
    self.print_resource = None
    self.uris = None
    self.uri_update_cache_op = None
    self.user_output_enabled = True
    self.StartObjectPatch(display_taps.UriCacher,
                          'Done',
                          autospec=True).side_effect = self.MockUpdateCache
    self.StartObjectPatch(resource_printer_base.ResourcePrinter,
                          'Print', autospec=True).side_effect = self.MockPrint
    self.StartObjectPatch(
        log, 'IsUserOutputEnabled').side_effect = self.MockIsUserOutputEnabled
    self.mock_resource = copy.copy(_MOCK_RESOURCE)
    self.mock_corrupt_resource = copy.copy(_MOCK_CORRUPT_RESOURCE)

  def testDisplayNoUserOutput(self):
    self.DisableUserOutput()
    command, args = _MockCommandArgs(_MockCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('')
    self.AssertErrEquals('INFO: Display disabled.\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDisplayWithDisplay(self):
    command, args = _MockCommandArgs(_MockCommandWithDisplay)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Display().\n')
    self.AssertErrEquals('INFO: Explicit Display.\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDisplayWithDisplayJson(self):
    command, args = _MockCommandArgs(_MockCommandWithDisplay, format='json')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(json).\n')
    self.AssertErrEquals('INFO: Display format: "json"\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDescribeCommandDisplay(self):
    command, args = _MockCommandArgs(_MockDescribeCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(default).\n')
    self.AssertErrEquals('INFO: Display format: "default"\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testCreateCommandDisplay(self):
    command, args = _MockCommandArgs(_MockCreateCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.AssertErrEquals('INFO: Display format: "none"\n')
    self.assertEqual(self.uri_update_cache_op, 'AddToCacheOp')
    self.assertEqual(self.uris, self.cached_uris)

  def testCreateCommandDisplayCorruptResource(self):
    command, args = _MockCommandArgs(_MockCreateCommand)
    display.Displayer(command, args, self.mock_corrupt_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testCreateCommandDisplayCorruptFilterFlag(self):
    command, args = _MockCommandArgs(_MockCreateCommand, filter='status:DONE')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testCreateCommandDisplayCorruptLimitFlag(self):
    command, args = _MockCommandArgs(_MockCreateCommand, limit=1)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDeleteCommandDisplay(self):
    command, args = _MockCommandArgs(_MockDeleteCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.AssertErrEquals('INFO: Display format: "none"\n')
    self.assertEqual(self.uri_update_cache_op, 'DeleteFromCacheOp')
    self.assertEqual(self.uris, self.cached_uris)

  def testDeleteCommandDisplayCorruptResource(self):
    command, args = _MockCommandArgs(_MockDeleteCommand)
    display.Displayer(command, args, self.mock_corrupt_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDeleteCommandDisplayCorruptFilterFlag(self):
    command, args = _MockCommandArgs(_MockDeleteCommand, filter='status:DONE')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testDeleteCommandDisplayCorruptLimitFlag(self):
    command, args = _MockCommandArgs(_MockDeleteCommand, limit=1)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testListCommandDisplay(self):
    command, args = _MockCommandArgs(_MockListCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.AssertErrEquals("""\
INFO: Display filter: "-status:OBSOLETE"
INFO: Display format: "table(good,async)"
""")
    self.assertEqual(self.uri_update_cache_op, 'ReplaceCacheOp')
    self.assertEqual(self.uris, self.cached_uris)

  def testListCommandDisplayCorruptResource(self):
    command, args = _MockCommandArgs(_MockListCommand)
    display.Displayer(command, args, self.mock_corrupt_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testListCommandDisplayCorruptFilterFlag(self):
    command, args = _MockCommandArgs(_MockListCommand, filter='status:DONE')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testListCommandDisplayCorruptLimitFlag(self):
    command, args = _MockCommandArgs(_MockListCommand, limit=1)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testListCommandDisplayFilterFlagOne(self):
    command, args = _MockCommandArgs(_MockListCommand, filter='status:ERROR')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)
    self.assertEqual(len(self.print_resource), 1)
    self.assertEqual(sorted(self.print_resource[0]),
                     sorted(_MOCK_RESOURCE[1]))

  def testListCommandDisplayLimitFlagOne(self):
    command, args = _MockCommandArgs(_MockListCommand, limit=1)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)
    self.assertEqual(len(self.print_resource), 1)
    self.assertEqual(sorted(self.print_resource[0]),
                     sorted(_MOCK_RESOURCE[0]))

  def testListCommandDisplayLimitFlagOneWithResourceGenerator(self):
    command, args = _MockCommandArgs(_MockListCommand, limit=1)
    display.Displayer(command, args, _ResourceGenerator(8)).Display()
    self.AssertOutputEquals("""\
Yield(0)
Yield(1)
Print(table(good,async)).
""")
    self.assertEqual(self.uri_update_cache_op, None)
    self.assertEqual(len(self.print_resource), 1)

  def testListCommandDisplayLimitFlagAll(self):
    command, args = _MockCommandArgs(_MockListCommand, limit=2)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, None)
    self.assertEqual(len(self.print_resource), 2)
    self.assertEqual(sorted(self.print_resource[0]),
                     sorted(_MOCK_RESOURCE[0]))
    self.assertEqual(sorted(self.print_resource[1]),
                     sorted(_MOCK_RESOURCE[1]))

  def testListCommandDisplayLimitFlagAllWithGenerator(self):
    command, args = _MockCommandArgs(_MockListCommand, limit=8)
    display.Displayer(command, args, _ResourceGenerator(8)).Display()
    self.AssertOutputEquals("""\
Yield(0)
Yield(1)
Yield(2)
Yield(3)
Yield(4)
Yield(5)
Yield(6)
Yield(7)
Print(table(good,async)).
""")
    self.assertEqual(self.uri_update_cache_op, None)
    self.assertEqual(len(self.print_resource), 8)

  def testListCommandDisplayPageSizeFlagOne(self):
    command, args = _MockCommandArgs(_MockListCommand, page_size=1)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, 'ReplaceCacheOp')
    self.assertEqual(len(self.print_resource), 3)
    self.assertEqual(sorted(self.print_resource[0]),
                     sorted(_MOCK_RESOURCE[0]))
    self.assertTrue(isinstance(self.print_resource[1],
                               resource_printer_base.PageMarker))
    self.assertEqual(sorted(self.print_resource[2]),
                     sorted(_MOCK_RESOURCE[1]))

  def testListCommandDisplayPageSizeFlagAll(self):
    command, args = _MockCommandArgs(_MockListCommand, page_size=2)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(good,async)).\n')
    self.assertEqual(self.uri_update_cache_op, 'ReplaceCacheOp')
    self.assertEqual(len(self.print_resource), 2)
    self.assertEqual(sorted(self.print_resource[0]),
                     sorted(_MOCK_RESOURCE[0]))
    self.assertEqual(sorted(self.print_resource[1]),
                     sorted(_MOCK_RESOURCE[1]))

  def testListCommandDisplayGoodAsyncDefaultFormatNoResources(self):
    command, args = _MockCommandArgs(_MockListCommandWithEpilog)
    resource = display.Displayer(command, args, _ResourceGenerator(0)).Display()
    # Resource should be consumed.
    self.assertFalse(list(resource))
    # Epilog() should be called.
    self.AssertOutputEquals("""\
Print(table(good,async)).
Epilog(False).
""")

  def testListCommandDisplayGoodAsyncDefaultFormatJsonFormatNoResources(self):
    command, args = _MockCommandArgs(_MockListCommandWithEpilog, format='json')
    resource = display.Displayer(command, args, _ResourceGenerator(0)).Display()
    # Resource should be consumed.
    self.assertFalse(list(resource))
    # Epilog() should not be called.
    self.AssertOutputEquals("""\
Print(json).
""")

  def testRestoreCommandDisplay(self):
    command, args = _MockCommandArgs(_MockRestoreCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.AssertErrEquals('INFO: Display format: "none"\n')
    self.assertEqual(self.uri_update_cache_op, 'AddToCacheOp')
    self.assertEqual(self.uris, self.cached_uris)

  def testUpdateCommandDisplay(self):
    command, args = _MockCommandArgs(_MockUpdateCommand)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(none).\n')
    self.AssertErrEquals('INFO: Display format: "none"\n')
    self.assertEqual(self.uri_update_cache_op, None)

  def testCreateCommandWithBypassCache(self):
    command, args = _MockCommandArgs(_MockBypassCreateCommand)
    resource = display.Displayer(command, args, _ResourceGenerator(3)).Display()
    # Resource should be consumed.
    self.assertFalse(list(resource))
    self.assertEqual(self.uri_update_cache_op, None)
    self.AssertOutputEquals("""\
Yield(0)
Yield(1)
Yield(2)
Print(none).
""")

  def testDeleteCommandWithBypassCache(self):
    command, args = _MockCommandArgs(_MockBypassDeleteCommand)
    resource = display.Displayer(command, args, _ResourceGenerator(3)).Display()
    # Resource should be consumed.
    self.assertFalse(list(resource))
    self.assertEqual(self.uri_update_cache_op, None)
    self.AssertOutputEquals("""\
Yield(0)
Yield(1)
Yield(2)
Print(none).
""")

  def testDisplayConditionalFormat(self):
    command, args = _MockCommandArgs(
        _MockCommand, format='table(kind, status.if(limit AND page))')
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(kind)).\n')

  def testDisplayConditionalFormatLimitPage(self):
    command, args = _MockCommandArgs(
        _MockCommand, format='table(kind, status.if(limit AND page_size))',
        limit=1, page_size=99)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(kind,status)).\n')

  def testDisplayConditionalFormatSimpleFormat(self):
    command, args = _MockCommandArgs(
        _MockCommand, format='table(kind.if(NOT simple_format), status)',
        simple_format=True)
    display.Displayer(command, args, self.mock_resource).Display()
    self.AssertOutputEquals('Print(table(status)).\n')


class DisplayPrintTest(calliope_test_base.CalliopeTestBase,
                       test_case.WithOutputCapture):

  def SetUp(self):
    self._command, _ = _MockCommandArgs(_MockListCommand)
    self._resource = resource_projector.MakeSerializable(_MOCK_PRINT_RESOURCE)

  def testDisplayPrint(self):
    args = _MockArgs(format='csv(name,status)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
name,status
resource#1,101
resource#2,101
resource#3,101
""")

  def testDisplayPrintFilter(self):
    args = _MockArgs(format='csv(name,status)', filter='name:*#2')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
name,status
resource#2,101
""")

  def testDisplayPrintLimitTwo(self):
    args = _MockArgs(format='csv(name,status)', limit=2)
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
name,status
resource#1,101
resource#2,101
""")

  def testDisplayPrintSortByIndex(self):
    args = _MockArgs(
        format='table(name,status,devices[0].disks[0].name:label=DISK)',
        sort_by=['~devices[0].disks[0].name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        STATUS  DISK
resource#3  101     disk#3#1
resource#2  101     disk#2#1
resource#1  101     disk#1#1
""")

  def testDisplayPrintSortBySlice(self):
    args = _MockArgs(
        format='table(name,status,devices[0].disks[0].name:label=DISK)',
        sort_by=['~devices[].disks[].name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        STATUS  DISK
resource#3  101     disk#3#1
resource#2  101     disk#2#1
resource#1  101     disk#1#1
""")

  def testDisplayPrintFlatten(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='table(name:sort=1,'
                     'devices.disks.name:sort=2,'
                     'devices.disks.size:sort=3)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        DISKS_NAME  SIZE
resource#1  disk#1#1    1
resource#1  disk#1#2    10
resource#1  disk#1#3    100
resource#2  disk#2#1    1
resource#2  disk#2#2    10
resource#2  disk#2#3    100
resource#3  disk#3#1    1
resource#3  disk#3#2    10
resource#3  disk#3#3    100
""")

  def testDisplayNoPrintFlattenScalar(self):
    args = _MockArgs(flatten='devices[].disks[].name[]', format='disable')
    results = display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals('')
    self.assertEqual([
        'disk#1#1',
        'disk#1#2',
        'disk#1#3',
        'disk#2#1',
        'disk#2#2',
        'disk#2#3',
        'disk#3#1',
        'disk#3#2',
        'disk#3#3',
    ], list(results))

  def testDisplayPrintFlattenFilter(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     filter='devices.disks.size>=10',
                     format='table(name:sort=1,'
                     'devices.disks.name:sort=2,'
                     'devices.disks.size:sort=3)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        DISKS_NAME  SIZE
resource#1  disk#1#2    10
resource#1  disk#1#3    100
resource#2  disk#2#2    10
resource#2  disk#2#3    100
resource#3  disk#3#2    10
resource#3  disk#3#3    100
""")

  def testDisplayPrintFlatten2(self):
    args = _MockArgs(flatten='devices[].cpus[]',
                     format='table(name:sort=1,'
                     'devices.cpus.name:sort=2)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        CPUS_NAME
resource#1  cpu#1#1
resource#1  cpu#1#2
resource#1  cpu#1#3
resource#2  cpu#2#1
resource#2  cpu#2#2
resource#2  cpu#2#3
resource#3  cpu#3#1
resource#3  cpu#3#2
resource#3  cpu#3#3
""")

  def testDisplayPrintFlattenDisjoint(self):
    args = _MockArgs(flatten='devices[].cpus[],devices.disks[]',
                     format='table(name:sort=1,'
                     'devices.cpus.name:sort=2,'
                     'devices.disks.name:sort=3,'
                     'devices.disks.size:sort=4)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        CPUS_NAME  DISKS_NAME  SIZE
resource#1  cpu#1#1    disk#1#1    1
resource#1  cpu#1#1    disk#1#2    10
resource#1  cpu#1#1    disk#1#3    100
resource#1  cpu#1#2    disk#1#1    1
resource#1  cpu#1#2    disk#1#2    10
resource#1  cpu#1#2    disk#1#3    100
resource#1  cpu#1#3    disk#1#1    1
resource#1  cpu#1#3    disk#1#2    10
resource#1  cpu#1#3    disk#1#3    100
resource#2  cpu#2#1    disk#2#1    1
resource#2  cpu#2#1    disk#2#2    10
resource#2  cpu#2#1    disk#2#3    100
resource#2  cpu#2#2    disk#2#1    1
resource#2  cpu#2#2    disk#2#2    10
resource#2  cpu#2#2    disk#2#3    100
resource#2  cpu#2#3    disk#2#1    1
resource#2  cpu#2#3    disk#2#2    10
resource#2  cpu#2#3    disk#2#3    100
resource#3  cpu#3#1    disk#3#1    1
resource#3  cpu#3#1    disk#3#2    10
resource#3  cpu#3#1    disk#3#3    100
resource#3  cpu#3#2    disk#3#1    1
resource#3  cpu#3#2    disk#3#2    10
resource#3  cpu#3#2    disk#3#3    100
resource#3  cpu#3#3    disk#3#1    1
resource#3  cpu#3#3    disk#3#2    10
resource#3  cpu#3#3    disk#3#3    100
""")

  def testDisplayPrintFlattenDisjoint2(self):
    args = _MockArgs(flatten='devices[].cpus[],devices.disks[]',
                     format='table(name:sort=1,'
                     'devices.cpus.name:sort=2,'
                     'devices.disks.name:sort=3)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        CPUS_NAME  DISKS_NAME
resource#1  cpu#1#1    disk#1#1
resource#1  cpu#1#1    disk#1#2
resource#1  cpu#1#1    disk#1#3
resource#1  cpu#1#2    disk#1#1
resource#1  cpu#1#2    disk#1#2
resource#1  cpu#1#2    disk#1#3
resource#1  cpu#1#3    disk#1#1
resource#1  cpu#1#3    disk#1#2
resource#1  cpu#1#3    disk#1#3
resource#2  cpu#2#1    disk#2#1
resource#2  cpu#2#1    disk#2#2
resource#2  cpu#2#1    disk#2#3
resource#2  cpu#2#2    disk#2#1
resource#2  cpu#2#2    disk#2#2
resource#2  cpu#2#2    disk#2#3
resource#2  cpu#2#3    disk#2#1
resource#2  cpu#2#3    disk#2#2
resource#2  cpu#2#3    disk#2#3
resource#3  cpu#3#1    disk#3#1
resource#3  cpu#3#1    disk#3#2
resource#3  cpu#3#1    disk#3#3
resource#3  cpu#3#2    disk#3#1
resource#3  cpu#3#2    disk#3#2
resource#3  cpu#3#2    disk#3#3
resource#3  cpu#3#3    disk#3#1
resource#3  cpu#3#3    disk#3#2
resource#3  cpu#3#3    disk#3#3
""")

  def testDisplayPrintFlattenDisjointLeftToRight(self):
    args = _MockArgs(flatten='devices[],devices.cpus[],devices.disks[]',
                     format='table(name:sort=1,'
                     'devices.cpus.name:sort=2,'
                     'devices.disks.name:sort=3,'
                     'devices.disks.size:sort=4)')
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        CPUS_NAME  DISKS_NAME  SIZE
resource#1  cpu#1#1    disk#1#1    1
resource#1  cpu#1#1    disk#1#2    10
resource#1  cpu#1#1    disk#1#3    100
resource#1  cpu#1#2    disk#1#1    1
resource#1  cpu#1#2    disk#1#2    10
resource#1  cpu#1#2    disk#1#3    100
resource#1  cpu#1#3    disk#1#1    1
resource#1  cpu#1#3    disk#1#2    10
resource#1  cpu#1#3    disk#1#3    100
resource#2  cpu#2#1    disk#2#1    1
resource#2  cpu#2#1    disk#2#2    10
resource#2  cpu#2#1    disk#2#3    100
resource#2  cpu#2#2    disk#2#1    1
resource#2  cpu#2#2    disk#2#2    10
resource#2  cpu#2#2    disk#2#3    100
resource#2  cpu#2#3    disk#2#1    1
resource#2  cpu#2#3    disk#2#2    10
resource#2  cpu#2#3    disk#2#3    100
resource#3  cpu#3#1    disk#3#1    1
resource#3  cpu#3#1    disk#3#2    10
resource#3  cpu#3#1    disk#3#3    100
resource#3  cpu#3#2    disk#3#1    1
resource#3  cpu#3#2    disk#3#2    10
resource#3  cpu#3#2    disk#3#3    100
resource#3  cpu#3#3    disk#3#1    1
resource#3  cpu#3#3    disk#3#2    10
resource#3  cpu#3#3    disk#3#3    100
""")

  def testDisplayPrintFlattenSortBy(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='table(name:sort=1,'
                     'devices.disks.name:sort=2,'
                     'devices.disks.size:sort=3)',
                     sort_by=['~devices.disks.size'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME        DISKS_NAME  SIZE
resource#1  disk#1#3    100
resource#1  disk#1#3    100
resource#1  disk#1#3    100
resource#2  disk#2#3    100
resource#2  disk#2#3    100
resource#2  disk#2#3    100
resource#3  disk#3#3    100
resource#3  disk#3#3    100
resource#3  disk#3#3    100
""")

  def testDisplayPrintFlattenSortByAscendingLimitFormatValue(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='value(devices.disks.name)',
                     limit=4,
                     sort_by=['devices.disks.name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
disk#1#3
disk#1#3
disk#1#3
disk#2#3
""")

  def testDisplayPrintFlattenSortByDescendingLimitFormatValue(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='value(devices.disks.name)',
                     limit=4,
                     sort_by=['~devices.disks.name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
disk#3#3
disk#3#3
disk#3#3
disk#2#3
""")

  def testDisplayPrintFlattenSortByAscendingLimitFormatTable(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='table(devices.disks.name)',
                     limit=4,
                     sort_by=['devices.disks.name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME
disk#1#3
disk#1#3
disk#1#3
disk#2#3
""")

  def testDisplayPrintFlattenSortByDescendingLimitFormatTable(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='table(devices.disks.name)',
                     limit=4,
                     sort_by=['~devices.disks.name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME
disk#3#3
disk#3#3
disk#3#3
disk#2#3
""")

  def testDisplaySortByDateWithNoneValues(self):
    args = _MockArgs(format='table(datetime.date("%Y-%m-%dT%H:%M:%S"))',
                     sort_by=['datetime'])
    resource = [
        {'datetime': datetime.datetime(year=2014, month=1, day=6, hour=9)},
        {'datetime': None},
        {'datetime': datetime.datetime(year=2017, month=8, day=11, hour=11)},
    ]
    display.Displayer(self._command, args, resource).Display()
    self.AssertOutputEquals("""\
DATETIME

2014-01-06T09:00:00
2017-08-11T11:00:00
""")

  def testDisplaySortByStringWithNoneValues(self):
    args = _MockArgs(format='table(value)',
                     sort_by=['~value'])
    resource = [
        {'value': 'abc'},
        {'value': None},
        {'value': 'xyz'},
        {'value': None},
    ]
    display.Displayer(self._command, args, resource).Display()
    self.AssertOutputEquals("""\
VALUE
xyz
abc


""")

  def testDisplayPrintFlattenSortFilterLimitFormatTable(self):
    args = _MockArgs(flatten='devices[].disks[]',
                     format='table(devices.disks.name)',
                     limit=4,
                     filter='-NAME:disk#3*',
                     sort_by=['~devices.disks.name'])
    display.Displayer(self._command, args, self._resource).Display()
    self.AssertOutputEquals("""\
NAME
disk#2#3
disk#2#3
disk#2#3
disk#1#3
""")


class DisplayFormatSortByCombinationsTest(calliope_test_base.CalliopeTestBase):

  def testDisplayPrintSortByCombinations(self):
    command, _ = _MockCommandArgs(_MockListCommand)

    # Generate the raw resource with all combinations of 3 fields with 3 values.
    resource = []
    for a in range(3):
      for b in range(3):
        for c in range(3):
          resource.append({'a': a, 'b': b, 'c': c})

    # Generate and run the tests of all reverse combinations for the 3 fields.
    for a_reverse in (False, True):
      a_key = '~a' if a_reverse else 'a'
      for b_reverse in (False, True):
        b_key = '~b' if b_reverse else 'b'
        for c_reverse in (False, True):
          c_key = '~c' if c_reverse else 'c'

          # Generate the expected value by a sequence of individual sorts.
          # The code under test sorts by groups with same reverse value.
          expected = sorted(
              resource, key=operator.itemgetter('c'), reverse=c_reverse)
          expected = sorted(
              expected, key=operator.itemgetter('b'), reverse=b_reverse)
          expected = sorted(
              expected, key=operator.itemgetter('a'), reverse=a_reverse)

          sort_by = [a_key, b_key, c_key]
          args = _MockArgs(format='none[disable]', sort_by=sort_by)
          actual = display.Displayer(command, args, resource).Display()
          self.assertEqual(expected, actual,
                           '--sort-by={} mismatch'.format(','.join(sort_by)))


class DisplayFormatTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self._command = _MockListCommand()
    self._resource = []

  def testDisplayPrintSortByIndex(self):
    args = _MockArgs(format='csv(name,status)',
                     sort_by=['~devices[0].disks[0].name'])
    expected = ('csv(name,status):(devices[0].disks[0].name:sort=1:reverse)')
    actual = display.Displayer(self._command, args).GetFormat()
    self.assertEqual(expected, actual)

  def testDisplayPrintSortBySlice(self):
    args = _MockArgs(format='csv(name,status)',
                     sort_by=['~devices[].disks[].name'])
    expected = ('csv(name,status):(devices[0].disks[0].name:sort=1:reverse)')
    actual = display.Displayer(self._command, args).GetFormat()
    self.assertEqual(expected, actual)


class CliDisplayTest(calliope_test_base.CalliopeTestBase,
                     test_case.WithOutputCapture):

  def MockUpdateCache(self, obj):
    if obj._uris is not None:
      self.uri_update_cache_op = obj._update_cache_op.__class__.__name__
      self.uris = obj._uris

  def SetUp(self):
    self.StartObjectPatch(display_taps.UriCacher,
                          'Done',
                          autospec=True).side_effect = self.MockUpdateCache
    self.cli = self.LoadTestCli('sdk6')
    self.uri_update_cache_op = None
    self.uris = None

  def testCliDisplayGoodAsyncOff(self):
    self.cli.Execute(['sdk', 'collection-good-async'])

  def testCliDisplayGoodAsyncDebug(self):
    self.cli.Execute(['sdk',
                      'collection-good-async',
                      '--format='
                      '''table[debug](
                           a:sort=4,
                           b.x:sort=3:reverse,
                           c.y.z:sort=2,
                           d:sort=1:reverse
                         )
                      ''',
                     ])
    self.AssertErrEquals("""\
table format projection:
   a : (2, 4, 'A', left, None, False, None)
   b : (1, UNORDERED, None, left, None, None, None)
     x : (2, 3, 'X', left, None, False, None, [reverse])
   c : (1, UNORDERED, None, left, None, None, None)
     y : (1, UNORDERED, None, left, None, None, None)
       z : (2, 2, 'Z', left, None, False, None)
   d : (2, 1, 'D', left, None, False, None, [reverse])
""")

  def testCliDisplayGoodAsyncDebugImplicitSortBy(self):
    self.cli.Execute(['sdk',
                      'collection-good-async',
                      '--format='
                      '''table[debug](
                           a:sort=4,
                           b:sort=3:reverse,
                           c:sort=2,
                           d:sort=1:reverse
                         )
                         :(
                           b:sort=1,
                           c:sort=2:reverse
                         )
                      ''',
                     ])
    self.AssertErrEquals("""\
table format projection:
   a : (2, 6, 'A', left, None, False, None)
   b : (2, 1, 'B', left, None, False, None, [reverse])
   c : (2, 2, 'C', left, None, False, None, [reverse])
   d : (2, 3, 'D', left, None, False, None, [reverse])
""")

  def testCliDisplayGoodAsyncDebugTwoImplicitSortBy(self):
    self.cli.Execute(['sdk',
                      'collection-good-async',
                      '--format='
                      '''table[debug](
                           a:sort=4,
                           b:sort=3:reverse,
                           c:sort=2,
                           d:sort=1:reverse
                         )
                         :(
                           b:sort=1,
                           c:sort=2:reverse
                         )
                         :(
                           a:sort=1,
                           d:sort=2
                         )
                      ''',
                     ])
    self.AssertErrEquals("""\
table format projection:
   a : (2, 1, 'A', left, None, False, None)
   b : (2, 3, 'B', left, None, False, None, [reverse])
   c : (2, 4, 'C', left, None, False, None, [reverse])
   d : (2, 2, 'D', left, None, False, None, [reverse])
""")

  def testCliDisplayGoodAsyncDebugImplicitAndExplicitSortBy(self):
    self.cli.Execute(['sdk',
                      'collection-good-async',
                      '--format='
                      '''table[debug](
                           a:sort=4,
                           b:sort=3:reverse,
                           c:sort=2,
                           d:sort=1:reverse
                         )
                         :(
                           b:sort=1,
                           c:sort=2:reverse
                         )
                      ''',
                      '--sort-by=a,d',
                     ])
    self.AssertErrEquals("""\
table format projection:
   a : (2, 1, 'A', left, None, False, None)
   b : (2, 3, 'B', left, None, False, None, [reverse])
   c : (2, 4, 'C', left, None, False, None, [reverse])
   d : (2, 2, 'D', left, None, False, None, [reverse])
""")

  def testCliDisplayGetUriUriFlagOffOutputDisabled(self):
    expected = ['abc/def', 'xyz']
    actual = self.cli.Execute(['sdk', 'geturi', '--format=[disable]'])
    self.assertEqual(expected, list(actual))
    self.assertEqual('ReplaceCacheOp', self.uri_update_cache_op)
    expected_uris = ['URI({0})'.format(x) for x in expected]
    self.assertEqual(expected_uris, self.uris)

  def testCliDisplayGetUriUriFlagOffAsyncOff(self):
    self.cli.Execute(['sdk', 'geturi'])
    self.AssertOutputContains('GOOD ASYNC', normalize_space=True)

  def testCliDisplayGetUriUriFlagOffAsyncOn(self):
    self.cli.Execute(['sdk', 'geturi', '--async'])
    self.AssertOutputContains('GOOD OPERATIONS', normalize_space=True)

  def testCliDisplayGetUriUriFlagOffAsyncOnFOrmatSpecified(self):
    self.cli.Execute(['sdk', 'geturi', '--async',
                      '--format=table(good,specified)'])
    self.AssertOutputContains('GOOD SPECIFIED', normalize_space=True)

  def testCliDisplayGetUriUriFlagOnOutputDisabled(self):
    expected = ['URI(abc/def)', 'URI(xyz)']
    actual = self.cli.Execute(
        ['sdk', 'geturi', '--format=[disable]', '--uri'])
    self.assertEqual(expected, list(actual))
    self.assertEqual('ReplaceCacheOp', self.uri_update_cache_op)
    self.assertEqual(expected, self.uris)

  def testCliDisplayGetUriUriFlagOn(self):
    expected = """\
URI(abc/def)
URI(xyz)
"""
    self.cli.Execute(['sdk', 'geturi', '--uri'])
    self.AssertOutputEquals(expected)
    self.assertEqual('ReplaceCacheOp', self.uri_update_cache_op)

  def testCliGetReferencedKeyNamesNone(self):
    expected = []
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
    ]))
    self.assertEqual(expected, actual)

  def testCliGetReferencedKeyNamesFilter(self):
    expected = ['ABC', 'pdq']
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
        '--filter=ABC:xyz OR pdq<123]',
    ]))
    self.assertEqual(expected, actual)

  def testCliGetReferencedKeyNamesFormat(self):
    expected = ['abc.xyz', 'pdq']
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
        '--format=table(abc.xyz:label=ABC, pdq)',
    ]))
    self.AssertOutputEquals('')
    self.assertEqual(expected, actual)

  def testCliGetReferencedKeyNamesFilterFormatDisable(self):
    expected = ['abc.xyz', 'pdq']
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
        '--filter=ABC:xyz OR pdq<123]',
        '--format=table(abc.xyz:label=ABC, pdq) disable',
    ]))
    self.AssertOutputEquals('')
    self.assertEqual(expected, actual)

  def testCliGetReferencedKeyNamesFilterFormat(self):
    expected = []
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
        '--filter=ABC:xyz OR pdq<123]',
        '--format=table(abc.xyz:label=ABC, pdq) list',
    ]))
    self.AssertOutputEquals(' - abc.xyz\n - pdq\n')
    self.assertEqual(expected, actual)

  def testCliGetReferencedKeyNamesRepeatedFilterFormatDisable(self):
    expected = ['abc.xyz', 'pdq']
    actual = list(self.cli.Execute([
        'sdk',
        'referenced-key-names',
        '--filter=ABC:xyz OR pdq[2]<123]',
        '--format=table(abc[].xyz:label=ABC, pdq) disable',
    ]))
    self.AssertOutputEquals('')
    self.assertEqual(expected, actual)

  def testCliUnserializedResourceFilter(self):
    """_unserializable should not be serialized."""
    expected = []
    actual = [(type(x).__name__, x.serializable) for x in self.cli.Execute([
        'sdk',
        'trial-serialization',
        '--filter=_unserializable>=4',
    ])]
    self.assertEqual(expected, actual)

  def testCliSerializedResourceFilter(self):
    """serializable should be serialized."""
    expected = [('Resource', i) for i in range(4, 9)]
    actual = [(type(x).__name__, x.serializable) for x in self.cli.Execute([
        'sdk',
        'trial-serialization',
        '--filter=serializable>=4',
    ])]
    self.assertEqual(expected, actual)

  def testCliEnumWithDefaults(self):
    self.cli.Execute(['sdk', 'enum'])
    expected = """\
A B
1 RUNNING
0 STOPPED
? ?
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByA(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=A'])
    expected = """\
A B
0 STOPPED
1 RUNNING
? ?
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByInvA(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=~A'])
    expected = """\
A B
? ?
1 RUNNING
0 STOPPED
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByAB(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=A,B'])
    expected = """\
A B
0 STOPPED
1 RUNNING
? ?
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByB(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=B'])
    expected = """\
A B
? ?
1 RUNNING
0 STOPPED
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByInvB(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=~B'])
    expected = """\
A B
0 STOPPED
1 RUNNING
? ?
"""
    self.AssertOutputEquals(expected, normalize_space=True)

  def testCliEnumSortByXInvB(self):
    self.cli.Execute(['sdk', 'enum', '--sort-by=X,~B'])
    expected = """\
A B
0 STOPPED
1 RUNNING
? ?
"""
    self.AssertOutputEquals(expected, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
