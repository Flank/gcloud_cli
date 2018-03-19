# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Unit tests for simplify_path."""

from googlecloudsdk.api_lib.compute import path_simplifier
from tests.lib import test_case


class SimplifyPathTest(test_case.TestCase):

  def SetUp(self):
    self.paths = {
        'global': 'https://www.example.com/projects/my-project/names/my-name',
        'regional': (
            'https://www.example.com/projects/my-project/regions/my-region/'
            'names/my-name'),
        'zonal': (
            'https://www.example.com/projects/my-project/zones/my-zone/names/'
            'my-name'),
    }

  def testName(self):
    for _, path in self.paths.iteritems():
      name = path_simplifier.Name(path)
      self.assertEqual('my-name', name)

  def testScopedSuffix(self):
    expected_suffix = {
        'global': 'my-name',
        'regional': 'my-region/names/my-name',
        'zonal': 'my-zone/names/my-name',
    }

    for object_type, path in self.paths.iteritems():
      suffix = path_simplifier.ScopedSuffix(path)
      self.assertEqual(expected_suffix[object_type], suffix)

  def testProjectSuffix(self):
    expected_suffix = {
        'global': 'my-project/names/my-name',
        'regional': 'my-project/regions/my-region/names/my-name',
        'zonal': 'my-project/zones/my-zone/names/my-name',
    }

    for object_type, path in self.paths.iteritems():
      suffix = path_simplifier.ProjectSuffix(path)
      self.assertEqual(expected_suffix[object_type], suffix)


if __name__ == '__main__':
  test_case.main()
