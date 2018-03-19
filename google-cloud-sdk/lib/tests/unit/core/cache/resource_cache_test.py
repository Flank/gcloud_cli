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
from googlecloudsdk.core import properties
from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.cache import resource_cache
from googlecloudsdk.core.util import encoding
from tests.lib import sdk_test_base
from tests.lib.core.cache import updaters


class ResourceCacheTest(sdk_test_base.SdkBase):

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

  def TearDown(self):
    self.cache.Delete()

  def GetTableList(self):
    tables = []
    for table_name in self.cache.Select():
      table = self.cache.Table(table_name, create=False)
      tables.append((table.name, table.columns, table.keys, table.timeout,
                     table.modified, int(table.restricted)))
    return sorted(tables)

  def AssertSetEquals(self, seq1, seq2):
    self.assertEqual(set(seq1), set(seq2))

  def testCacheGetDefaultNameWithAccount(self):
    account = 'BoZo@Big.Top'
    self.StartObjectPatch(
        properties.VALUES.core.account, 'Get', return_value=account)
    cache_name = resource_cache.ResourceCache.GetDefaultName()
    self.assertTrue(
        os.path.sep + account + os.path.sep in cache_name)

  def testCacheDefaultNameWithAccount(self):
    account = 'BoZo@Big.Top'
    self.StartObjectPatch(
        properties.VALUES.core.account, 'Get', return_value=account)
    self.cache.Delete()
    self.cache = resource_cache.ResourceCache()
    self.assertTrue(
        os.path.sep + account + os.path.sep in self.cache.name)

  def testCacheOneCollectionZeroRequired(self):
    collection = updaters.ZeroRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345678, 0)],
                         self.GetTableList())

    self.assertEqual('test.api', collection.GetTableForRow(
        ('abb', 'pdq-b', 'xyz-a'), parameter_info).name)
    self.assertEqual('test.api', collection.GetTableForRow(
        ('abc', 'pdq-c', 'xyz-b'), parameter_info).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.ZeroRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneCollectionZeroRequiredShortTemplate(self):
    collection = updaters.ZeroRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*',), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*',), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*',), parameter_info))

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*',), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*',), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*',), parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345678, 0)],
                         self.GetTableList())

    self.assertEqual('test.api', collection.GetTableForRow(
        ('abb', 'pdq-b', 'xyz-a'), parameter_info).name)
    self.assertEqual('test.api', collection.GetTableForRow(
        ('abc', 'pdq-c', 'xyz-b'), parameter_info).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.ZeroRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [],
        collection.Select(('aa*',), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*',), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*',), parameter_info))

    self.assertEqual(
        [],
        collection.Select(('aa*',), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*',), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*',), parameter_info))

    self.AssertSetEquals([('test.api', 3, 3, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneCollectionOneRequired(self):
    collection = updaters.OneRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-c', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals([('test.api.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.project', 1, 1, 1, 12345678, 0)],
                         self.GetTableList())

    self.assertEqual('test.api.xyz-a', collection.GetTableForRow(
        ('aaa', 'pdq-a', 'xyz-a'), parameter_info, create=False).name)
    self.assertEqual('test.api.xyz-b', collection.GetTableForRow(
        ('aab', 'pdq-b', 'xyz-b'), parameter_info, create=False).name)
    with self.assertRaisesRegexp(
        exceptions.CacheTableNotFound,
        r'resource.cache] cache table \[test.api.xyz-c] not found'):
      collection.GetTableForRow(
          ('ace', 'pdq-e', 'xyz-c'), parameter_info, create=False)
    self.assertEqual('test.api.xyz-c', collection.GetTableForRow(
        ('ace', 'pdq-e', 'xyz-c'), parameter_info).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.OneRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-d', 'xyz-b'), ('ace', 'pdq-e', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals([('test.api.xyz-a', 3, 3, 1, 12345680, 0),
                          ('test.api.xyz-b', 3, 3, 1, 12345680, 0),
                          ('test.api.xyz-c', 3, 3, 1, 12345680, 0),
                          ('test.project', 1, 1, 1, 12345680, 0)],
                         self.GetTableList())

  def testCacheOneCollectionTwoRequired(self):
    collection = updaters.TwoRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-a', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-a', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals([('test.api.pdq-a.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-a.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-b.xyz-a', 3, 3, 1, 12345678, 0),
                          ('test.api.pdq-b.xyz-b', 3, 3, 1, 12345678, 0),
                          ('test.project.pdq-a', 1, 1, 1, 12345678, 0),
                          ('test.project.pdq-b', 1, 1, 1, 12345678, 0),
                          ('test.zone', 1, 1, 1, 12345678, 0)],
                         self.GetTableList())

    self.assertEqual('test.api.pdq-a.xyz-a', collection.GetTableForRow(
        ('aaa', 'pdq-a', 'xyz-a'), parameter_info, create=False).name)
    self.assertEqual('test.api.pdq-a.xyz-b', collection.GetTableForRow(
        ('aaa', 'pdq-a', 'xyz-b'), parameter_info, create=False).name)
    self.assertEqual('test.api.pdq-b.xyz-a', collection.GetTableForRow(
        ('aab', 'pdq-b', 'xyz-a'), parameter_info, create=False).name)
    self.assertEqual('test.api.pdq-b.xyz-b', collection.GetTableForRow(
        ('aab', 'pdq-b', 'xyz-b'), parameter_info, create=False).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.TwoRequiredCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-b', 'xyz-b'), ('ace', 'pdq-c', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-b', 'xyz-b'), ('ace', 'pdq-c', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

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

  def testCacheOneCollectionTwoRequiredCumulative(self):
    collection = updaters.TwoRequiredCollectionCumulativeUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-a', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [('aaa', 'pdq-a', 'xyz-a'), ('aab', 'pdq-b', 'xyz-b')],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abc', 'pdq-a', 'xyz-b')],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [],
        collection.Select(('ac*', None, None), parameter_info))

    self.AssertSetEquals(
        [('test.project.zone.instance.aaa.pdq-a', 3, 3, 1, 12345678, 0),
         ('test.project.zone.instance.aab.pdq-b', 3, 3, 1, 12345678, 0),
         ('test.project.zone.instance.abc.pdq-a', 3, 3, 1, 12345678, 0),
         ('test.project', 1, 1, 1, 12345678, 0),
         ('test.project.zone.aaa', 2, 2, 1, 12345678, 0),
         ('test.project.zone.aab', 2, 2, 1, 12345678, 0),
         ('test.project.zone.abc', 2, 2, 1, 12345678, 0)],
        self.GetTableList())

    self.assertEqual(
        'test.project.zone.instance.aaa.pdq-a',
        collection.GetTableForRow(
            ('aaa', 'pdq-a', 'xyz-a'), parameter_info, create=False).name)
    self.assertEqual(
        'test.project.zone.instance.aaa.pdq-a',
        collection.GetTableForRow(
            ('aaa', 'pdq-a', 'xyz-b'), parameter_info, create=False).name)
    self.assertEqual(
        'test.project.zone.instance.aab.pdq-b',
        collection.GetTableForRow(
            ('aab', 'pdq-b', 'xyz-a'), parameter_info, create=False).name)
    self.assertEqual(
        'test.project.zone.instance.aab.pdq-b',
        collection.GetTableForRow(
            ('aab', 'pdq-b', 'xyz-b'), parameter_info, create=False).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.TwoRequiredCollectionCumulativeUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-b', 'xyz-b'), ('ace', 'pdq-c', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

    self.assertEqual(
        [],
        collection.Select(('aa*', None, None), parameter_info))
    self.assertEqual(
        [('abb', 'pdq-b', 'xyz-a'), ('abc', 'pdq-c', 'xyz-b'),],
        collection.Select(('ab*', None, None), parameter_info))
    self.assertEqual(
        [('acc', 'pdq-b', 'xyz-b'), ('ace', 'pdq-c', 'xyz-c')],
        collection.Select(('ac*', None, None), parameter_info))

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

  def testCacheNoCollection(self):
    collection = updaters.NoCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('thing-1',), ('thing-2',)],
        collection.Select(('*',), parameter_info))

    self.AssertSetEquals(
        [('tests.lib.core.cache.updaters:NoCollectionUpdater',
          1, 1, 1, 12345678, 0)],
        self.GetTableList())

    self.assertEqual(
        'tests.lib.core.cache.updaters:NoCollectionUpdater',
        collection.GetTableForRow(('thing-1',), parameter_info).name)

    self.Tick()
    self.cache.Close()
    self.cache = resource_cache.ResourceCache()
    collection = updaters.NoCollectionUpdater(self.cache)
    parameter_info = collection.ParameterInfo()

    self.assertEqual(
        [('thing-0',), ('thing-1',), ('thing-n',)],
        collection.Select(('*',), parameter_info))

    self.AssertSetEquals(
        [('tests.lib.core.cache.updaters:NoCollectionUpdater',
          1, 1, 1, 12345680, 0)], self.GetTableList())


