# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Unit test mixin for completion cache tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
from googlecloudsdk.core.cache import persistent_cache_base
from googlecloudsdk.core.cache import resource_cache
from tests.lib import sdk_test_base
from tests.lib.core.cache import updaters

import mock


class CompletionCacheBase(sdk_test_base.SdkBase):
  """Base class for completion cache tests."""

  def Now(self):
    return self.now

  def Tick(self, seconds=2):
    self.now += seconds

  def SetUp(self):
    # mock the cache dir
    self.StartObjectPatch(
        config.Paths,
        'cache_dir',
        return_value=os.path.join(self.temp_path, 'cache'),
        new_callable=mock.PropertyMock)

    # mock the cache timer
    self.StartObjectPatch(persistent_cache_base, 'Now', side_effect=self.Now)
    self.now = updaters.NOW_START_TIME

    # instantiate objects common to most tests
    self.cache = resource_cache.ResourceCache()

    # show all test failure more diff details
    self.maxDiff = None  # pylint: disable=invalid-name

  def TearDown(self):
    if self.cache:
      self.cache.Close(commit=False)
      self.cache = None

  def GetCacheTableList(self):
    tables = []
    for table_name in self.cache.Select():
      table = self.cache.Table(table_name, create=False)
      tables.append((table.name, table.columns, table.keys, table.timeout,
                     table.modified, int(table.restricted)))
    return sorted(tables)

  def AssertSetEquals(self, seq1, seq2, message=None):
    self.assertEqual(set(seq1), set(seq2), message)

