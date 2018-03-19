# -*- coding: utf-8 -*-
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

"""Unit tests for the core persistent cache implementation module."""

import os

from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import file_cache
from googlecloudsdk.core.cache import persistent_cache_base
from tests.lib import cli_test_base
from tests.lib import subtests

try:
  # pylint: disable=g-import-not-at-top, Drop this when sqlite3 is bundled.
  from googlecloudsdk.core.cache import sqlite_cache
except ImportError:
  sqlite_cache = None


_TEST_TABLE_NAME_1 = 'test.table.1'
_TEST_TABLE_NAME_2 = 'test.table.2'


class CacheBase(cli_test_base.CliTestBase):

  CACHE_MODULE = file_cache

  def SetUp(self):
    self.cache_name = os.path.join(self.temp_path, 'test.db')
    self.cache = self.CACHE_MODULE.Cache(self.cache_name)

  def TearDown(self):
    self.cache.Delete()

  def GetTableInfo(self):
    info = []
    for table_name in self.cache.Select():
      table = self.cache.Table(table_name, create=False)
      info.append((table.name, table.columns, table.keys, table.timeout,
                   table.modified, table.restricted))
    return sorted(info)

  def AssertRowsEqual(self, seq1, seq2):
    self.assertEqual(set(seq1), set(seq2))


class CacheTests(CacheBase):
  """Cache tests with no table content manipulation."""

  def testCacheInvalidFilesystemArtifact(self):
    self.cache.Commit()
    if not os.path.exists(self.cache_name):
      # There are no filesystem artifacts for this cache implementation.
      # Skip the rest of the test.
      return
    self.cache.Delete()

    open(self.cache_name, 'w').close()
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheInvalid,
        'test.db] is not a persistent cache.'):
      self.CACHE_MODULE.Cache(self.cache_name, create=False)
    os.remove(self.cache_name)

    os.mkdir(self.cache_name)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheInvalid,
        'test.db] is not a persistent cache.'):
      self.CACHE_MODULE.Cache(self.cache_name, create=False)
    os.rmdir(self.cache_name)

  def testCacheTableNotFound(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableNotFound,
        'test.db] cache table [not.found] not found.'):
      self.cache.Table('not.found', create=False)

  def testCacheTableNames(self):
    self.cache.Table('valid')
    self.cache.Table('__alsovalid__')
    self.cache.Table('also/valid/too')

  def testCacheCloseNoCommitNoTable(self):
    """A new cache closed without commit should disappear on close."""
    self.cache.Close(commit=False)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheNotFound,
        'test.db] not found.'):
      self.cache = self.CACHE_MODULE.Cache(self.cache_name, create=False)

  def testCacheDelete(self):
    """Make sure a deleted cache leaves no file droppings."""
    self.cache.Delete()
    self.assertFalse(os.path.exists(self.cache_name))

  def testCacheCloseNoTable(self):
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    self.assertEqual([], self.GetTableInfo())

  def testCacheCloseVersionNoTable(self):
    self.cache.Delete()

    with self.AssertRaisesExceptionMatches(
        exceptions.CacheNotFound,
        'test.db] not found.'):
      self.cache = self.CACHE_MODULE.Cache(self.cache_name, create=False)

    self.cache = self.CACHE_MODULE.Cache(self.cache_name, version='1.0')
    self.cache.Close()

    with self.AssertRaisesExceptionMatches(
        exceptions.CacheVersionMismatch,
        'test.db] cache version [1.0] does not match [2.5].'):
      self.CACHE_MODULE.Cache(self.cache_name, version='2.5')

  def testCacheCreateInvalidTable(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableColumnsInvalid,
        'test.db] table [{}] column count [0] must be >= 1.'.format(
            _TEST_TABLE_NAME_1)):
      self.cache.Table(_TEST_TABLE_NAME_1, columns=0, keys=3)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableKeysInvalid,
        'test.db] table [{}] primary key count [0] must be '
        '>= 1 and <= 1.'.format(_TEST_TABLE_NAME_1)):
      self.cache.Table(_TEST_TABLE_NAME_1, columns=1, keys=0)

  def testCacheCloseNoCommitOneTable(self):
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.cache.Close(commit=False)

    with self.AssertRaisesExceptionMatches(
        exceptions.CacheNotFound,
        'test.db] not found.'):
      self.cache = self.CACHE_MODULE.Cache(self.cache_name, create=False)

  def testCacheCloseOneTable(self):
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.assertEqual([(_TEST_TABLE_NAME_1, 1, 1, 0, 0, 0)], self.GetTableInfo())

  def testCacheTableImplementationRestrictedOpen(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRestricted,
        'test.db] cache table [__metadata__] is restricted.'):
      self.cache.Table('__metadata__')
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRestricted,
        'test.db] cache table [__lock__] is restricted.'):
      self.cache.Table('__lock__')

  def testCacheTableImplementationRestrictedCreateBadColumnsKeys(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRestricted,
        'test.db] cache table [__metadata__] is restricted.'):
      self.cache.Table('__metadata__', columns=1, keys=1)

  def testCacheTableCallerRestrictedCreateThenOpen(self):
    self.cache.Table('__resource__', restricted=True,
                     columns=1, keys=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRestricted,
        'test.db] cache table [__resource__] is restricted.'):
      self.cache.Table('__resource__')

  def testTableExpiredAtCreation(self):
    self.cache.Table(_TEST_TABLE_NAME_1)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table.Select()


