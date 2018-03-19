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

"""Unit tests for the resource cache module."""

import os

from googlecloudsdk.core import config
from googlecloudsdk.core.cache import completion_cache
from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.cache import resource_cache
from tests.lib import test_case
from tests.lib.core import core_completer_test_base
from tests.lib.core.cache import updaters


class MockCompleter(completion_cache.Completer):
  """Completer with mock : separated resource strings."""

  def StringToRow(self, string):
    return string.split(':')

  def RowToString(self, row, parameter_info=None):
    return ':'.join(row)


class ZeroRequiredResourceCompleter(MockCompleter,
                                    updaters.ZeroRequiredCollectionUpdater):
  """Completer with 0 required columns."""


class ColumnOneCompleter(MockCompleter, updaters.ColumnOneUpdater):
  """Value updater for TwoRequiredResourceCompleter."""


class ColumnTwoCompleter(MockCompleter, updaters.ColumnTwoUpdater):
  """Value updater for OneRequiredResourceCompleter."""


class OneRequiredResourceCompleter(MockCompleter,
                                   updaters.OneRequiredCollectionUpdater):
  """Completer with 1 required column."""


class TwoRequiredResourceCompleter(MockCompleter,
                                   updaters.TwoRequiredCollectionUpdater):
  """Completer with 2 required columns."""


class TwoRequiredResourceCumulativeCompleter(
    MockCompleter,
    updaters.TwoRequiredCollectionCumulativeUpdater):
  """Completer with 2 required columns and a cumulative updater."""


