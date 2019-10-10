# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the command_lib.util.cache_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.meta import cache_util as meta_cache_util
from googlecloudsdk.command_lib.util import cache_util
from googlecloudsdk.core import resources
from tests.lib import calliope_test_base
from tests.lib import test_case
from tests.lib.core.cache import fake


class CacheResourceTest(test_case.TestCase):

  def testCacheResource(self):
    refs = {
        'a': [
            resources.REGISTRY.Create('compute.zones', project='p', zone='a')
        ],
        'b': [
            resources.REGISTRY.Create('compute.zones', project='p', zone='b1'),
            resources.REGISTRY.Create('compute.zones', project='p', zone='b2'),
        ]
    }
    cache = fake.Cache('fake://dummy', create=True)
    self.StartObjectPatch(meta_cache_util.GetCache, '_OpenCache',
                          return_value=cache)

    @cache_util.CacheResource('my resource')
    def GetResource(key):
      return refs[key].pop(0)

    # pylint: disable=too-many-function-args,unexpected-keyword-arg
    with meta_cache_util.GetCache('resource://') as cache:
      # No args set; uses key as argument
      self.assertTrue(refs['a'])
      self.assertEqual(GetResource(cache, 'a').RelativeName(),
                       'projects/p/zones/a')
      self.assertFalse(refs['a'])
      self.assertEqual(GetResource(cache, 'a').RelativeName(),
                       'projects/p/zones/a')
      # Args set
      self.assertEqual(GetResource(cache, 'c', args=('b',)).RelativeName(),
                       'projects/p/zones/b1')
      self.assertEqual(GetResource(cache, 'c').RelativeName(),
                       'projects/p/zones/b1')
      cache.Invalidate()  # After invalidating, call the function again
      self.assertEqual(GetResource(cache, 'c', args=('b',)).RelativeName(),
                       'projects/p/zones/b2')

if __name__ == '__main__':
  calliope_test_base.main()