class CacheTableTests(CacheBase):
  """Cache tests with table content manipulation."""

  def testTableCreateOpenColumnsMismatch(self):
    self.cache.Table(_TEST_TABLE_NAME_1, columns=3, keys=2, timeout=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableColumnsInvalid,
        'test.db] cache table [test.table.1] columns [9] does not '
        'match existing 3.'):
      self.cache.Table(_TEST_TABLE_NAME_1, columns=9, keys=2)

  def testTableCreateOpenKeysMismatch(self):
    self.cache.Table(_TEST_TABLE_NAME_1, columns=3, keys=2, timeout=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableKeysInvalid,
        'test.db] cache table [test.table.1] keys [1] does not '
        'match existing 2.'):
      self.cache.Table(_TEST_TABLE_NAME_1, columns=3, keys=1)

  def testTableAddRowsExpire(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=3, keys=2, timeout=1)
    table.AddRows((('abc', 'b', 1),
                   ('def', 'e', 2),
                   ('ghi', 'h', 3)))
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table.Select(('a*',))
    table.Validate(timeout=-1)  # Expires on next open.
    self.assertEqual([('abc', 'b', 1)], table.Select(('a*',)))
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table.Select(('a*',))
    table.Validate()
    self.assertEqual([('abc', 'b', 1)], table.Select(('a*',)))

  def testTableAddRowsNoExpire(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows((('abc', 'b', 1),
                   ('def', 'e', 2),
                   ('ghi', 'h', 3)))
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table.Select(('a*',))
    table.Validate()
    self.assertEqual([('abc', 'b', 1)], table.Select(('a*',)))
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    self.assertEqual([('abc', 'b', 1)], table.Select(('a*',)))
    table.Invalidate()
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table.Select(('a*',))
    table.Validate()
    self.assertEqual([('abc', 'b', 1)], table.Select(('a*',)))

  def testTableDeleteAllRows(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows((('abc', 'b', 1),
                   ('def', 'e', 2),
                   ('ghi', 'h', 3)))
    table.Validate()
    table.DeleteRows()
    self.assertEqual([], table.Select(('a*',)))

  def testTableDelete(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows((('abc', 'b', 1),
                   ('def', 'e', 2),
                   ('ghi', 'h', 3)))
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    table.Delete()
    self.assertEqual([], self.cache.Select())

    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableNotFound,
        'test.db] cache table [{}] not found.'.format(_TEST_TABLE_NAME_1)):
      self.cache.Table(_TEST_TABLE_NAME_1, create=False)
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    self.assertEqual([], self.cache.Select())
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableNotFound,
        'test.db] cache table [{}] not found.'.format(_TEST_TABLE_NAME_1)):
      self.cache.Table(_TEST_TABLE_NAME_1, create=False)

  def testTableDeleteRowsMultipleTemplates(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=2, keys=1, timeout=0)
    table.AddRows((('abc', 1),
                   ('def', 2),
                   ('ghi', 3)))
    table.DeleteRows([['pdq'], ['xyz']])
    table.Validate()
    self.assertEqual([('abc', 1),
                      ('def', 2),
                      ('ghi', 3)],
                     sorted(table.Select()))

  def testTableDeleteCreate(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows((('abc', 'b', 1),
                   ('def', 'e', 2),
                   ('ghi', 'h', 3)))
    table.Delete()
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=2, keys=1, timeout=60*60)
    table.AddRows([('abc', 'xyz')])
    table.Validate()
    self.assertEqual([('abc', 'xyz')], table.Select(('a*',)))

  def testTableDeleteNoCommit(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=3, keys=2)
    table.Delete()
    self.cache.Close()

  def testTableKeysWithCloseNoCommit(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows([('abc', 'a', 1)])
    table.AddRows([('abc', 'a', 2)])
    table.AddRows([('abc', 'b', 2)])
    table.AddRows([('abc', 'b', 3)])
    table.Validate()
    self.AssertRowsEqual([('abc', 'a', 2), ('abc', 'b', 3)],
                         table.Select(('a*',)))

    table.DeleteRows([(None, 'a', None)])
    self.assertEqual([('abc', 'b', 3)], table.Select(('a*',)))

    self.cache.Close(commit=False)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheNotFound,
        'test.db] not found.'):
      self.cache = self.CACHE_MODULE.Cache(self.cache_name, create=False)

  def testTableKeysWithDoubleCommit(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows([('abc', 'a', 1)])
    table.AddRows([('abc', 'a', 2)])
    table.AddRows([('abc', 'b', 2)])
    table.AddRows([('abc', 'b', 3)])
    table.Validate()
    self.cache.Commit()
    self.cache.Commit()
    self.AssertRowsEqual([('abc', 'a', 2), ('abc', 'b', 3)],
                         table.Select(('a*',)))

  def testTableKeysWithCommitAndClose(self):
    table = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table.AddRows([('abc', 'a', 1)])
    table.AddRows([('abc', 'a', 2)])
    table.AddRows([('abc', 'b', 2)])
    table.AddRows([('abc', 'b', 3)])
    table.Validate()
    self.cache.Commit()
    self.AssertRowsEqual([('abc', 'a', 2), ('abc', 'b', 3)],
                         table.Select(('a*',)))

    table.DeleteRows([(None, 'a', None)])
    self.assertEqual([('abc', 'b', 3)], table.Select(('a*',)))

    self.cache.Close()
    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table = self.cache.Table(_TEST_TABLE_NAME_1)
    self.assertEqual([('abc', 'b', 3)], table.Select(('a*',)))

  def testTableMultipleTablesInvalidate(self):
    table_1 = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table_1.AddRows([('abc', 'a', 1)])
    table_1.Validate()
    table_2 = self.cache.Table(
        _TEST_TABLE_NAME_2, columns=2, keys=2, timeout=60*60)
    table_2.AddRows([('abc', 1)])
    table_2.Validate()
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    self.cache.Table(_TEST_TABLE_NAME_1)
    self.cache.Invalidate()
    self.cache.Close()

    self.cache = self.CACHE_MODULE.Cache(self.cache_name)
    table_1 = self.cache.Table(_TEST_TABLE_NAME_1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table_1.Select()
    table_2 = self.cache.Table(_TEST_TABLE_NAME_2)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_2)):
      table_2.Select()
    self.assertEqual([(_TEST_TABLE_NAME_1, 3, 2, 3600, 0, 0),
                      (_TEST_TABLE_NAME_2, 2, 2, 3600, 0, 0)],
                     self.GetTableInfo())

  def testTableMultipleTablesMultipleOps(self):
    table_1 = self.cache.Table(
        _TEST_TABLE_NAME_1, columns=3, keys=2, timeout=60*60)
    table_1.AddRows([('abc', 'a', 1)])
    table_1.AddRows([('abc', 'a', 2)])
    table_1.AddRows([('abc', 'b', 2)])
    table_1.AddRows([('abc', 'b', 3)])
    table_1.Validate()

    table_2 = self.cache.Table(
        _TEST_TABLE_NAME_2, columns=2, keys=2, timeout=60*60)
    table_2.AddRows([('abc', 1)])
    table_2.AddRows([('abc', 2)])
    table_2.AddRows([('abc', 3)])
    table_2.Validate()

    self.cache.Commit()
    self.AssertRowsEqual([('abc', 'a', 2), ('abc', 'b', 3)],
                         table_1.Select(('a*',)))

    table_1.DeleteRows([(None, 'a', None)])
    self.assertEqual([('abc', 'b', 3)], table_1.Select(('a*',)))
    self.AssertRowsEqual([('abc', 1), ('abc', 2), ('abc', 3)],
                         table_2.Select(('a*',)))

    table_2.DeleteRows([(None, 2)])
    self.AssertRowsEqual([('abc', 1), ('abc', 3)],
                         table_2.Select(('a*',)))

    self.cache.Close()
    self.cache = self.CACHE_MODULE.Cache(self.cache_name)

    table_1 = self.cache.Table(_TEST_TABLE_NAME_1)
    self.assertEqual([('abc', 'b', 3)], table_1.Select(('a*',)))

    table_2 = self.cache.Table(_TEST_TABLE_NAME_2)
    self.AssertRowsEqual([('abc', 1), ('abc', 3)],
                         table_2.Select(('a*',)))
    self.AssertRowsEqual([_TEST_TABLE_NAME_1, _TEST_TABLE_NAME_2],
                         self.cache.Select())

    self.cache.Invalidate()
    self.AssertRowsEqual([_TEST_TABLE_NAME_1, _TEST_TABLE_NAME_2],
                         self.cache.Select())

    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_1)):
      table_1.Select()
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableExpired,
        'test.db] cache table [{}] has expired.'.format(_TEST_TABLE_NAME_2)):
      table_2.Select()

  def testTableOneColumnAddRowsInvalidRowSize(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=1, keys=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [2] is invalid. Must be 1.'):
      table.AddRows([('abc', 'a')])
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [0] is invalid. Must be 1.'):
      table.AddRows([[]])

  def testTableOneColumnDeleteRowsInvalidRowSize(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=1, keys=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [2] is invalid. Must be 1.'):
      table.DeleteRows([('abc', 'a')])
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [0] is invalid. Must be 1.'):
      table.DeleteRows([[]])

  def testTableTwoColumnsDeleteRowsInvalidRowSize(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=2, keys=1)
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [3] is invalid. '
        'Must be >= 1 and <= 2.'):
      table.DeleteRows([('abc', 'a', 1)])
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [0] is invalid. '
        'Must be >= 1 and <= 2.'):
      table.DeleteRows([[]])

  def testTableOneColumnSelectInvalidRowSize(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=1, keys=1)
    table.Validate()
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [2] is invalid. Must be 1.'):
      table.Select(('abc', 'a'))
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [0] is invalid. Must be 1.'):
      table.Select([])

  def testTableTwoColumnsSelectInvalidRowSize(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=2, keys=1)
    table.Validate()
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [3] is invalid. '
        'Must be >= 1 and <= 2.'):
      table.Select(('abc', 'a', 1))
    with self.AssertRaisesExceptionMatches(
        exceptions.CacheTableRowSizeInvalid,
        'Cache table [test.table.1] row size [0] is invalid. '
        'Must be >= 1 and <= 2.'):
      table.Select([])

  def testTableUnicodeColumnValues(self):
    table = self.cache.Table(_TEST_TABLE_NAME_1, columns=2, keys=1)
    table.AddRows((
        (u'Ṁöë', u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"),
        (u'Larry', u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."),
        (u'Shemp', u'Hey, Ṁöë! Hey, Larry!'),
        (u'Curly', u'Søɨŧɇnłɏ!')))
    table.Validate()
    self.AssertRowsEqual(
        [(u'Ṁöë', u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW")],
        table.Select((u'Ṁöë',)))
    self.AssertRowsEqual(
        [(u'Larry', u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.")],
        table.Select((u'Larry',)))
    self.AssertRowsEqual(
        [(u'Ṁöë', u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"),
         (u'Larry', u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."),
         (u'Shemp', u'Hey, Ṁöë! Hey, Larry!'),
         (u'Curly', u'Søɨŧɇnłɏ!')],
        table.Select())
    self.cache.Close()
    self.cache = self.CACHE_MODULE.Cache(self.cache_name)

    table = self.cache.Table(_TEST_TABLE_NAME_1)
    self.AssertRowsEqual(
        [(u'Ṁöë', u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW")],
        table.Select((u'Ṁöë',)))
    self.AssertRowsEqual(
        [(u'Larry', u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ.")],
        table.Select((u'Larry',)))
    self.AssertRowsEqual(
        [(u'Ṁöë', u".TꙅAꟻ ɘↄAlq oᴎ 'ᴎiTTɘg ɘᴙ'ɘW"),
         (u'Larry', u"ι ∂ι∂η'т ωαηηα ѕαу уєѕ, вυт ι ¢συℓ∂η'т ѕαу ησ."),
         (u'Shemp', u'Hey, Ṁöë! Hey, Larry!'),
         (u'Curly', u'Søɨŧɇnłɏ!')],
        table.Select())


class SqliteCacheTests(CacheTests):

  CACHE_MODULE = sqlite_cache


class SqliteCacheTableTests(CacheTableTests):

  CACHE_MODULE = sqlite_cache


class CacheIsValidNameTests(subtests.Base):

  def RunSubTest(self, name):
    return persistent_cache_base.Cache.EncodeName(name)

  def testCacheIsvalidName(self):

    def T(expected, name, exception=None):
      self.Run(expected, name, depth=2, exception=exception)

    T(None, None, exception=exceptions.CacheNameInvalid)
    T(None, '', exception=exceptions.CacheNameInvalid)

    T('abc', 'abc')
    T('a_c', 'a_c')
    T('a-c', 'a-c')
    T('a.c', 'a.c')

    T('a@c', 'a@c')
    T('a%23c', 'a#c')
    T('a%24c', 'a$c')
    T('a%25c', 'a%c')
    T('a%3Ac', 'a:c')
    T('a%2Ac', 'a*c')
    T('a%3Fc', 'a?c')

    T(None, 'abc/', exception=exceptions.CacheNameInvalid)
    T(None, 'a_c/', exception=exceptions.CacheNameInvalid)
    T(None, 'a-c/', exception=exceptions.CacheNameInvalid)
    T(None, 'a.c/', exception=exceptions.CacheNameInvalid)

    T(None, 'abc\\', exception=exceptions.CacheNameInvalid)
    T(None, 'a_c\\', exception=exceptions.CacheNameInvalid)
    T(None, 'a-c\\', exception=exceptions.CacheNameInvalid)
    T(None, 'a.c\\', exception=exceptions.CacheNameInvalid)

    T(r'/abc/xyz', r'/abc/xyz')
    T(r'/abc/x_z', r'/abc/x_z')
    T(r'/a_c/xbz', r'/a_c/xbz')
    T(r'/a_c/x_z', r'/a_c/x_z')
    T(r'/abc/x-z', r'/abc/x-z')
    T(r'/a-c/xbz', r'/a-c/xbz')
    T(r'/a-c/x-z', r'/a-c/x-z')
    T(r'/abc/x.z', r'/abc/x.z')
    T(r'/a.c/xbz', r'/a.c/xbz')
    T(r'/a.c/x.z', r'/a.c/x.z')

    T(r'/abc\xyz', r'/abc\xyz')
    T(r'/abc\x_z', r'/abc\x_z')
    T(r'/a_c\xbz', r'/a_c\xbz')
    T(r'/a_c\x_z', r'/a_c\x_z')
    T(r'/abc\x-z', r'/abc\x-z')
    T(r'/a-c\xbz', r'/a-c\xbz')
    T(r'/a-c\x-z', r'/a-c\x-z')
    T(r'/abc\x.z', r'/abc\x.z')
    T(r'/a.c\xbz', r'/a.c\xbz')
    T(r'/a.c\x.z', r'/a.c\x.z')

    T(r'\abc/xyz', r'\abc/xyz')
    T(r'\abc/x_z', r'\abc/x_z')
    T(r'\a_c/xbz', r'\a_c/xbz')
    T(r'\a_c/x_z', r'\a_c/x_z')
    T(r'\abc/x-z', r'\abc/x-z')
    T(r'\a-c/xbz', r'\a-c/xbz')
    T(r'\a-c/x-z', r'\a-c/x-z')
    T(r'\abc/x.z', r'\abc/x.z')
    T(r'\a.c/xbz', r'\a.c/xbz')
    T(r'\a.c/x.z', r'\a.c/x.z')

    T(r'\abc\xyz', r'\abc\xyz')
    T(r'\abc\x_z', r'\abc\x_z')
    T(r'\a_c\xbz', r'\a_c\xbz')
    T(r'\a_c\x_z', r'\a_c\x_z')
    T(r'\abc\x-z', r'\abc\x-z')
    T(r'\a-c\xbz', r'\a-c\xbz')
    T(r'\a-c\x-z', r'\a-c\x-z')
    T(r'\abc\x.z', r'\abc\x.z')
    T(r'\a.c\xbz', r'\a.c\xbz')
    T(r'\a.c\x.z', r'\a.c\x.z')

    T('a@c/xyz', 'a@c/xyz')
    T('a#c/xyz', 'a#c/xyz')
    T('a$c/xyz', 'a$c/xyz')
    T('a%c/xyz', 'a%c/xyz')
    T('a:c/xyz', 'a:c/xyz')
    T('a*c/xyz', 'a*c/xyz')
    T('a?c/xyz', 'a?c/xyz')


class CacheTableEncodeNameTests(subtests.Base):

  def RunSubTest(self, name):
    return persistent_cache_base.Table.EncodeName(name)

  def testCacheTableIsvalidName(self):

    def T(expected, name, exception=None):
      self.Run(expected, name, depth=2, exception=exception)

    T(None, None, exception=exceptions.CacheTableNameInvalid)
    T(None, '', exception=exceptions.CacheTableNameInvalid)

    T('abc', 'abc')
    T('a_c', 'a_c')
    T('a-c', 'a-c')
    T('a.c', 'a.c')

    T('a@c', 'a@c')
    T('a%23c', 'a#c')
    T('a%24c', 'a$c')
    T('a%25c', 'a%c')
    T('a%3Ac', 'a:c')
    T('a%2Ac', 'a*c')
    T('a%3Fc', 'a?c')

    T('%2Fabc%2Fxyz', r'/abc/xyz')
    T('%2Fabc%2Fx_z', r'/abc/x_z')
    T('%2Fa_c%2Fxbz', r'/a_c/xbz')
    T('%2Fa_c%2Fx_z', r'/a_c/x_z')
    T('%2Fabc%2Fx-z', r'/abc/x-z')
    T('%2Fa-c%2Fxbz', r'/a-c/xbz')
    T('%2Fa-c%2Fx-z', r'/a-c/x-z')
    T('%2Fabc%2Fx.z', r'/abc/x.z')
    T('%2Fa.c%2Fxbz', r'/a.c/xbz')
    T('%2Fa.c%2Fx.z', r'/a.c/x.z')

    T('%2Fabc%5Cxyz', r'/abc\xyz')
    T('%2Fabc%5Cx_z', r'/abc\x_z')
    T('%2Fa_c%5Cxbz', r'/a_c\xbz')
    T('%2Fa_c%5Cx_z', r'/a_c\x_z')
    T('%2Fabc%5Cx-z', r'/abc\x-z')
    T('%2Fa-c%5Cxbz', r'/a-c\xbz')
    T('%2Fa-c%5Cx-z', r'/a-c\x-z')
    T('%2Fabc%5Cx.z', r'/abc\x.z')
    T('%2Fa.c%5Cxbz', r'/a.c\xbz')
    T('%2Fa.c%5Cx.z', r'/a.c\x.z')

    T('%5Cabc%2Fxyz', r'\abc/xyz')
    T('%5Cabc%2Fx_z', r'\abc/x_z')
    T('%5Ca_c%2Fxbz', r'\a_c/xbz')
    T('%5Ca_c%2Fx_z', r'\a_c/x_z')
    T('%5Cabc%2Fx-z', r'\abc/x-z')
    T('%5Ca-c%2Fxbz', r'\a-c/xbz')
    T('%5Ca-c%2Fx-z', r'\a-c/x-z')
    T('%5Cabc%2Fx.z', r'\abc/x.z')
    T('%5Ca.c%2Fxbz', r'\a.c/xbz')
    T('%5Ca.c%2Fx.z', r'\a.c/x.z')

    T('%5Cabc%5Cxyz', r'\abc\xyz')
    T('%5Cabc%5Cx_z', r'\abc\x_z')
    T('%5Ca_c%5Cxbz', r'\a_c\xbz')
    T('%5Ca_c%5Cx_z', r'\a_c\x_z')
    T('%5Cabc%5Cx-z', r'\abc\x-z')
    T('%5Ca-c%5Cxbz', r'\a-c\xbz')
    T('%5Ca-c%5Cx-z', r'\a-c\x-z')
    T('%5Cabc%5Cx.z', r'\abc\x.z')
    T('%5Ca.c%5Cxbz', r'\a.c\xbz')
    T('%5Ca.c%5Cx.z', r'\a.c\x.z')

    T('a@c%2Fxyz', 'a@c/xyz')
    T('a%23c%2Fxyz', 'a#c/xyz')
    T('a%24c%2Fxyz', 'a$c/xyz')
    T('a%25c%2Fxyz', 'a%c/xyz')
    T('a%3Ac%2Fxyz', 'a:c/xyz')
    T('a%2Ac%2Fxyz', 'a*c/xyz')
    T('a%3Fc%2Fxyz', 'a?c/xyz')


if __name__ == '__main__':
  cli_test_base.main()
