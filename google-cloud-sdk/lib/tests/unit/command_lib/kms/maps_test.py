# -*- coding: utf-8 -*- #
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
"""Unit tests for third_party.py.googlecloudsdk.command_lib.kms.maps."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.kms import maps
from tests.lib import test_case
from tests.lib.surface.kms import base


class MapsTest(base.KmsMockTest):

  def SetUp(self):
    self.valid_algorithms_map_values = []
    for algorithms in maps.VALID_ALGORITHMS_MAP.values():
      self.valid_algorithms_map_values += algorithms

  def testAllMapsKeysAreUnique(self):
    assert len(set(maps.PURPOSE_MAP.keys())) == len(maps.PURPOSE_MAP.keys())

  def testPurposeMapValuesMatchValidAlgorithmsMapKeys(self):
    for purpose in maps.PURPOSE_MAP.values():
      assert purpose in maps.VALID_ALGORITHMS_MAP.keys()

    for purpose in maps.VALID_ALGORITHMS_MAP.keys():
      assert purpose in maps.PURPOSE_MAP.values()

  def testAlgorithmMapKeysMatchValidAlgorithmsMapValues(self):
    for algorithm in maps.ALL_ALGORITHMS:
      if algorithm != 'crypto-key-version-algorithm-unspecified':
        assert algorithm in self.valid_algorithms_map_values, algorithm

    for algorithm in self.valid_algorithms_map_values:
      assert algorithm in maps.ALL_ALGORITHMS


if __name__ == '__main__':
  test_case.main()