class CompletionCacheTest(core_completer_test_base.CoreCompleterBase):

  def Now(self):
    return self.now

  def Tick(self, seconds=2):
    self.now += seconds

  def SetUp(self):
    self.StartPropertyPatch(
        config.Paths,
        'cache_dir',
        return_value=os.path.join(self.temp_path, 'cache'))
    self.StartObjectPatch(persistent_cache_base, 'Now', side_effect=self.Now)
    self.now = updaters.NOW_START_TIME
    self.cache = resource_cache.ResourceCache()
    dest = 'instance'
    self.parsed_args = core_completer_test_base.MockNamespace(args={dest: None})
    self.argument = self.parsed_args.GetPositionalArgument(dest)

  def DeleteCache(self):
    if self.cache:
      self.cache.Delete()
      self.cache = None

  def TearDown(self):
    self.DeleteCache()

  def GetTableList(self):
    tables = []
    for table_name in self.cache.Select():
      table = self.cache.Table(table_name, create=False)
      tables.append((table.name, table.columns, table.keys, table.timeout,
                     table.modified, int(table.restricted)))
    return sorted(tables)

  @test_case.Filters.SkipOnWindows('winerror 32 on TearDown', 'b/24905560')
  def testCacheNoCreateNotFound(self):
    self.DeleteCache()
    with self.assertRaisesRegexp(
        exceptions.CacheNotFound,
        r'Persistent cache \[.*resource.cache\] not found.'):
      self.cache = resource_cache.ResourceCache(create=False)

  def testCacheOneResourceZeroRequired(self):
    completer = ZeroRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa:pdq', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b'],
        completer.Complete('aa:*:xyz-b', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b', 'abc:pdq-c:xyz-b'],
        completer.Complete('*:*:xyz-b', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa:pdq', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b'],
        completer.Complete('aa:*:xyz-b', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b', 'abc:pdq-c:xyz-b'],
        completer.Complete('*:*:xyz-b', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345678, 0)],
                         self.GetTableList())

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    completer = ZeroRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac:pdq', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b'],
        completer.Complete('ac:*:xyz-b', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b', 'acc:pdq-d:xyz-b'],
        completer.Complete('*:*:xyz-b', parameter_info))

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac:pdq', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b'],
        completer.Complete('ac:*:xyz-b', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b', 'acc:pdq-d:xyz-b'],
        completer.Complete('*:*:xyz-b', parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneResourceOneRequired(self):
    completer = OneRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa:pdq', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b'],
        completer.Complete('aa:*:xyz-b', parameter_info))
    self.assertEqual(
        ['aab:pdq-b:xyz-b', 'abc:pdq-c:xyz-b'],
        completer.Complete('*:*:xyz-b', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals([('test.api.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.project', 1, 1, 1, 12345678, 0)],
                         self.GetTableList())

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    completer = OneRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-d:xyz-b', 'ace:pdq-e:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals([('test.api.xyz-a', 3, 3, 1, 12345680, 0),
                          ('test.api.xyz-b', 3, 3, 1, 12345680, 0),
                          ('test.api.xyz-c', 3, 3, 1, 12345680, 0),
                          ('test.project', 1, 1, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneResourceTwoRequired(self):
    completer = TwoRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abc:pdq-a:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abc:pdq-a:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals([('test.api.pdq-a.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-a.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-b.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-b.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.project.pdq-a', 1, 1, 1, 12345678, 0),
                          ('test.project.pdq-b', 1, 1, 1, 12345678, 0),
                          ('test.zone', 1, 1, 1, 12345678, 0)],
                         self.GetTableList())

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    completer = TwoRequiredResourceCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-b:xyz-b', 'ace:pdq-c:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-b:xyz-b', 'ace:pdq-c:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals([('test.api.pdq-a.xyz-a', 3, 3, 1, 0, 0),
                          ('test.api.pdq-a.xyz-b', 3, 3, 1, 0, 0),
                          ('test.api.pdq-b.xyz-a', 3, 3, 1, 12345680, 0),
                          ('test.api.pdq-b.xyz-b', 3, 3, 1, 12345680, 0),
                          ('test.api.pdq-b.xyz-c', 3, 3, 1, 12345680, 0),
                          ('test.api.pdq-c.xyz-a', 3, 3, 1, 12345680, 0),
                          ('test.api.pdq-c.xyz-b', 3, 3, 1, 12345680, 0),
                          ('test.api.pdq-c.xyz-c', 3, 3, 1, 12345680, 0),
                          ('test.project.pdq-a', 1, 1, 1, 0, 0),
                          ('test.project.pdq-b', 1, 1, 1, 12345680, 0),
                          ('test.project.pdq-c', 1, 1, 1, 12345680, 0),
                          ('test.zone', 1, 1, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneResourceTwoRequiredCumulative(self):
    completer = TwoRequiredResourceCumulativeCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abc:pdq-a:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        ['aaa:pdq-a:xyz-a', 'aab:pdq-b:xyz-b'],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abc:pdq-a:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        [],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals(
        [('test.project.zone.instance.aaa.pdq-a', 3, 3, 1, 12345678, 0),
         ('test.project.zone.instance.aab.pdq-b', 3, 3, 1, 12345678, 0),
         ('test.project.zone.instance.abc.pdq-a', 3, 3, 1, 12345678, 0),
         ('test.project', 1, 1, 1, 12345678, 0),
         ('test.project.zone.aaa', 2, 2, 1, 12345678, 0),
         ('test.project.zone.aab', 2, 2, 1, 12345678, 0),
         ('test.project.zone.abc', 2, 2, 1, 12345678, 0)],
        self.GetTableList())

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    completer = TwoRequiredResourceCumulativeCompleter(cache=self.cache)
    parameter_info = completer.ParameterInfo(self.parsed_args, self.argument)

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-b:xyz-b', 'ace:pdq-c:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.assertEqual(
        [],
        completer.Complete('aa', parameter_info))
    self.assertEqual(
        ['abb:pdq-b:xyz-a', 'abc:pdq-c:xyz-b'],
        completer.Complete('ab', parameter_info))
    self.assertEqual(
        ['acc:pdq-b:xyz-b', 'ace:pdq-c:xyz-c'],
        completer.Complete('ac', parameter_info))

    self.AssertSetEquals(
        [('test.project.zone.instance.aaa.pdq-a', 3, 3, 1, 0, 0),
         ('test.project.zone.instance.aab.pdq-b', 3, 3, 1, 0, 0),
         ('test.project.zone.instance.abc.pdq-a', 3, 3, 1, 0, 0),
         ('test.project.zone.instance.abb.pdq-b', 3, 3, 1, 12345680, 0),
         ('test.project.zone.instance.abc.pdq-c', 3, 3, 1, 12345680, 0),
         ('test.project.zone.instance.acc.pdq-b', 3, 3, 1, 12345680, 0),
         ('test.project.zone.instance.ace.pdq-c', 3, 3, 1, 12345680, 0),
         ('test.project', 1, 1, 1, 12345680, 0),
         ('test.project.zone.aaa', 2, 2, 1, 0, 0),
         ('test.project.zone.aab', 2, 2, 1, 0, 0),
         ('test.project.zone.abc', 2, 2, 1, 12345680, 0),
         ('test.project.zone.abb', 2, 2, 1, 12345680, 0),
         ('test.project.zone.acc', 2, 2, 1, 12345680, 0),
         ('test.project.zone.ace', 2, 2, 1, 12345680, 0)],
        self.GetTableList())

  @test_case.Filters.SkipOnWindows('winerror 32 on TearDown', 'b/24905560')
  def testCacheCompleterRowToTemplate(self):
    completer = ZeroRequiredResourceCompleter(cache=self.cache)

    self.assertEqual(
        ['*', '*', '*'],
        completer.RowToTemplate([]))
    self.assertEqual(
        ['a*', '*', '*'],
        completer.RowToTemplate(['a']))
    self.assertEqual(
        ['a*', '*b', '*'],
        completer.RowToTemplate(['a', '*b']))
    self.assertEqual(
        ['a*', '*b', 'c*c'],
        completer.RowToTemplate(['a', '*b', 'c*c']))
    self.assertEqual(
        ['a*', '*b', 'c*c', 'd*'],
        completer.RowToTemplate(['a', '*b', 'c*c', 'd']))


if __name__ == '__main__':
  core_completer_test_base.main()