class ResourceCacheDeleteTest(sdk_test_base.SdkBase):
  """resource_cache.Delete() must work across cache implementation changes."""

  def SetUp(self):
    self.StartPropertyPatch(
        config.Paths,
        'cache_dir',
        return_value=os.path.join(self.temp_path, 'cache'))
    self.StartEnvPatch({})

  def _CreateAndDeleteCacheAcrossImplementations(
      self, create_implementation=None, delete_implementation=None):

    if create_implementation:
      encoding.SetEncodedValue(
          os.environ, 'CLOUDSDK_CACHE_IMPLEMENTATION', create_implementation)

    cache = resource_cache.ResourceCache()
    collection = updaters.NoCollectionUpdater(cache)
    parameter_info = collection.ParameterInfo()
    collection.Select(('*',), parameter_info)
    cache.Close()

    if delete_implementation:
      encoding.SetEncodedValue(
          os.environ, 'CLOUDSDK_CACHE_IMPLEMENTATION', delete_implementation)
    resource_cache.Delete()

    with self.assertRaisesRegexp(
        exceptions.CacheNotFound,
        r'resource.cache] not found'):
      resource_cache.Delete()

  def testDelete(self):
    self._CreateAndDeleteCacheAcrossImplementations()

  def testDeleteWithFileToFile(self):
    self._CreateAndDeleteCacheAcrossImplementations(
        create_implementation='file', delete_implementation='file')

  def testDeleteWithFileToSql(self):
    self._CreateAndDeleteCacheAcrossImplementations(
        create_implementation='file', delete_implementation='sql')

  def testDeleteWithSqlToFile(self):
    self._CreateAndDeleteCacheAcrossImplementations(
        create_implementation='sql', delete_implementation='file')

  def testDeleteWithSqlToSql(self):
    self._CreateAndDeleteCacheAcrossImplementations(
        create_implementation='sql', delete_implementation='sql')


if __name__ == '__main__':
  sdk_test_base.main()
