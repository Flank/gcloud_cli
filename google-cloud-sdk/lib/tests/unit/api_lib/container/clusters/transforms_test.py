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

"""Unit tests for the transforms module."""

import datetime

from googlecloudsdk.api_lib.container import transforms
from googlecloudsdk.core.util import times
from tests.lib import test_case
from tests.lib.surface.container import base


class TransformsTest(test_case.Base):

  def SetUp(self):
    # Mock out now for consistent results.
    now = datetime.datetime(2016, 11, 4, 11, 15, 32, tzinfo=times.UTC)
    self.StartPatch('googlecloudsdk.core.util.times.Now', return_value=now)

  def _TestMasterVersionTransform(self, resource, expected):
    self.assertEqual(transforms.TransformMasterVersion(resource), expected)

  def testRegular(self):
    self._TestMasterVersionTransform(
        resource={
            'name': 'regular',
            'currentMasterVersion': '1.3.1',
        },
        expected='1.3.1')

  def testRegular5dTTL(self):
    self._TestMasterVersionTransform(
        resource={
            'currentMasterVersion': '1.3.2',
            'enableKubernetesAlpha': '',
            'expireTime': base.format_date_time('P5D'),
        },
        expected='1.3.2 (! 5 days left !)')

  def testAlpha30dTTL(self):
    self._TestMasterVersionTransform(
        resource={
            'currentMasterVersion': '1.3.3',
            'expireTime': base.format_date_time('P30D'),
            'enableKubernetesAlpha': True,
        },
        expected='1.3.3 ALPHA (30 days left)')

  def testAlpha10dTTL(self):
    self._TestMasterVersionTransform(
        resource={
            'currentMasterVersion': '1.3.4',
            'enableKubernetesAlpha': True,
            'expireTime': base.format_date_time('P10D'),
        },
        expected='1.3.4 ALPHA (! 10 days left !)')

  def testInvalidTTL(self):
    self._TestMasterVersionTransform(
        resource={
            'currentMasterVersion': '1.3.6',
            'expireTime': 'i am not a timestamp',
        },
        expected='')

  def testMissingVersion(self):
    self._TestMasterVersionTransform(
        resource={
            'name': 'missing version',
        },
        expected='')


if __name__ == '__main__':
  test_case.main()
