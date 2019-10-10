# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Tests to make sure that generated resources module is correct."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_internal
from tests.lib import test_case


class ResourcesTest(test_case.TestCase):

  def testCanImportEveryModule(self):
    for api_name in apis_internal._GetApiNames():
      for api_version in apis_internal._GetVersions(api_name):
        collections = list(
            apis_internal._GetApiCollections(api_name, api_version))
        for collection in collections:
          self.assertEqual(api_name, collection.api_name)


if __name__ == '__main__':
  test_case.main()

