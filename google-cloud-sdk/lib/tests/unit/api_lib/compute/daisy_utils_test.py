# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Tests for googlecloudsdk.api_lib.compute.daisy_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import daisy_utils
from tests.lib import test_case


class DaisyUtilsTest(test_case.TestCase):

  def testSafeBucketNameNoGoogle(self):
    self._AssertSafeBucketName('new-google-maps-storage',
                               'new-go-ogle-maps-storage')
    self._AssertSafeBucketName('google', 'go-ogle')
    self._AssertSafeBucketName('#google#', '#go-ogle#')

  def testSafeBucketNameNoStartWithGoog(self):
    self._AssertSafeBucketName('goog-maps-storage', 'go-og-maps-storage')
    self._AssertSafeBucketName('new-goog-maps-storage', 'new-goog-maps-storage')
    self._AssertSafeBucketName('goog', 'go-og')
    self._AssertSafeBucketName('goog#', 'go-og#')
    self._AssertSafeBucketName('#goog', '#goog')

    # Test some special case
    self._AssertSafeBucketName('googogle', 'go-ogogle')
    self._AssertSafeBucketName('googgle', 'go-oggle')
    self._AssertSafeBucketName('googoogle', 'go-ogo-ogle')
    self._AssertSafeBucketName('goog-google', 'go-og-go-ogle')

  def _AssertSafeBucketName(self, original, expected):
    safe_bucket_name = daisy_utils._GetSafeBucketName(original)

    # Check whether the bucket name follows naming rule.
    self.assertNotIn('google', safe_bucket_name)
    self._AssertNotStartWith(safe_bucket_name, 'goog')

    # Check whether the bucket name is as expected
    self.assertEqual(expected, safe_bucket_name)

  def _AssertNotStartWith(self, actual, unexpected_start):
    if actual.startswith(unexpected_start):
      self.fail('%r does start with %r' % (actual, unexpected_start))


if __name__ == '__main__':
  test_case.main()
