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

"""Tests for the concepts.concept_parsers module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import re

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
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

    self.assertTrue(hasattr(concept_parser._runtime_handler, 'book'))

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

    self.assertTrue(hasattr(concept_parser._runtime_handler, 'book'))
    self.assertTrue(hasattr(concept_parser._runtime_handler, 'other_book'))

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


class ParsingTests(concepts_test_base.ConceptsTestBase,
                   parameterized.TestCase):
  """Tests of the entire parsing mechanism."""

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

  def testTwoResourceArgs(self):
    """Test a concept parser with two resource args."""
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = presentation_specs.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=True)
    concept_parser = concept_parsers.ConceptParser([resource, other_resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args([
        'example',
        '--book-shelf', 'exampleshelf',
        '--other', 'otherbook',
        '--other-shelf', 'othershelf'])
    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/example'.format(self.Project()),
        namespace.CONCEPTS.book.Parse().RelativeName())
    self.assertEqual(
        'projects/{}/shelves/othershelf/books/otherbook'.format(self.Project()),
        namespace.CONCEPTS.other.Parse().RelativeName())

  @parameterized.named_parameters(
      ('Nonrequired', '--book', False),
      ('Required', '--book', True),
      ('NonrequiredPositional', 'book', False),
      ('RequiredPositional', 'book', True))
  def testParseAnchorFallthrough(self, name, rsrc_required):
    """Tests resource can be parsed when there are fallthroughs for anchor."""
    resource = presentation_specs.ResourcePresentationSpec(
        name,
        self.SetUpFallthroughSpec('!'),
        'Group Help',
        prefixes=False,
        required=rsrc_required
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args([])
    self.assertEqual('projects/!/shelves/!/books/!',
                     namespace.CONCEPTS.book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('Nonrequired', '--books', False),
      ('Required', '--books', True),
      ('NonrequiredPositional', 'books', False),
      ('RequiredPositional', 'books', True))
  def testParsePluralAnchorFallthrough(self, name, rsrc_required):
    """Tests plural resource args parse when there's an anchor fallthorugh."""
    resource = presentation_specs.ResourcePresentationSpec(
        name,
        self.SetUpFallthroughSpec(['!']),
        'Group Help',
        prefixes=False,
        required=rsrc_required,
        plural=True
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    namespace = self.parser.parser.parse_args([])
    self.assertEqual(
        ['projects/!/shelves/!/books/!'],
        [b.RelativeName() for b in namespace.CONCEPTS.books.Parse()])

  def testResourceArgParsedInGroup(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    resource = presentation_specs.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        group=group,
        prefixes=False,
        flag_name_overrides={'project': '--book-project'})
    concept_parsers.ConceptParser([resource]).AddToParser(self.parser)
    namespace = self.parser.parser.parse_args(
        ['example', '--shelf', 'exampleshelf', '--book-project',
         'example-project'])
    self.assertEqual(
        'projects/example-project/shelves/exampleshelf/books/example',
        namespace.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserAndCommandFallthroughs(self):
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

  def testConceptParserAndCommandFallthroughsNotUsed(self):
    """Tests that primary arguments are favored over command level fallthroughs.
    """
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'},
        command_level_fallthroughs={'project': ['--other-project']})
    concept_parser.AddToParser(self.parser)
    self.parser.add_argument('--other-project', help='h')

    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook',
         '--shelf', 'exampleshelf',
         '--book-project', 'exampleproject',
         '--other-project', 'otherproject'])

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/examplebook',
        parsed_args.CONCEPTS.book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('Used',
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample'],
       'shelves/exampleshelf/books/otherexample'),
      ('NotUsed',
       ['--book', 'examplebook', '--shelf', 'exampleshelf', '--other-book',
        'otherexample', '--other-book-shelf', 'othershelf'],
       'shelves/othershelf/books/otherexample'))
  def testConceptParserAndCommandFallthroughsOtherResource(
      self, args_to_parse, expected_name):
    """Tests that command level fallthroughs are prioritized over others."""
    concept_parser = concept_parsers.ConceptParser(
        [presentation_specs.ResourcePresentationSpec(
            '--book',
            self.resource_spec,
            'The book to act upon.'),
         presentation_specs.ResourcePresentationSpec(
             '--other-book',
             self.resource_spec,
             'The other book',
             prefixes=True)],
        command_level_fallthroughs={'--other-book.shelf': ['--book.shelf']})
    concept_parser.AddToParser(self.parser)

    parsed_args = self.parser.parser.parse_args(args_to_parse)

    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/examplebook'.format(
            self.Project()),
        parsed_args.CONCEPTS.book.Parse().RelativeName())
    self.assertEqual(
        'projects/{}/{}'.format(self.Project(), expected_name),
        parsed_args.CONCEPTS.other_book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('FormattingOfValue', {'--other-book.shelf': ['--book.x.y']},
       'invalid fallthrough value: [--book.x.y]. Must be in the form BAR.b or '
       '--baz'),
      ('FormattingOfKey', {'shelf': ['--book.shelf']},
       'invalid fallthrough key: [shelf]. Must be in format "FOO.a" where FOO '
       'is the presentation spec name and a is the attribute name.'),
      ('KeySpecNotFound', {'FOO.shelf': ['--book.shelf']},
       'invalid fallthrough key: [FOO.shelf]. Spec name is not present in the '
       'presentation specs. Available names: [--book, --other-book]'),
      ('KeyAttributeNotFound', {'--other-book.case': ['--book.shelf']},
       'invalid fallthrough key: [--other-book.case]. spec named '
       '[--other-book] has no attribute named [case]'),
      ('ValueSpecNotFound', {'--other-book.shelf': ['FOO.shelf']},
       'invalid fallthrough value: [FOO.shelf]. Spec name is not present in '
       'the presentation specs. Available names: [--book, --other-book]'),
      ('ValueAttributeNotFound', {'--other-book.shelf': ['--book.case']},
       'invalid fallthrough value: [--book.case]. spec named [--book] '
       'has no attribute named [case]'))
  def testConceptParserAndCommandFallthroughInvalid(self, fallthroughs,
                                                    expected):
    with self.assertRaisesRegexp(ValueError,
                                 re.escape(expected)):
      concept_parsers.ConceptParser(
          [presentation_specs.ResourcePresentationSpec(
              '--book',
              self.resource_spec,
              'The book to act upon.'),
           presentation_specs.ResourcePresentationSpec(
               '--other-book',
               self.resource_spec,
               'The other book',
               prefixes=True)],
          command_level_fallthroughs=fallthroughs)

  def testConceptParserAndCommandFallthroughsArgNotFound(self):
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
