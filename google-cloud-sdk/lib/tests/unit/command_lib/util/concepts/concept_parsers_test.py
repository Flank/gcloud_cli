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

import re

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util as concepts_util
import mock


class ConceptParsersTest(concepts_test_base.ConceptsTestBase,
                         parameterized.TestCase):
  """Test for concept_parsers module."""

  def testResourceArgNames(self):
    """Test a resource spec with prefixes=False."""

    resource = concept_parsers.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=False)

    args = [arg.name for arg in resource.GetAttributeArgs()]

    self.assertEqual(['--shelf', '--book'], args)

  def testResourceArgNamesWithPrefixes(self):
    """Test a resource spec with prefixes=True."""
    resource = concept_parsers.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)

    args = [arg.name for arg in resource.GetAttributeArgs()]

    self.assertEqual(['--book-shelf', '--book'], args)

  def testResourceArgNamesWithOverrides(self):
    """Test a resource spec with flag name overrides."""
    resource = concept_parsers.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--project-flag',
                             'shelf': '--book-shelf'},
        prefixes=False)

    args = [arg.name for arg in resource.GetAttributeArgs()]

    self.assertEqual(['--project-flag', '--book-shelf', '--book'], args)

  @parameterized.named_parameters(
      ('Nonrequired', '--book', False, None),
      ('Required', '--book', True, None),
      ('NonrequiredPositional', 'book', False, '?'),
      ('RequiredPositional', 'book', True, '?'))
  def testResourceArgAnchorFallthrough(self, name, rsrc_required,
                                       expected_nargs):
    """Tests anchor args not required when there's another fallthrough."""
    resource = concept_parsers.ResourcePresentationSpec(
        name,
        self.SetUpFallthroughSpec('!'),
        'Group Help',
        prefixes=False,
        required=rsrc_required
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    self.assertEqual(
        expected_nargs,
        resource.GetAttributeArgs()[-1].kwargs.get('nargs', None))
    self.assertIsNone(
        resource.GetAttributeArgs()[-1].kwargs.get('required', None))
    namespace = self.parser.parser.parse_args([])
    self.assertEqual('projects/!/shelves/!/books/!',
                     namespace.CONCEPTS.book.Parse().RelativeName())

  @parameterized.named_parameters(
      ('Nonrequired', '--books', False, None),
      ('Required', '--books', True, None),
      ('NonrequiredPositional', 'books', False, '*'),
      ('RequiredPositional', 'books', True, '*'))
  def testResourceArgAnchorPluralFallthrough(self, name, rsrc_required,
                                             expected_nargs):
    """Tests plural args not required when there's another fallthrough."""
    resource = concept_parsers.ResourcePresentationSpec(
        name,
        self.SetUpFallthroughSpec(['!']),
        'Group Help',
        prefixes=False,
        required=rsrc_required,
        plural=True
    )
    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)

    self.assertEqual(
        expected_nargs,
        resource.GetAttributeArgs()[-1].kwargs.get('nargs', None))
    self.assertIsNone(
        resource.GetAttributeArgs()[-1].kwargs.get('required', None))
    namespace = self.parser.parser.parse_args([])
    self.assertEqual(
        ['projects/!/shelves/!/books/!'],
        [b.RelativeName() for b in namespace.CONCEPTS.books.Parse()])

  @parameterized.named_parameters(
      ('NotRequired', 'BOOKS', False),
      ('Required', 'BOOKS', True))
  def testResourceArgArgsPositionalWithPlural(self, name, required):
    """Tests that presentation spec correctly creates plural positional args."""
    resource = concept_parsers.ResourcePresentationSpec(
        name,
        self.resource_spec,
        'The book to act upon.',
        required=required,
        plural=True)

    expected = {
        'help': ('The ID of the book or a fully qualified identifier for the '
                 'book.'),
        'completer': None,
        'nargs': '+',
        'type': str}
    name = 'BOOKS'
    self.assertEqual(expected, resource.GetAttributeArgs()[-1].kwargs)
    self.assertEqual(name, resource.GetAttributeArgs()[-1].name)

  @parameterized.named_parameters(
      ('NotRequired', '--books', False),
      ('Required', '--books', True)
      )
  def testResourceArgArgsFlagWithPlural(self, name, required):
    """Tests that presentation spec correctly creates plural flag args."""
    resource = concept_parsers.ResourcePresentationSpec(
        name,
        self.resource_spec,
        'The book to act upon.',
        required=required,
        plural=True)
    args = resource.GetAttributeArgs()
    actual_type = args[-1].kwargs.pop('type')
    self.assertIsInstance(actual_type, arg_parsers.ArgList)
    expected = {
        'help': ('The ID of the book or a fully qualified identifier for the '
                 'book.'),
        'completer': None,
        'metavar': 'BOOKS',
        'required': True}
    self.assertEqual(expected, args[-1].kwargs)

  def testSingleParameter(self):
    """Test a resource with only 1 parameter that doesn't get generated."""
    resource = concept_parsers.ResourcePresentationSpec(
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

    # No args should be generated.
    args = [arg.name for arg in resource.GetAttributeArgs()]
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
    resource = concept_parsers.ResourcePresentationSpec(
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

    args = [arg.name for arg in resource.GetAttributeArgs()]
    self.assertEqual(['--shelf', 'book'], args)

    concept_parser = concept_parsers.ConceptParser([resource])
    concept_parser.AddToParser(self.parser)
    properties.VALUES.core.project.Set('foo')
    namespace = self.parser.parser.parse_args([])
    self.assertEqual('projects/foo/shelves/!/books/!',
                     namespace.CONCEPTS.book.Parse().RelativeName())

  def testConceptParserCreatesRuntimeHandler(self):
    """Tests that a runtime handler is created and concept is registered."""
    concept_parser = concept_parsers.ConceptParser(
        [concept_parsers.ResourcePresentationSpec(
            '--book',
            self.resource_spec,
            'The book to act upon.')])

    concept_parser.AddToParser(self.parser)

    self.assertTrue(hasattr(concept_parser._runtime_handler, 'book'))

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

  def testTwoResourcesInRuntimeHandler(self):
    """Tests that a runtime handler has two concepts registered."""
    resource = concept_parsers.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = concept_parsers.ResourcePresentationSpec(
        '--other-book',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=True)

    concept_parser = concept_parsers.ConceptParser([resource, other_resource])
    concept_parser.AddToParser(self.parser)

    self.assertTrue(hasattr(concept_parser._runtime_handler, 'book'))
    self.assertTrue(hasattr(concept_parser._runtime_handler, 'other_book'))

  def testTwoResourceArgs(self):
    """Test a concept parser with two resource args."""
    resource = concept_parsers.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = concept_parsers.ResourcePresentationSpec(
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

  def testResourceArgAddedToGroups(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    group_obj = mock.MagicMock()
    group_add_group = self.StartObjectPatch(group, 'add_group',
                                            return_value=group_obj)
    resource = concept_parsers.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = concept_parsers.ResourcePresentationSpec(
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

  def testResourceArgParsedInGroup(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group')
    resource = concept_parsers.ResourcePresentationSpec(
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

  def testResourceArgsInMutexGroup(self):
    """Test a concept parser with two resource args."""
    group = self.parser.add_group('A group', mutex=True)
    resource = concept_parsers.ResourcePresentationSpec(
        'book',
        self.resource_spec,
        'The book to act upon.',
        group=group,
        prefixes=True)
    other_resource = concept_parsers.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        group=group,
        prefixes=True)
    concept_parsers.ConceptParser([resource, other_resource]).AddToParser(
        self.parser)
    with self.AssertRaisesArgumentErrorMatches('At most one of'):
      self.parser.parser.parse_args(['example', '--other', 'otherexample'])

  def testTwoResourceArgsPositionals(self):
    """Test a concept parser with two positional resource args raises error."""
    resource = concept_parsers.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=True)
    other_resource = concept_parsers.ResourcePresentationSpec(
        'OTHER',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=True)
    with self.assertRaisesRegexp(ValueError, re.escape('[BOOK, OTHER]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testTwoResourceArgsConflict(self):
    """Test concept parser raises an error when resource arg names conflict."""
    resource = concept_parsers.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.')
    other_resource = concept_parsers.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The second book to act upon.')
    with self.assertRaisesRegexp(ValueError, re.escape('[BOOK, --book]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testTwoResourceArgsConflictingFlags(self):
    """Test concept parser raises an error when resource arg names conflict."""
    resource = concept_parsers.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=False)
    other_resource = concept_parsers.ResourcePresentationSpec(
        '--other',
        self.resource_spec,
        'The second book to act upon.',
        prefixes=False)
    with self.assertRaisesRegexp(ValueError, re.escape('[--shelf]')):
      concept_parsers.ConceptParser([resource, other_resource])

  def testPresentationSpecConceptInfo(self):
    """Tests that presentation spec correctly initializes a ConceptInfo."""
    resource = concept_parsers.ResourcePresentationSpec(
        'BOOK',
        self.resource_spec,
        'The book to act upon.',
        prefixes=False)
    concept_info = resource.GetInfo()

    self.assertEqual(self.resource_spec.name, concept_info.concept_spec.name)
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

  @parameterized.named_parameters(
      ('Positional', 'book', False, False, True, False),
      ('Flag', '--book', False, False, True, False),
      ('PositionalWithFallthroughs', 'book', False, True, True, False),
      ('FlagWithFallthroughs', '--book', False, True, True, False),
      ('PositionalRequired', 'book', True, False, False, True),
      ('FlagRequired', '--book', True, False, False, True),
      ('PositionalWithFallthroughsRequired', 'book', True, True, False, False),
      ('FlagWithFallthroughsRequired', '--book', True, True, False, False))
  def testPresentationSpecConceptInfoAllowEmpty(self, name, required,
                                                with_fallthroughs,
                                                expected_allow_empty,
                                                expected_args_required):
    """Tests that presentation spec correctly initializes a ConceptInfo."""
    if with_fallthroughs:
      spec = self.SetUpFallthroughSpec('!')
    else:
      spec = self.resource_spec
    resource = concept_parsers.ResourcePresentationSpec(
        name,
        spec,
        'The book to act upon.',
        prefixes=False,
        required=required)
    concept_info = resource.GetInfo()

    self.assertEqual(
        expected_allow_empty,
        concept_info.allow_empty)
    self.assertEqual(
        expected_args_required,
        resource.args_required)

  def testConceptParserAddsCompleter(self):
    """Tests that the concept parser adds completers to attribute args."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec_completers,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    completers = [
        arg.kwargs.get('completer', None)
        for arg in concept_parser._specs['--book'].GetAttributeArgs()]
    self.assertEqual([concepts_util.MockProjectCompleter,
                      concepts_util.MockShelfCompleter,
                      concepts_util.MockBookCompleter],
                     completers)

  def testConceptParserExpandsHelpText(self):
    """Tests that the concept parser expands {resource} in help text."""
    concept_parser = concept_parsers.ConceptParser.ForResource(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    help_text = [
        arg.kwargs.get('help', None)
        for arg in concept_parser._specs['--book'].GetAttributeArgs()]
    self.assertEqual(['The Cloud Project of the book.',
                      'The shelf of the book. Shelves hold books.',
                      'The ID of the book or a fully qualified identifier for '
                      'the book.'],
                     help_text)

  def testSingleArgUsesGroupHelp(self):
    """Tests that concept parser uses group help for single argument in a group.
    """
    resource_spec = concept_parsers.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'shelf': ''})

    help_text = [
        arg.kwargs.get('help', None)
        for arg in resource_spec.GetAttributeArgs()]

    self.assertEqual(['The book to act upon.'], help_text)

  def testGroupHelp(self):
    """Tests that the presentation spec generates group help correctly."""
    presentation_spec = concept_parsers.ResourcePresentationSpec(
        '--a-book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'})
    expected = ('A BOOK - The book to act upon. The arguments in this group '
                'can be used to specify the attributes of this resource.')
    self.assertEqual(expected, presentation_spec.GetGroupHelp())

  def testGroupHelpSkippedFlag(self):
    """Tests presentation spec generates group help when some flags are skipped.
    """
    presentation_spec = concept_parsers.ResourcePresentationSpec(
        '--a-book',
        self.resource_spec,
        'The book to act upon.')
    expected = ('A BOOK - The book to act upon. The arguments in this group '
                'can be used to specify the attributes of this resource. '
                '(NOTE) Some attributes are not given arguments in this group '
                'but can be set in other ways. To set the [project] attribute: '
                'Set the property [core/project] or provide the flag '
                '[--project] on the command line.')
    self.assertEqual(expected, presentation_spec.GetGroupHelp())

  def testGetExampleArgListFlag(self):
    """Tests that the presentation spec generates example args correctly."""
    presentation_spec = concept_parsers.ResourcePresentationSpec(
        '--a-book',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'},
        prefixes=True)
    expected = [
        '--book-project=my-book-project',
        '--a-book-shelf=my-a-book-shelf',
        '--a-book=my-a-book',
    ]
    self.assertEqual(expected, presentation_spec.GetExampleArgList())

  def testGetExampleArgListPositional(self):
    """Tests that the presentation spec generates example args correctly."""
    presentation_spec = concept_parsers.ResourcePresentationSpec(
        'a-BOOK',
        self.resource_spec,
        'The book to act upon.',
        flag_name_overrides={'project': '--book-project'},
        prefixes=True)
    expected = [
        '--book-project=my-book-project',
        '--a-book-shelf=my-a-book-shelf',
        'my-a-book',
    ]
    self.assertEqual(expected, presentation_spec.GetExampleArgList())


if __name__ == '__main__':
  test_case.main()
