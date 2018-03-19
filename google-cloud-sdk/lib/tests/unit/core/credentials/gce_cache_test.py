# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for gce properties."""

import httplib
import os
import socket
import urllib2

from googlecloudsdk.core.credentials import gce_cache
from tests.lib import sdk_test_base
from tests.lib import test_case
import mock


class GCECacheTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.current_time = 1000
    self.StartPatch('time.time', return_value=self.current_time)
    self.tempfilepath = os.path.join(self.temp_path, 'gce')
    self.StartPatch(
        'googlecloudsdk.core.config.Paths.GCECachePath',
        return_value=self.tempfilepath)
    self._SetUpServerResponse(error=urllib2.URLError(''))

  def _SetUpFile(self, contents, mtime):
    with open(self.tempfilepath, 'w') as f:
      f.write(contents)
    os.utime(self.tempfilepath, (0, mtime))

  def _SetUpServerResponse(self, error=None):
    method_to_patch = 'googlecloudsdk.core.credentials.gce_read.ReadNoProxy'
    if error:
      self.StartPatch(method_to_patch, side_effect=error)
    else:
      self.StartPatch(method_to_patch, return_value='123')

  # In these tests, the answer is retrieved from memory.
  def testGetOnGCE_InMemoryTrue(self):
    on_gce_cache = gce_cache._OnGCECache(True, self.current_time)
    self.assertTrue(on_gce_cache.GetOnGCE())

  def testGetOnGCE_InMemoryFalse(self):
    on_gce_cache = gce_cache._OnGCECache(False, self.current_time)
    on_gce = on_gce_cache.GetOnGCE()
    # Use assertIs, not assertFalse, to distinguish from None
    self.assertIs(on_gce, False)

  def testGetOnGCE_InMemoryTrue_ExpiredNoCheckAge(self):
    on_gce_cache = gce_cache._OnGCECache(True, self.current_time - 1)
    self.assertTrue(on_gce_cache.GetOnGCE(check_age=False))

  # In these tests, the answer is read from disk.
  # The memory cache should be updated.
  def testGetOnGce_NotInMemory_OnDiskTrue(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpFile('True', self.current_time - gce_cache._GCE_CACHE_MAX_AGE)
    self.assertTrue(on_gce_cache.GetOnGCE())

    self.assertTrue(on_gce_cache.connected)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time)

  def testGetOnGce_InMemoryExpired_OnDiskTrue(self):
    on_gce_cache = gce_cache._OnGCECache(False, self.current_time - 1)
    self._SetUpFile('True', self.current_time - gce_cache._GCE_CACHE_MAX_AGE)
    self.assertTrue(on_gce_cache.GetOnGCE())

    self.assertTrue(on_gce_cache.connected)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time)

  def testGetOnGce_NotInMemory_OnDisk_False(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpFile('False', self.current_time - gce_cache._GCE_CACHE_MAX_AGE)
    self.assertIs(on_gce_cache.GetOnGCE(), False)

    self.assertIs(on_gce_cache.connected, False)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time)

  def testGetOnGce_NotInMemory_OnDisk_Empty(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpFile('False', self.current_time - gce_cache._GCE_CACHE_MAX_AGE)
    self.assertIs(on_gce_cache.GetOnGCE(), False)

    self.assertIs(on_gce_cache.connected, False)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time)

  def testGetOnGce_NotInMemory_OnDisk_Corrupt(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpFile('bad"%!', self.current_time - gce_cache._GCE_CACHE_MAX_AGE)
    self.assertIs(on_gce_cache.GetOnGCE(), False)

    self.assertIs(on_gce_cache.connected, False)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time)

  def testGetOnGce_NotInMemory_OnDisk_ExpiredNoCheckAge(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpFile('True',
                    self.current_time - gce_cache._GCE_CACHE_MAX_AGE - 1)
    self.assertTrue(on_gce_cache.GetOnGCE(check_age=False))

    self.assertIs(on_gce_cache.connected, True)
    # Should be current time, since file mtime was:
    #     current_time - _GCE_CACHE_MAX_AGE
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time - 1)

  # In these tests, the answer is computed by attempting to reach the server.
  # The memory and and disk caches should be updated.
  def testGetOnGce_NotInMemory_NotOnDisk_ServerResponds(self):
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpServerResponse()
    self.assertTrue(on_gce_cache.GetOnGCE())

    self.assertTrue(on_gce_cache.connected)
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time + gce_cache._GCE_CACHE_MAX_AGE)

    self.AssertFileExistsWithContents('True', self.tempfilepath)

  def testGetOnGce_NotInMemory_NotOnDisk_ServerResponds_NoCheckAge(self):
    # Should be identical to testGetOnGce_NotInMemory_NotOnDisk_ServerResponds
    on_gce_cache = gce_cache._OnGCECache()
    self._SetUpServerResponse()
    self.assertTrue(on_gce_cache.GetOnGCE(check_age=False))

    self.assertTrue(on_gce_cache.connected)
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time + gce_cache._GCE_CACHE_MAX_AGE)

    self.AssertFileExistsWithContents('True', self.tempfilepath)

  def testGetOnGce_NotInMemory_NotOnDisk_ServerDoesntRespond(self):
    on_gce_cache = gce_cache._OnGCECache()
    self.assertIs(on_gce_cache.GetOnGCE(), False)

    self.assertIs(on_gce_cache.connected, False)
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time + gce_cache._GCE_CACHE_MAX_AGE)

    self.AssertFileExistsWithContents('False', self.tempfilepath)

  def testGetOnGce_NotInMemory_NotOnDisk_CheckServerErrors(self):
    errors = (
        urllib2.URLError(''),
        urllib2.HTTPError(None, None, None, None, None),
        socket.timeout(''),
        socket.error(''),
        socket.herror(''),
        socket.gaierror(''),
        httplib.BadStatusLine('')
    )
    for error in errors:
      self._SetUpServerResponse(error=error)
      on_gce_cache = gce_cache._OnGCECache()

      self.assertIs(on_gce_cache.GetOnGCE(), False)
      self.assertIs(on_gce_cache.connected, False)
      self.AssertFileExistsWithContents('False', self.tempfilepath)

  def testGetOnGce_InMemoryExpired_OnDiskExpired_ServerResponds(self):
    on_gce_cache = gce_cache._OnGCECache(False, self.current_time - 1)
    self._SetUpFile('False',
                    self.current_time - gce_cache._GCE_CACHE_MAX_AGE - 1)
    self._SetUpServerResponse()
    self.assertTrue(on_gce_cache.GetOnGCE())

    self.assertTrue(on_gce_cache.connected)
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time + gce_cache._GCE_CACHE_MAX_AGE)

    self.AssertFileExistsWithContents('True', self.tempfilepath)

  def testGetOnGce_InMemoryExpired_OnDiskError_ServerResponds(self):
    on_gce_cache = gce_cache._OnGCECache(False, self.current_time - 1)
    self._SetUpFile('False',
                    self.current_time - gce_cache._GCE_CACHE_MAX_AGE - 1)
    self._SetUpServerResponse()
    # Use the decorator because holding onto this any longer than necessary can
    # obscure errors.
    with mock.patch('__builtin__.open', side_effect=IOError()):
      on_gce = on_gce_cache.GetOnGCE()
    self.assertTrue(on_gce)

    self.assertTrue(on_gce_cache.connected)
    self.assertEqual(on_gce_cache.expiration_time,
                     self.current_time + gce_cache._GCE_CACHE_MAX_AGE)
    # Don't check the cache file because we mocked out open() and gave errors.


if __name__ == '__main__':
  test_case.main()
