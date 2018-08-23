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

"""Unit tests for googlecloudsdk.api_lib.app.service_util."""

from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from googlecloudsdk.api_lib.app import service_util
from tests.lib import test_case

DECIMAL_PRECISION = 3


class ServiceUtilTest(test_case.TestCase):

  def testSplitRespectsDecimalPrecision(self):
    """Tests that unparsed traffic splits properly respect precision."""

    # These allocations sum to 0.9999999999999999
    unparsed_allocations = {"v1": 50, "v2": 41, "v3": 9}
    result = service_util.ParseTrafficAllocations(unparsed_allocations,
                                                  DECIMAL_PRECISION)

    expected_result = {"v1": 0.5, "v2": 0.41, "v3": 0.09}
    self.assertEqual(result, expected_result)

  def testLessThanOneHundredIsRoundedUp(self):
    """Tests that allocations which sum less than 100 are rounded up to 100."""
    split = {"v1": 33, "v2": 33, "v3": 33}
    result = service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

    # v1 is expected to round up, since it is the first version in a sort and
    # all allocations are equally max.
    expected_result = {"v1": 0.334, "v2": 0.333, "v3": 0.333}
    self.assertEqual(result, expected_result)

  def testMaximumElementIsRounded(self):
    """Tests that the maximum value is picked as the element that is modified.

    This ensures that we don't mistakenly round the first value down to zero.
    """

    split = {"v1": 0.1, "v2": 49, "v3": 51}
    result = service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

    expected_result = {"v1": 0.001, "v2": 0.49, "v3": 0.509}
    self.assertEqual(result, expected_result)

  def testZeroSum(self):
    """Tests that we fail if all allocations are zero."""

    split = {"v1": 0.0, "v2": 0.0}

    with self.assertRaises(service_util.ServicesSplitTrafficError):
      service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

  def testSingleZero(self):
    """Tests that we fail if one allocation is zero."""

    split = {"v1": 1.0, "v2": 0.0}

    with self.assertRaises(service_util.ServicesSplitTrafficError):
      service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

  def testSingleRoundedDownToZero(self):
    """Tests that we fail if one allocation is rounded down to zero."""

    split = {"v1": 1.0, "v2": 0.0001}

    with self.assertRaises(service_util.ServicesSplitTrafficError):
      service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

  def testSmallNumbersMatter(self):
    """Tests that if we have two tiny numbers with a good split, it's ok."""

    split = {"v1": 0.00008, "v2": 0.00008}
    result = service_util.ParseTrafficAllocations(split, DECIMAL_PRECISION)

    expected_result = {"v1": 0.500, "v2": 0.500}
    self.assertEqual(result, expected_result)


if __name__ == "__main__":
  test_case.main()
