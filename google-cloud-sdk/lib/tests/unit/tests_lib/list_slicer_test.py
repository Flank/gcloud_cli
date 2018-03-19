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
"""Unit ests for tests.lib.api_lib.util.list_slicer."""


from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer


class ListSlicerTest(test_case.TestCase):

  def testPageSizeEqualsListLength(self):
    list_ = range(100)
    page_size = 100
    expected_slices_list = [slice(0, None, None)]
    expect_token_pairs_list = [(None, None)]
    actual_slices, actual_token_pairs = list_slicer.SliceList(list_, page_size)
    self.assertEqual((expected_slices_list, expect_token_pairs_list),
                     (list(actual_slices), list(actual_token_pairs)))

  def testPageSizeSmallerThanListLength(self):
    list_ = range(100)
    page_size = 80
    expected_slices_list = [slice(0, 80, None), slice(80, None, None)]
    expect_token_pairs_list = [(None, 'TOKEN80'), ('TOKEN80', None)]
    actual_slices, actual_token_pairs = list_slicer.SliceList(list_, page_size)
    self.assertEqual((expected_slices_list, expect_token_pairs_list),
                     (list(actual_slices), list(actual_token_pairs)))

  def testPageSizeMuchSmallerThanListLength(self):
    list_ = range(100)
    page_size = 6
    expected_slices_list = [slice(0, 6, None), slice(6, 12, None),
                            slice(12, 18, None), slice(18, 24, None),
                            slice(24, 30, None), slice(30, 36, None),
                            slice(36, 42, None), slice(42, 48, None),
                            slice(48, 54, None), slice(54, 60, None),
                            slice(60, 66, None), slice(66, 72, None),
                            slice(72, 78, None), slice(78, 84, None),
                            slice(84, 90, None), slice(90, 96, None),
                            slice(96, None, None)]
    expect_token_pairs_list = [(None, 'TOKEN6'), ('TOKEN6', 'TOKEN12'),
                               ('TOKEN12', 'TOKEN18'), ('TOKEN18', 'TOKEN24'),
                               ('TOKEN24', 'TOKEN30'), ('TOKEN30', 'TOKEN36'),
                               ('TOKEN36', 'TOKEN42'), ('TOKEN42', 'TOKEN48'),
                               ('TOKEN48', 'TOKEN54'), ('TOKEN54', 'TOKEN60'),
                               ('TOKEN60', 'TOKEN66'), ('TOKEN66', 'TOKEN72'),
                               ('TOKEN72', 'TOKEN78'), ('TOKEN78', 'TOKEN84'),
                               ('TOKEN84', 'TOKEN90'), ('TOKEN90', 'TOKEN96'),
                               ('TOKEN96', None)]
    actual_slices, actual_token_pairs = list_slicer.SliceList(list_, page_size)
    self.assertEqual((expected_slices_list, expect_token_pairs_list),
                     (list(actual_slices), list(actual_token_pairs)))

  def testEmptyList(self):
    list_ = []
    page_size = 6
    expected_slices_list = []
    expect_token_pairs_list = []
    actual_slices, actual_token_pairs = list_slicer.SliceList(list_, page_size)
    self.assertEqual((expected_slices_list, expect_token_pairs_list),
                     (list(actual_slices), list(actual_token_pairs)))

  def testPageSizeZero(self):
    list_ = range(100)
    page_size = 0
    with self.assertRaisesRegexp(
        ValueError, r'range\(\) step argument must not be zero'):
      list_slicer.SliceList(list_, page_size)


if __name__ == '__main__':
  test_case.main()
