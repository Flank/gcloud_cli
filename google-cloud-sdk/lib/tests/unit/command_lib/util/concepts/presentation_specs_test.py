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

"""Tests for the concepts.presentation_specs module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base


class ResourcePresentationSpecTest(concepts_test_base.ConceptsTestBase,
                                   parameterized.TestCase):
  """Test for presentation specs."""

  def testPresentationSpecValidatesFlagNameOverrides(self):
    """Test error is raised if an incorrect attribute name is provided."""
    with self.AssertRaisesExceptionMatches(
        ValueError,
        'Attempting to override the name for an attribute not present in the '
        'concept: [booksId]. Available attributes: [project, shelf, book]'):
      presentation_specs.ResourcePresentationSpec(
          '--book',
          self.resource_spec,
          'The book',
          flag_name_overrides={'booksId': '--book-flag'})

  @parameterized.named_parameters(
      ('Simple', False, {}, {'shelf': '--shelf', 'book': '--book'}),
      ('WithPrefixes', True, {}, {'shelf': '--book-shelf', 'book': '--book'}),
      ('WithOverrides', False,
       {'project': '--project-flag', 'shelf': '--book-shelf'},
       {'project': '--project-flag', 'shelf': '--book-shelf', 'book': '--book'})
  )
  def testPresentationSpecArgNames(self, prefixes, flag_name_overrides,
                                   expected):
    """Test a resource spec with prefixes=False."""

    resource = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=prefixes,
        flag_name_overrides=flag_name_overrides)

    self.assertEqual(expected, resource.attribute_to_args_map)

  def testPresentationSpecGenerateInfo(self):
    """Tests that presentation spec correctly initializes a ConceptInfo."""
    resource = presentation_specs.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=False)
    concept_info = concept_parsers.ConceptParser([resource]).GetInfo('BOOK')

    self.assertEqual(self.resource_spec.name, concept_info.concept_spec.name)
    self.assertEqual(resource.name, concept_info.presentation_name)
    self.assertFalse(concept_info.plural)
    self.assertTrue(concept_info.allow_empty)
    self.assertEqual('The book to act upon.', concept_info.group_help)
    self.assertEqual({'book': 'BOOK',
                      'shelf': '--shelf'},
                     concept_info.attribute_to_args_map)
    # Ensure that the fallthroughs map is correctly created.
    expected = {
        'book': [],
        'shelf': [],
        'project': [
            deps.PropertyFallthrough(properties.VALUES.core.project)]}
    self.assertEqual(expected, concept_info.fallthroughs_map)


class MultitypePresentationSpecTest(concepts_test_base.MultitypeTestBase,
                                    parameterized.TestCase):

  @parameterized.named_parameters(
      ('Simple', '--book', False, {},
       {'organization': '--organization', 'shelf': '--shelf', 'case': '--case',
        'book': '--book'}),
      ('WithPrefixes', '--book', True, {},
       {'organization': '--book-organization', 'shelf': '--book-shelf',
        'case': '--book-case', 'book': '--book'}),
      ('SimplePositional', 'BOOK', False, {},
       {'organization': '--organization', 'shelf': '--shelf', 'case': '--case',
        'book': 'BOOK'}),
      ('PositionalWithPrefixes', 'BOOK', True, {},
       {'organization': '--book-organization', 'shelf': '--book-shelf',
        'case': '--book-case', 'book': 'BOOK'}),
      ('WithOverrides', '--book', False, {'project': '--project-flag'},
       {'organization': '--organization', 'project': '--project-flag',
        'shelf': '--shelf', 'case': '--case', 'book': '--book'}),
      ('WithOverridesAndPrefixes', '--book', True,
       {'project': '--project-flag'},
       {'organization': '--book-organization', 'project': '--project-flag',
        'shelf': '--book-shelf', 'case': '--book-case', 'book': '--book'}),
      # Someone gives the group a name that doesn't match the renamed anchor.
      # This is fine.
      ('WithOverridesAnchor', 'book', False,
       {'book': '--surprise'},
       {'organization': '--organization', 'shelf': '--shelf',
        'case': '--case', 'book': '--surprise'}),
      # Someone gives the group a name that doesn't match the renamed anchor.
      # May still be used as a prefix.
      ('WithPrefixesAndOverridesAnchor', 'book', True,
       {'book': '--surprise'},
       {'organization': '--book-organization', 'shelf': '--book-shelf',
        'case': '--book-case', 'book': '--surprise'}),
      ('WithPluralName', '--books', True, {},
       {'organization': '--books-organization', 'shelf': '--books-shelf',
        'book': '--books', 'case': '--books-case'}),
      ('WithRandomName', '--surprise', True, {},
       {'organization': '--surprise-organization', 'shelf': '--surprise-shelf',
        'book': '--surprise', 'case': '--surprise-case'})
  )
  def testArgNames(self, name, prefixes, flag_name_overrides, expected):
    resource = presentation_specs.MultitypeResourcePresentationSpec(
        name,
        self.four_way_resource,
        'The book to act upon.',
        prefixes=prefixes,
        flag_name_overrides=flag_name_overrides)

    self.assertEqual(expected, resource.attribute_to_args_map)

  @parameterized.named_parameters(
      ('NoPrefixes', '--x', False, {},
       {'shelf': '--shelf', 'book': '--x'}),
      ('Prefixes', '--x', True, {},
       {'shelf': '--x-shelf', 'book': '--x'}))
  def testArgNamesParentChild(self, name, prefixes, flag_name_overrides,
                              expected):
    resource = presentation_specs.MultitypeResourcePresentationSpec(
        name,
        self.parent_child_resource,
        'The book to act upon.',
        prefixes=prefixes,
        flag_name_overrides=flag_name_overrides)

    self.assertEqual(expected, resource.attribute_to_args_map)

  @parameterized.named_parameters(
      ('NoPrefixes', '--x', False, {},
       # The "name" has no effect without prefixes or an identifiable anchor.
       {'shelf': '--shelf', 'case': '--case',
        'organization': '--organization'}),
      ('Prefixes', '--x', True, {},
       {'shelf': '--x-shelf', 'case': '--x-case',
        'organization': '--x-organization'}),
      ('Overrides', '--x', False, {'case': '--x'},
       {'shelf': '--shelf', 'case': '--x',
        'organization': '--organization'}),
      ('OverridesPrefixes', '--x', True, {'case': '--case'},
       {'shelf': '--x-shelf', 'case': '--case',
        'organization': '--x-organization'}))
  def testArgNamesNoSingleAnchor(self, name, prefixes, flag_name_overrides,
                                 expected):
    resource = presentation_specs.MultitypeResourcePresentationSpec(
        name,
        self.different_anchor_resource,
        'The book to act upon.',
        prefixes=prefixes,
        flag_name_overrides=flag_name_overrides)

    self.assertEqual(expected, resource.attribute_to_args_map)

if __name__ == '__main__':
  test_case.main()
