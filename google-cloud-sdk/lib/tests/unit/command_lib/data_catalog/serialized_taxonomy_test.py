# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Data Catalog serialized taxonomy tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.data_catalog.taxonomies import util
from tests.lib import parameterized
from tests.lib import test_case


class SerializedTaxonomyTest(test_case.TestCase, parameterized.TestCase):
  """Data Catalog serialized taxonomy tests class."""

  def testProcessInlineSourceFromFileInvalidDict(self):
    contents = [None]
    with self.assertRaisesRegex(
        util.InvalidInlineSourceError,
        r'An error occurred while parsing the '
        r'serialized taxonomy. Please check your '
        r'input file.'):
      print(util.ProcessTaxonomiesFromYAML(contents, 'v1beta1'))

  def testProcessInlineSourceFromFileUnrecognizedFields(self):
    policy_tag = {
        'description': '0',
        'displayName': 'Root',
        'policyTag': 'projects/594977690804/locations/us/taxonomies/740332'
    }
    contents = {
        'wrong_key': [
            {
                'description': 'Response for the import',
                'displayName': 'A taxonomy',
                'policyTags': [policy_tag]
            }
        ]
    }
    with self.assertRaisesRegex(
        util.InvalidInlineSourceError,
        r'(?m)Invalid inline source, the following fields are unrecognized:\n'
        r'inlineSource.wrong_key'):
      util.ProcessTaxonomiesFromYAML(contents, 'v1beta1')


if __name__ == '__main__':
  test_case.main()
