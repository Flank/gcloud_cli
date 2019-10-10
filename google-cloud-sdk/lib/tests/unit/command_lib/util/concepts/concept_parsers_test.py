# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for the concepts.concept_parsers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import re

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
import mock


class ConceptParsersTest(concepts_test_base.ConceptsTestBase,
                         parameterized.TestCase):
  """Tests of the ConceptParser functionality."""

  def testConceptParserCreatesRuntimeHandler(self):
    """Tests that a runtime handler is created and concept is registered."""
    concept_parser = concept_parsers.ConceptParser(
        [presentation_specs.ResourcePresentationSpec(
            '--book',
            self.resource_spec,
            'The book to act upon.')])

    concept_parser.AddToParser(self.parser)

    self.assertTrue(hasattr(self.parser.data.concept_handler, 'book'))

  def testTwoResourcesInRuntimeHandler(self):
    """Tests that a runtime handler has two concepts registered."""
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--other-book',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=True)

    concept_parser = concept_parsers.ConceptParser([resource, other_resource])
    concept_parser.AddToParser(self.parser)

    self.assertTrue(hasattr(self.parser.data.concept_handler, 'book'))
    self.assertTrue(hasattr(self.parser.data.concept_handler, 'other_book'))

  def testGetInfoError(self):
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.')
    with self.assertRaisesRegexp(ValueError, '[--fake]'):
      concept_parser.GetInfo('--fake')

  def testConceptParserGetExampleArgStringFlag(self):
    """Test the GetExampleArgString method on a flag resource arg."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    concept_parser.AddToParser(self.parser)
    expected = '--book-project=my-book-project --book=my-book --shelf=my-shelf'
    self.assertEqual(expected, concept_parser.GetExampleArgString())

  def testConceptParserGetExampleArgStringPositional(self):
    """Test the GetExampleArgString method on a positional resource arg."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        'book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    concept_parser.AddToParser(self.parser)
    expected = 'my-book --book-project=my-book-project --shelf=my-shelf'
    self.assertEqual(expected, concept_parser.GetExampleArgString())

  def testTwoResourceArgsPositionals(self):
    """Test a concept parser with two positional resource args raises error."""
    resource = presentation_specs.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = presentation_specs.ResourcePresentationSpec(
        'OTHER',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=True)
    with self.assertRaisesRegex(ValueError, re.escape('[BOOK, OTHER]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testTwoResourceArgsConflict(self):
    """Test concept parser raises an error when resource arg names conflict."""
    resource = presentation_specs.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.')
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The second book to act upon.')
    with self.assertRaisesRegex(ValueError, re.escape('[BOOK, --book]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testTwoResourceArgsConflictingFlags(self):
    """Test concept parser raises an error when resource arg names conflict."""
    resource = presentation_specs.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=False)
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=False)
    with self.assertRaisesRegex(ValueError, re.escape('[--shelf]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testResourceArgAddedToGroups(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    group_obj = mock.MagicMock()
    group_add_group = self.StartObjectPatch(group, 'add_group',
                                            return_value=group_obj)
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        group=group,
        prefixes=True)
    concept_parsers.ConceptParser([resource, other_resource]).AddToParser(
        self.parser)
    self.assertEqual(len(group_add_group.call_args_list), 1)
    added_args = [call[0][0] for call in group_obj.add_argument.call_args_list]
    self.assertEqual(['--other', '--other-shelf'],
                     sorted(added_args))

  def testForResourceInGroup(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    group_obj = mock.MagicMock()
    group_add_group = self.StartObjectPatch(group, 'add_group',
                                            return_value=group_obj)
    concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        group=group).AddToParser(self.parser)
    self.assertEqual(len(group_add_group.call_args_list), 1)
    added_args = [call[0][0] for call in group_obj.add_argument.call_args_list]
    self.assertEqual(['--book', '--shelf'],
                     sorted(added_args))

  def testResourceArgsInMutexGroup(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group', mutex=True)
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        group=group,
        prefixes=True)
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        group=group,
        prefixes=True)
    concept_parsers.ConceptParser([resource, other_resource]).AddToParser(
        self.parser)
    with self.AssertRaisesArgumentErrorMatches('At most one of'):
      self.parser.parser.parse_args(['example', '--other', 'otherexample'])


class ParsingTests(concepts_test_base.MultitypeTestBase,
                   parameterized.TestCase):
  """Tests of the entire parsing mechanism."""

  def AssertParsedResultEquals(self, expected, actual, is_multitype=False):
    if is_multitype:
      actual = actual.result
    if expected is None:
      self.assertIsNone(actual)
    else:
      self.assertEqual(expected, actual.RelativeName())

  def AssertParsedListEquals(self, expected, actual, is_multitype=False):
    if is_multitype:
      actual = [item.result for item in actual]
    self.assertEqual(expected, [resource.RelativeName() for resource in actual])

  def PresentationSpecType(self, is_multitype=False):
    if is_multitype:
      return presentation_specs.MultitypeResourcePresentationSpec
    return presentation_specs.ResourcePresentationSpec

  def testSingleParameter(self):
    """Test a resource with only 1 parameter that doesn't get generated."""
    resource = presentation_specs.ResourcePresentationSpec(
        'project',
        concepts.ResourceSpec(
            'example.projects',
            'project',
            projectsId=concepts.ResourceParameterAttributeConfig(
                name='project',
                help_text='The Cloud Project of the {resource}.',
                fallthroughs=[
                    deps.PropertyFallthrough(properties.VALUES.core.project)])),
        'Group Help',
        prefixes=False)
    info = concept_parsers.ConceptParser([resource]).GetInfo('project')

    # No args should be generated.
    args = [arg.name for arg in info.GetAttributeArgs()]
    self.assertEqual([], args)

    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    # Parsing still works and the spec is still registered as 'project' on
    # CONCEPTS even though nothing was generated.
    properties.VALUES.core.project.Set('foo')
    namespace = self.parser.parser.parse_args([])
    self.assertEqual('projects/foo',
                     namespace.CONCEPTS.project.Parse().RelativeName())

  def testAllFallthrough(self):
    """Test a resource where everything has a fallthough."""
    def Fallthrough():
      return '!'
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        concepts.ResourceSpec(
            'example.projects.shelves.books',
            'project',
            projectsId=concepts.ResourceParameterAttributeConfig(
                name='project', help_text='Auxilio aliis.',
                fallthroughs=[
                    deps.PropertyFallthrough(properties.VALUES.core.project)]),
            shelvesId=concepts.ResourceParameterAttributeConfig(
                name='shelf', help_text='Auxilio aliis.',
                fallthroughs=[deps.Fallthrough(Fallthrough, hint='hint')]),
            booksId=concepts.ResourceParameterAttributeConfig(
                name='book', help_text='Auxilio aliis.',
                fallthroughs=[deps.Fallthrough(Fallthrough, hint='hint')])),
        'Group Help',
        prefixes=False)

    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)
    properties.VALUES.core.project.Set('foo')
    namespace = self.parser.parser.parse_args([])
    self.assertEqual('projects/foo/shelves/!/books/!',
                     namespace.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserForResource(self):
    """Test the ForResource method."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(
        ['--book', 'example', '--shelf', 'exampleshelf', '--book-project',
         'example-project'])
    self.assertEqual(
        'projects/example-project/shelves/exampleshelf/books/example',
        namespace.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserForResourceMultipleResources(self):
    """Test the ForResource method."""
    concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'}
    ).AddToParser(self.parser)

    concept_parsers.ConceptParser.ForResource(
        '--other-book',
        self.resource_spec,
        'The other book to act upon.',
        flag_name_overrides={
            'book': '--other-book',
            'project': '--other-book-project',
            'shelf': '--other-book-shelf',
        }
    ).AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(
        ['--book', 'example', '--shelf', 'exampleshelf', '--book-project',
         'example-project', '--other-book', 'example2', '--other-book-shelf',
         'exampleshelf2', '--other-book-project', 'example-project2'])
    self.assertEqual(
        'projects/example-project/shelves/exampleshelf/books/example',
        namespace.CONCEPTS.book.Parse().RelativeName())
    self.assertEqual(
        'projects/example-project2/shelves/exampleshelf2/books/example2',
        namespace.CONCEPTS.other_book.Parse().RelativeName())

  def testConceptParserForResourceRequiredPositional(self):
    """Test the ForResource method parses a required positional correctly.

    This causes the arg to be formatted as a list by the parser, so the
    handler needs to convert it back to a single value.
    """
    concept_parser = concept_parsers.ConceptParser.ForResource(
        'book',
        self.resource_spec,
        'The book to act upon.',
        required=True)
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(
        ['example', '--shelf', 'exampleshelf'])
    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/example'.format(self.Project()),
        namespace.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserForResourceNonRequired(self):
    """Test non-required resource arg allows entire resource to be unspecified.
    """
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.')
    concept_parser.AddToParser(self.parser)
    self.parser.parser.parse_args([])

  def testConceptParserForResourceRequired(self):
    """Test the ForResource method when arg is required."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        required=True)
    concept_parser.AddToParser(self.parser)

    with self.AssertRaisesArgumentErrorMatches(
        'argument (--book : --shelf): Must be specified.'):
      self.parser.parser.parse_args([])

  def testConceptParserForResourceModal(self):
    """Test the ForResource method creates modal anchor arg."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        required=True)
    concept_parser.AddToParser(self.parser)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --shelf: --book must be specified.'):
      self.parser.parser.parse_args(['--shelf', 'myshelf'])

  def testConceptParserForResourceRequiredPositionalRaises(self):
    """Test the ForResource method with a required positional arg."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        required=True)
    concept_parser.AddToParser(self.parser)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --shelf: BOOK must be specified.'):
      self.parser.parser.parse_args(['--shelf', 'exampleshelf'])

  def testConceptParserAndPropertyFallthroughs(self):
    """Tests that the concept parser correctly gets project from property.
    """
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.')
    concept_parser.AddToParser(self.parser)

    parsed_args = self.parser.parser.parse_args(['--book', 'examplebook',
                                                 '--shelf', 'exampleshelf'])

    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/examplebook'.format(
            self.Project()),
        parsed_args.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserForResourceWithPositional(self):
    """Test the ForResource method with a positional arg."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        'BOOK',
        self.resource_spec,
        'The book to act upon.')
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(['example',
                                               '--shelf', 'exampleshelf'])
    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/example'.format(self.Project()),
        namespace.CONCEPTS.book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('Names', False,
       ['example', '--book-shelf', 'exampleshelf', '--other', 'otherbook',
        '--other-shelf', 'othershelf'],
       'projects/fake-project/shelves/exampleshelf/books/example',
       'projects/fake-project/shelves/othershelf/books/otherbook'),
      ('FullySpecified', False,
       ['projects/p1/shelves/s1/books/b1',
        '--other', 'projects/p2/shelves/s2/books/b2'],
       'projects/p1/shelves/s1/books/b1', 'projects/p2/shelves/s2/books/b2'),
      ('MultitypeNames', True,
       ['example', '--book-shelf', 'exampleshelf', '--other', 'otherbook',
        '--other-shelf', 'othershelf'],
       'projects/fake-project/shelves/exampleshelf/books/example',
       'projects/fake-project/shelves/othershelf/books/otherbook'),
      ('MultitypeFullySpecified', True,
       ['projects/p1/shelves/s1/books/b1',
        '--other', 'projects/p2/shelves/s2/books/b2'],
       'projects/p1/shelves/s1/books/b1', 'projects/p2/shelves/s2/books/b2'),
      ('MultitypeNamesDiffTypes', True,
       ['example', '--book-shelf', 'exampleshelf', '--other', 'otherbook',
        '--other-case', 'othercase'],
       'projects/fake-project/shelves/exampleshelf/books/example',
       'projects/fake-project/cases/othercase/books/otherbook'),
      ('MultitypeFullySpecifiedDiffTypes', True,
       ['projects/p1/shelves/s1/books/b1',
        '--other', 'projects/p2/cases/c2/books/b2'],
       'projects/p1/shelves/s1/books/b1', 'projects/p2/cases/c2/books/b2'))
  def testTwoResourceArgs(self, is_multitype, args, first_expected,
                          second_expected):
    """Test a concept parser with two resource args."""
    resource_spec = (
        self.two_way_shelf_case_book if is_multitype else self.resource_spec)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        'book',
        resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = self.PresentationSpecType(is_multitype=is_multitype)(
        '--other',
        resource_spec,
        'The second book to act upon.',
        prefixes=True)
    concept_parser = concept_parsers.ConceptParser([resource, other_resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)
    self.AssertParsedResultEquals(
        first_expected,
        namespace.CONCEPTS.book.Parse(),
        is_multitype=is_multitype)
    self.AssertParsedResultEquals(
        second_expected,
        namespace.CONCEPTS.other.Parse(),
        is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Names', False, '--book', False,
       ['--book', 'b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('Full', False, '--book', False,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('Positional', False, 'book', False,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('PositionalRequired', False, 'book', True,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypeNames', True, '--book', False,
       ['--book', 'b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypeFull', True, '--book', False,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypeDiffType', True, '--book', False,
       ['--book', 'organizations/o1/shelves/s1/books/b1'],
       'organizations/o1/shelves/s1/books/b1'),
      ('MultitypeRequired', True, '--book', True,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypePositional', True, 'book', False,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypePositionalRequired', True, 'book', True,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('MultitypePositionalRequiredDiffType', True, 'book', True,
       ['organizations/o1/shelves/s1/books/b1'],
       'organizations/o1/shelves/s1/books/b1'))
  def testParse(self, is_multitype, name, required, args, expected):
    resource_spec = (self.two_way_resource if is_multitype
                     else self.resource_spec)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        name,
        resource_spec,
        'Group Help',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False,
        required=required,
        plural=False)
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)

    self.AssertParsedResultEquals(
        expected, namespace.CONCEPTS.book.Parse(), is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Names', '--book', False,
       ['--book', 'b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('NamesWithExtra', '--book', False,
       ['--book', 'b1', '--shelf', 's1', '--case', 'c1',
        '--book-project', 'p1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'),
      ('Full', '--book', False,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('FullWithExtra', '--book', False,
       ['--book', 'projects/p1/cases/c1/shelves/s1/books/b1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'),
      ('Required', '--book', True,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('RequiredWithExtra', '--book', True,
       ['--book', 'projects/p1/cases/c1/shelves/s1/books/b1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'),
      ('Positional', 'book', False,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('PositionalWithExtra', 'book', False,
       ['b1', '--case', 'c1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'),
      ('PositionalRequired', 'book', True,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('PositionalRequiredWithExtra', 'book', True,
       ['b1', '--case', 'c1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'),
      ('PositionalRequiredFullySpecified', 'book', True,
       ['projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('PositionalRequiredFullySpecifiedWithExtra', 'book', True,
       ['projects/p1/cases/c1/shelves/s1/books/b1'],
       'projects/p1/cases/c1/shelves/s1/books/b1'))
  def testParseMultitypeExtraAttribute(self, name, required, args, expected):
    resource = self.PresentationSpecType(is_multitype=True)(
        name,
        self.multitype_extra_attribute_in_path,
        'Group Help',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False,
        required=required,
        plural=False)
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)

    self.AssertParsedResultEquals(
        expected, namespace.CONCEPTS.book.Parse(), is_multitype=True)

  @parameterized.named_parameters(
      ('Names', '--book', False,
       ['--book', 'b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('Full', '--book', False,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('Parent', '--book', False,
       ['--book-project', 'p1', '--shelf', 's1'], 'projects/p1/shelves/s1'),
      ('Empty', '--book', False,
       [], None),
      ('Required', '--book', True,
       ['--book', 'projects/p1/shelves/s1/books/b1'],
       'projects/p1/shelves/s1/books/b1'),
      ('Positional', 'book', False,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'),
      ('PositionalRequired', 'book', True,
       ['b1', '--shelf', 's1', '--book-project', 'p1'],
       'projects/p1/shelves/s1/books/b1'))
  def testParseParentChild(self, name, required, args, expected):
    resource_spec = self.parent_child_resource
    resource = self.PresentationSpecType(is_multitype=True)(
        name,
        resource_spec,
        'Group Help',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False,
        required=required,
        plural=False)
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)

    self.AssertParsedResultEquals(
        expected, namespace.CONCEPTS.book.Parse(), is_multitype=True)

  @parameterized.named_parameters(
      ('Names', False, '--books', False,
       ['--books', 'b1,b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('Full', False, '--books', False,
       ['--books',
        'projects/p1/shelves/s1/books/b1,projects/p2/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p2/shelves/s2/books/b2']),
      ('Positional', False, 'books', False,
       ['b1', 'b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('PositionalRequired', False, 'books', True,
       ['b1', 'b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('MultitypeNames', True, '--books', False,
       ['--books', 'b1,b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('MultitypeFull', True, '--books', False,
       ['--books',
        'projects/p1/shelves/s1/books/b1,projects/p2/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p2/shelves/s2/books/b2']),
      ('MultitypeDiffTypes', True, '--books', False,
       ['--books',
        'projects/p1/shelves/s1/books/b1,'
        'organizations/o1/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2']),
      ('MultitypeRequiredDiffTypes', True, '--books', True,
       ['--books',
        'projects/p1/shelves/s1/books/b1,'
        'organizations/o1/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2']),
      ('MultitypePositional', True, 'books', False,
       ['b1', 'b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('MultitypePositionalRequired', True, 'books', True,
       ['b1', 'b2', '--shelf', 's1', '--book-project', 'p1'],
       ['projects/p1/shelves/s1/books/b1', 'projects/p1/shelves/s1/books/b2']),
      ('MultitypePositionalDiffTypes', True, 'books', False,
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2']),
      ('MultitypePositionalRequiredDiffTypes', True, 'books', True,
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2'],
       ['projects/p1/shelves/s1/books/b1',
        'organizations/o1/shelves/s2/books/b2']))
  def testParsePlural(self, is_multitype, name, required, args, expected):
    resource_spec = (self.two_way_resource if is_multitype
                     else self.resource_spec)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        name,
        resource_spec,
        'Group Help',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False,
        required=required,
        plural=True)
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)

    self.AssertParsedListEquals(
        expected, namespace.CONCEPTS.books.Parse(), is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Nonrequired', False, '--book', False, []),
      ('Required', False, '--book', True, []),
      ('NonrequiredPositional', False, 'book', False, []),
      ('RequiredPositional', False, 'book', True, []),
      ('MultitypeNonrequired', True, '--book', False, ['--book-project', '!']),
      ('MultitypeRequired', True, '--book', True, ['--book-project', '!']),
      ('MultitypeNonrequiredPositional', True, 'book', False,
       ['--book-project', '!']),
      ('MultitypeRequiredPositional', True, 'book', True,
       ['--book-project', '!']))
  def testParseAnchorFallthrough(self, is_multitype, name, rsrc_required, args):
    """Tests resource can be parsed when there are fallthroughs for anchor."""
    resource_spec = self.SetUpFallthroughSpec(is_multitype=is_multitype)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        name,
        resource_spec,
        'Group Help',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False,
        required=rsrc_required)
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)
    self.AssertParsedResultEquals('projects/!/shelves/!/books/!',
                                  namespace.CONCEPTS.book.Parse(),
                                  is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Nonrequired', False, '--books', False,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), []),
      ('Required', False, '--books', True,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), []),
      ('NonrequiredPositional', False, 'books', False,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), []),
      ('RequiredPositional', False, 'books', True,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), []),
      ('PropertyFallthrough', False, '--books', False,
       deps.PropertyFallthrough(properties.VALUES.core.project), []),
      ('ArgFallthrough', False, '--books', False,
       deps.ArgFallthrough('--other'), ['--other', 'xyz']),
      ('MultitypeNonrequired', True, '--books', False,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), ['--book-project', 'xyz']),
      ('MultitypeRequired', True, '--books', True,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), ['--book-project', 'xyz']),
      ('MultitypeNonrequiredPositional', True, 'books', False,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), ['--book-project', 'xyz']),
      ('MultitypeRequiredPositional', True, 'books', True,
       deps.Fallthrough(lambda: ['xyz'], hint='h'), ['--book-project', 'xyz']),
      ('MultitypePropertyFallthrough', True, '--books', False,
       deps.PropertyFallthrough(properties.VALUES.core.project),
       ['--book-project', 'xyz']))
  def testParsePluralAnchorFallthrough(self, is_multitype, name, rsrc_required,
                                       fallthrough, args):
    """Tests plural resource args parse when there's an anchor fallthrough."""
    properties.VALUES.core.project.Set('xyz')
    resource_spec = self.SetUpFallthroughSpec(fallthrough=fallthrough,
                                              is_multitype=is_multitype)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        name,
        resource_spec,
        'Group Help',
        prefixes=False,
        required=rsrc_required,
        plural=True,
        flag_name_overrides={'project': '--book-project'}
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)
    self.parser.add_argument('--other', help='h')

    namespace = self.parser.parser.parse_args(args)
    self.AssertParsedListEquals(
        ['projects/xyz/shelves/xyz/books/xyz'],
        namespace.CONCEPTS.books.Parse(),
        is_multitype=is_multitype)

  def testParsePluralAnchorFallthroughMultitypeArgFallthrough(self):
    properties.VALUES.core.project.Set('xyz')
    fallthrough = deps.ArgFallthrough('--other')
    resource_spec = self.SetUpFallthroughSpec(fallthrough=fallthrough,
                                              is_multitype=True)
    # Remove the fallthrough for the organization.
    for attribute in resource_spec.attributes:
      if attribute.name == 'organization':
        attribute.fallthroughs = []
    resource = self.PresentationSpecType(is_multitype=True)(
        '--books',
        resource_spec,
        'Group Help',
        prefixes=False,
        required=False,
        plural=True,
        flag_name_overrides={'project': '--book-project'}
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)
    self.parser.add_argument('--other', help='h')

    namespace = self.parser.parser.parse_args(['--other', 'xyz'])
    self.AssertParsedListEquals(
        ['projects/xyz/shelves/xyz/books/xyz'],
        namespace.CONCEPTS.books.Parse(),
        is_multitype=True)

  @parameterized.named_parameters(
      ('Full', False,
       ['projects/abc/shelves/abc/books/abc',
        'projects/def/shelves/def/books/def'], [],
       ['projects/abc/shelves/abc/books/abc',
        'projects/def/shelves/def/books/def']),
      ('Name', False,
       ['abc', 'def'], [],
       ['projects/xyz/shelves/xyz/books/abc',
        'projects/xyz/shelves/xyz/books/def']),
      ('MultitypeFull', True,
       ['projects/abc/shelves/abc/books/abc',
        'projects/def/shelves/def/books/def'], [],
       ['projects/abc/shelves/abc/books/abc',
        'projects/def/shelves/def/books/def']),
      ('MultitypeFullDiffCollections', True,
       ['projects/abc/shelves/abc/books/abc',
        'organizations/def/shelves/def/books/def'], [],
       ['projects/abc/shelves/abc/books/abc',
        'organizations/def/shelves/def/books/def'])
  )
  def testParsePluralAnchorFallthroughMultiple(
      self, is_multitype, fallthrough_value, args, expected):
    """Tests plural resource args parse when there's an anchor fallthrough."""
    spec = copy.deepcopy(
        self.SetUpFallthroughSpec(
            deps.Fallthrough(lambda: ['xyz'], hint='h'),
            is_multitype=is_multitype))
    fallthrough = deps.Fallthrough(lambda: fallthrough_value, hint='h',
                                   active=True)
    for attribute in spec.attributes:
      if attribute.name == 'book':
        attribute.fallthroughs = [fallthrough] + attribute.fallthroughs
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        '--books',
        spec,
        'Group Help',
        prefixes=False,
        plural=True,
        flag_name_overrides={'project': '--book-project'}
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args(args)
    self.AssertParsedListEquals(
        expected,
        namespace.CONCEPTS.books.Parse(),
        is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Overridden', 'examplebook', False,
       'projects/exampleproject/shelves/exampleshelf/books/examplebook'),
      ('NotOverridden', '', False,
       'projects/junk/shelves/junk/books/junk'),
      ('OverriddenPlural', 'examplebook,projects/p1/shelves/s1/books/b1', True,
       ['projects/exampleproject/shelves/exampleshelf/books/examplebook',
        'projects/p1/shelves/s1/books/b1']),
      ('NotOverriddenPlural', '', True,
       ['projects/junk/shelves/junk/books/junk']))
  def testParseFullySpecifiedAnchorFallthrough(self, book_arg, plural,
                                               expected_value):
    """Only get values from a parsed anchor if that anchor is being used."""
    fallthroughs = [
        deps.Fallthrough(
            lambda: 'projects/junk/shelves/junk/books/junk', hint='h')]
    spec = copy.deepcopy(self.resource_spec)
    spec.attributes[-1].fallthroughs = fallthroughs
    # These should be used as fallthroughs unless the anchor fallthrough comes
    # from the fully specified fallthrough.
    spec.attributes[0].fallthroughs = [
        deps.Fallthrough(lambda: 'exampleproject', hint='h')]
    spec.attributes[1].fallthroughs = [
        deps.Fallthrough(lambda: 'exampleshelf', hint='h')]
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        spec,
        'The book to act upon.',
        plural=plural)
    concept_parser.AddToParser(self.parser)

    parsed_args = self.parser.parser.parse_args(['--book', book_arg])

    if plural:
      result = [book.RelativeName()
                for book in parsed_args.CONCEPTS.book.Parse()]
    else:
      result = parsed_args.CONCEPTS.book.Parse().RelativeName()
    self.assertEqual(expected_value, result)

  @parameterized.named_parameters(
      ('', False),
      ('Multitype', True))
  def testResourceArgParsedInGroup(self, is_multitype):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    resource_spec = (
        self.resource_spec if not is_multitype else self.two_way_resource)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        'book',
        resource_spec,
        'The book to act upon.',
        group=group,
        prefixes=False,
        flag_name_overrides={'project': '--book-project'})
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)
    namespace = self.parser.parser.parse_args(
        ['example', '--shelf', 'exampleshelf', '--book-project',
         'example-project'])
    self.AssertParsedResultEquals(
        'projects/example-project/shelves/exampleshelf/books/example',
        namespace.CONCEPTS.book.Parse(),
        is_multitype=is_multitype)

  def testConceptParserForResourceAndCommandFallthroughs(self):
    """Tests that command level fallthroughs are prioritized over others."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        command_level_fallthroughs={'project': ['--other-project']})
    concept_parser.AddToParser(self.parser)
    self.parser.add_argument('--other-project', help='h')

    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook',
         '--shelf', 'exampleshelf',
         '--other-project', 'otherproject'])

    self.assertEqual(
        'projects/otherproject/shelves/exampleshelf/books/examplebook',
        parsed_args.CONCEPTS.book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('OF', False),
      ('Multitype', True))
  def testCommandFallthroughs(self, is_multitype):
    """Tests that command level fallthroughs are prioritized over others."""
    resource_spec = (
        self.resource_spec if not is_multitype else self.two_way_resource)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        '--book',
        resource_spec,
        'The book to act upon.')
    concept_parsers.ConceptParser(
        [resource],
        command_level_fallthroughs={'--book.project': ['--other-project']}
    ).AddToParser(self.parser)
    self.parser.add_argument('--other-project', help='h')

    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook',
         '--shelf', 'exampleshelf',
         '--other-project', 'otherproject'])

    self.AssertParsedResultEquals(
        'projects/otherproject/shelves/exampleshelf/books/examplebook',
        parsed_args.CONCEPTS.book.Parse(),
        is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('OF', False),
      ('Multitype', True))
  def testCommandFallthroughsNotUsed(self, is_multitype):
    """Tests that command level fallthroughs are prioritized over others."""
    resource_spec = (
        self.resource_spec if not is_multitype else self.two_way_resource)
    resource = self.PresentationSpecType(is_multitype=is_multitype)(
        '--book',
        resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    concept_parsers.ConceptParser(
        [resource],
        command_level_fallthroughs={'--book.project': ['--other-project']}
    ).AddToParser(self.parser)
    self.parser.add_argument('--other-project', help='h')

    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook',
         '--shelf', 'exampleshelf',
         '--book-project', 'exampleproject',
         '--other-project', 'otherproject'])

    self.AssertParsedResultEquals(
        'projects/exampleproject/shelves/exampleshelf/books/examplebook',
        parsed_args.CONCEPTS.book.Parse(),
        is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('Used', False,
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample'],
       'shelves/exampleshelf/books/otherexample'),
      ('NotUsed', False,
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample', '--other-book-shelf', 'othershelf'],
       'shelves/othershelf/books/otherexample'),
      ('MultitypeUsed', True,
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample'],
       'shelves/exampleshelf/books/otherexample'),
      ('MultitypeNotUsed', True,
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample', '--other-book-shelf', 'othershelf'],
       'shelves/othershelf/books/otherexample'))
  def testCommandFallthroughsOtherResource(
      self, is_multitype, args_to_parse, expected):
    """Tests that command level fallthroughs are prioritized over others."""
    resource_spec = (
        self.two_way_shelf_case_book if is_multitype else self.resource_spec)
    concept_parser = concept_parsers.ConceptParser(
        [self.PresentationSpecType(is_multitype=is_multitype)(
            '--book',
            resource_spec,
            'The book to act upon.'),
         self.PresentationSpecType(is_multitype=is_multitype)(
             '--other-book',
             resource_spec,
             'The other book',
             prefixes=True)],
        command_level_fallthroughs={'--other-book.shelf': ['--book.shelf']})
    concept_parser.AddToParser(self.parser)

    parsed_args = self.parser.parser.parse_args(args_to_parse)

    self.AssertParsedResultEquals(
        'projects/{}/shelves/exampleshelf/books/examplebook'.format(
            self.Project()),
        parsed_args.CONCEPTS.book.Parse(),
        is_multitype=is_multitype)
    self.AssertParsedResultEquals(
        'projects/{}/{}'.format(self.Project(), expected),
        parsed_args.CONCEPTS.other_book.Parse(),
        is_multitype=is_multitype)

  @parameterized.named_parameters(
      ('FormattingOfValue', False, {'--other-book.shelf': ['--book.x.y']},
       'invalid fallthrough value: [--book.x.y]. Must be in the form BAR.b or '
       '--baz'),
      ('FormattingOfKey', False, {'shelf': ['--book.shelf']},
       'invalid fallthrough key: [shelf]. Must be in format "FOO.a" where FOO '
       'is the presentation spec name and a is the attribute name.'),
      ('KeySpecNotFound', False, {'FOO.shelf': ['--book.shelf']},
       'invalid fallthrough key: [FOO.shelf]. Spec name is not present in the '
       'presentation specs. Available names: [--book, --other-book]'),
      ('KeyAttributeNotFound', False, {'--other-book.case': ['--book.shelf']},
       'invalid fallthrough key: [--other-book.case]. spec named '
       '[--other-book] has no attribute named [case]'),
      ('ValueSpecNotFound', False, {'--other-book.shelf': ['FOO.shelf']},
       'invalid fallthrough value: [FOO.shelf]. Spec name is not present in '
       'the presentation specs. Available names: [--book, --other-book]'),
      ('ValueAttributeNotFound', False,
       {'--other-book.shelf': ['--book.case']},
       'invalid fallthrough value: [--book.case]. spec named [--book] '
       'has no attribute named [case]'),
      ('MultitypeAttributeNotFound', True,
       {'--other-book.shelf': ['--book.junk']},
       'invalid fallthrough value: [--book.junk]. spec named [--book] '
       'has no attribute named [junk]'))
  def testCommandFallthroughInvalid(self, is_multitype, fallthroughs, expected):
    resource_spec = (
        self.two_way_shelf_case_book if is_multitype else self.resource_spec)
    with self.assertRaisesRegexp(ValueError,
                                 re.escape(expected)):
      concept_parsers.ConceptParser(
          [self.PresentationSpecType(is_multitype=is_multitype)(
              '--book',
              resource_spec,
              'The book to act upon.'),
           self.PresentationSpecType(is_multitype=is_multitype)(
               '--other-book',
               resource_spec,
               'The other book',
               prefixes=True)],
          command_level_fallthroughs=fallthroughs)

  def testCommandFallthroughMultitypeError(self):
    """If a conflicting arg fallthrough is given, error out."""
    resource_spec = self.two_way_shelf_case_book
    concept_parsers.ConceptParser(
        [presentation_specs.MultitypeResourcePresentationSpec(
            '--book',
            resource_spec,
            'The book to act upon.'),
         presentation_specs.MultitypeResourcePresentationSpec(
             '--other-book',
             resource_spec,
             'The other book',
             prefixes=True)],
        command_level_fallthroughs={'--other-book.shelf': ['--book.shelf']}
    ).AddToParser(self.parser)
    namespace = self.parser.parser.parse_args(
        ['--book', 'b1', '--shelf', 's1', '--other-book', 'b1',
         '--other-book-case', 'c1'])
    with self.assertRaisesRegex(multitype.ConflictingTypesError,
                                re.escape('[shelf, book, case]')):
      namespace.CONCEPTS.other_book.Parse()

  def testCommandFallthroughsArgNotFound(self):
    specs = [
        presentation_specs.ResourcePresentationSpec(
            '--book',
            self.resource_spec,
            'The book to act upon.'),
        presentation_specs.ResourcePresentationSpec(
            '--other-book',
            self.resource_spec,
            'The other book',
            prefixes=True)]
    concept_parser = concept_parsers.ConceptParser(
        specs,
        command_level_fallthroughs={
            '--other-book.project': ['--book.project']})
    message = (
        'Invalid fallthrough value [--book.project]: No argument associated '
        'with attribute [project] in concept argument named [--book]')
    with self.assertRaisesRegexp(ValueError, re.escape(message)):
      concept_parser.GetInfo(specs[1].name)


if __name__ == '__main__':
  test_case.main()
