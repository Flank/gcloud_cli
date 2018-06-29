# Copyright 2018 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import info_holders
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util as concepts_util

import six


class InfoHoldersTests(concepts_test_base.ConceptsTestBase,
                       parameterized.TestCase):
  """Test for info_holders module."""

  def SetUp(self):
    def Fallthrough():
      return '!'
    self.fallthrough = deps.Fallthrough(Fallthrough, hint='hint')

  @parameterized.named_parameters(
      ('Positional', 'book', False, False, True, False),
      ('Flag', '--book', False, False, True, False),
      ('PositionalWithFallthroughs', 'book', False, True, True, False),
      ('FlagWithFallthroughs', '--book', False, True, True, False),
      ('PositionalRequired', 'book', True, False, False, True),
      ('FlagRequired', '--book', True, False, False, True),
      ('PositionalWithFallthroughsRequired', 'book', True, True, False, False),
      ('FlagWithFallthroughsRequired', '--book', True, True, False, False))
  def testResourceInfoAllowEmpty(self, name, required, with_fallthroughs,
                                 expected_allow_empty, expected_args_required):
    """Tests that presentation spec correctly initializes a ConceptInfo."""
    if with_fallthroughs:
      fallthroughs_map = {'book': [self.fallthrough],
                          'shelf': [self.fallthrough],
                          'project': [self.fallthrough]}
    else:
      fallthroughs_map = {}
    info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'The book to act upon.',
        {'book': name, 'shelf': '--shelf'},
        fallthroughs_map,
        required=required)

    self.assertEqual(
        expected_allow_empty,
        info.allow_empty)
    self.assertEqual(
        expected_args_required,
        info.args_required)

  @parameterized.named_parameters(
      ('Nonrequired', '--book', False, None),
      ('Required', '--book', True, None),
      ('NonrequiredPositional', 'book', False, '?'),
      ('RequiredPositional', 'book', True, '?'))
  def testResourceInfoAnchorFallthrough(self, name, rsrc_required,
                                        expected_nargs):
    """Tests anchor args not required when there's another fallthrough."""
    fallthroughs_map = {'book': [self.fallthrough],
                        'shelf': [self.fallthrough],
                        'project': [self.fallthrough]}
    info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'The book to act upon.',
        {'book': name, 'shelf': '--shelf'},
        fallthroughs_map,
        required=rsrc_required)

    self.assertEqual(
        expected_nargs,
        info.GetAttributeArgs()[-1].kwargs.get('nargs', None))
    self.assertIsNone(
        info.GetAttributeArgs()[-1].kwargs.get('required', None))

  @parameterized.named_parameters(
      ('Nonrequired', '--books', False, None),
      ('Required', '--books', True, None),
      ('NonrequiredPositional', 'books', False, '*'),
      ('RequiredPositional', 'books', True, '*'))
  def testResourceInfoAnchorPluralFallthrough(self, name, rsrc_required,
                                              expected_nargs):
    """Tests plural args not required when there's another fallthrough."""
    fallthroughs_map = {'book': [self.fallthrough],
                        'shelf': [self.fallthrough],
                        'project': [self.fallthrough]}
    info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'The book to act upon.',
        {'book': name, 'shelf': '--shelf'},
        fallthroughs_map,
        plural=True,
        required=rsrc_required)

    self.assertEqual(
        expected_nargs,
        info.GetAttributeArgs()[-1].kwargs.get('nargs', None))
    self.assertIsNone(
        info.GetAttributeArgs()[-1].kwargs.get('required', None))

  @parameterized.named_parameters(
      ('Required', True, False, False),
      ('NotRequired', False, True, False))
  def testResourceInfoAllFallthroughs(self, required,
                                      expected_allow_empty,
                                      expected_args_required):
    """Tests args_required is False if there is a fallthrough."""
    fallthroughs_map = {'shelf': [self.fallthrough], 'book': [self.fallthrough],
                        'project': [self.fallthrough]}
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf'},
        fallthroughs_map,
        plural=True,
        required=required)

    self.assertEqual(
        expected_allow_empty,
        info.allow_empty)
    self.assertEqual(
        expected_args_required,
        info.args_required)

  @parameterized.named_parameters(
      ('Required', True, False, True),
      ('NotRequired', False, True, False))
  def testResourceInfoSomeFallthroughs(self, required,
                                       expected_allow_empty,
                                       expected_args_required):
    """Tests args_required is True if 'book' has no fallthroughs."""
    fallthroughs_map = {'shelf': [self.fallthrough]}
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf'},
        fallthroughs_map,
        required=required)

    self.assertEqual(
        expected_allow_empty,
        info.allow_empty)
    self.assertEqual(
        expected_args_required,
        info.args_required)

  @parameterized.named_parameters(
      ('NotRequired', False, {'book': '--books', 'shelf': '--shelf'}),
      ('Required', True, {'book': '--books', 'shelf': '--shelf'}),
      ('NotRequiredSingleArg', False, {'book': '--books'}),
      ('RequiredSingleArg', True, {'book': '--books'}),
      )
  def testArgsFlagWithPlural(self, required, attribute_to_arg_names):
    """Tests that presentation spec correctly creates plural flag args."""
    info = info_holders.ResourceInfo(
        '--books',
        self.resource_spec,
        'The book to act upon.',
        attribute_to_arg_names,
        {},
        plural=True,
        required=required)

    args = info.GetAttributeArgs()
    actual_type = args[-1].kwargs.pop('type')
    self.assertIsInstance(actual_type, arg_parsers.ArgList)
    expected = {
        'help': ('IDs of the books or fully qualified identifiers for the '
                 'books.'),
        'completer': None,
        'metavar': 'BOOKS',
        # Anchor argument is always required within the group.
        'required': True}
    self.assertEqual(expected, args[-1].kwargs)

  @parameterized.named_parameters(
      ('NotRequired', False, {'book': 'BOOKS', 'shelf': '--shelf'}),
      ('Required', True, {'book': 'BOOKS', 'shelf': '--shelf'}),
      ('NotRequiredSingleArg', False, {'book': 'BOOKS'}),
      ('RequiredSingleArg', True, {'book': 'BOOKS'}))
  def testArgsPositionalWithPlural(self, required, attribute_to_arg_names):
    """Tests that presentation spec correctly creates plural positional args."""
    info = info_holders.ResourceInfo(
        'BOOKS',
        self.resource_spec,
        'The book to act upon.',
        attribute_to_arg_names,
        {},
        plural=True,
        required=required)

    expected = {
        'help': ('IDs of the books or fully qualified identifiers for the '
                 'books.'),
        'completer': None,
        # Anchor argument is always required within the group.
        'nargs': '+',
        'type': six.text_type}
    name = 'BOOKS'
    self.assertEqual(expected, info.GetAttributeArgs()[-1].kwargs)
    self.assertEqual(name, info.GetAttributeArgs()[-1].name)

  def testAddsCompleter(self):
    """Tests that the concept parser adds completers to attribute args."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec_completers,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})
    completers = [
        arg.kwargs.get('completer', None)
        for arg in info.GetAttributeArgs()]
    self.assertEqual([concepts_util.MockProjectCompleter,
                      concepts_util.MockShelfCompleter,
                      concepts_util.MockBookCompleter],
                     completers)

  def testExpandsHelpText(self):
    """Tests that the concept parser expands {resource} in help text."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec_completers,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})
    help_text = [
        arg.kwargs.get('help', None)
        for arg in info.GetAttributeArgs()]
    self.assertEqual(['The Cloud Project of the book.',
                      'The shelf of the book. Shelves hold books.',
                      'The ID of the book or a fully qualified identifier for '
                      'the book.'],
                     help_text)

  def testExpandsHelpTextPlural(self):
    """Tests that the concept parser expands {resource} in help text."""
    info = info_holders.ResourceInfo(
        '--books',
        self.resource_spec_completers,
        'The books to act upon.',
        {'book': '--books', 'shelf': '--shelf', 'project': '--book-project'},
        {},
        plural=True)
    help_text = [
        arg.kwargs.get('help', None)
        for arg in info.GetAttributeArgs()]
    self.assertEqual(
        ['The Cloud Project of the books.',
         'The shelf of the books. Shelves hold books.',
         'IDs of the books or fully qualified identifiers for the books.'],
        help_text  # Anchor help text.
    )

  def testExpandsHelpTextPluralCustom(self):
    """Tests that the concept parser expands {resource} in help text."""
    spec = concepts_util.GetBookResource()
    spec.plural_name = 'boooooks'
    info = info_holders.ResourceInfo(
        '--book',
        spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {},
        plural=True)
    help_text = [
        arg.kwargs.get('help', None)
        for arg in info.GetAttributeArgs()]
    self.assertEqual(['The Cloud Project of the boooooks.',
                      'The shelf of the boooooks. Shelves hold books.',
                      'IDs of the boooooks or fully qualified identifiers for '
                      'the boooooks.'],
                     help_text)

  @parameterized.named_parameters(
      ('Lowercase', 'book', 'Book'),
      ('Uppercase', 'BOOK', 'BOOK'),
      ('Multiword', 'project_book', 'Project book'))
  def testTitle(self, resource_name, expected_title):
    """Tests that the presentation spec generates the title correctly."""
    resource_spec = concepts_util.GetBookResource(name=resource_name)
    info = info_holders.ResourceInfo(
        '--book',
        resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})
    self.assertEqual(expected_title, info.title)

  def testGroupHelp(self):
    """Tests that the presentation spec generates group help correctly."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})
    expected = ('Book resource - The book to act upon. The arguments in this '
                'group can be used to specify the attributes of this resource.')
    self.assertEqual(expected, info.GetGroupHelp())

  def testGroupHelpSkippedFlags(self):
    """Tests presentation spec group help when flags are skipped."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf'},
        {'project': [deps.ArgFallthrough('--project'),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]})
    expected = ('Book resource - The book to act upon. The arguments in this '
                'group can be used to specify the attributes of this resource. '
                '(NOTE) Some attributes are not given arguments in this group '
                'but can be set in other ways. To set the [project] attribute: '
                'provide the flag [--book] on the command line with a fully '
                'specified name; provide the flag [--project] on the command '
                'line; set the property [core/project].')
    self.assertEqual(expected, info.GetGroupHelp())

  def testGroupHelpSkippedFlagsOtherFlagFallthrough(self):
    """Tests presentation spec group help when flags are skipped."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf'},
        {'project': [
            deps.ArgFallthrough('--other-project'),
            deps.ArgFallthrough('--project'),
            deps.PropertyFallthrough(properties.VALUES.core.project)]})
    expected = ('Book resource - The book to act upon. The arguments in this '
                'group can be used to specify the attributes of this resource. '
                '(NOTE) Some attributes are not given arguments in this group '
                'but can be set in other ways. To set the [project] attribute: '
                'provide the flag [--book] on the command line with a fully '
                'specified name; provide the flag [--other-project] on the '
                'command line; provide the flag [--project] on the '
                'command line; set the property [core/project].')
    self.assertEqual(expected, info.GetGroupHelp())

  def testGroupHelpSingleArg(self):
    """Tests presentation spec group help when flags are skipped."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book'},
        {'project': [deps.ArgFallthrough('--project'),
                     deps.PropertyFallthrough(properties.VALUES.core.project)]})
    expected = ('Book resource - The book to act upon. This represents a Cloud '
                'resource. (NOTE) Some attributes are not given arguments in '
                'this group but can be set in other ways. To set the [project] '
                'attribute: provide the flag [--book] on the command line with '
                'a fully specified name; provide the flag [--project] on the '
                'command line; set the property [core/project]. To set the '
                '[shelf] attribute: provide the flag [--book] on the command '
                'line with a fully specified name.')
    self.assertEqual(expected, info.GetGroupHelp())

  def testGetExampleArgListFlag(self):
    """Tests that the presentation spec generates example args correctly."""
    info = info_holders.ResourceInfo(
        '--a-book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--a-book', 'shelf': '--a-book-shelf',
         'project': '--book-project'},
        {})
    expected = [
        '--book-project=my-book-project',
        '--a-book-shelf=my-a-book-shelf',
        '--a-book=my-a-book',
    ]
    self.assertEqual(expected, info.GetExampleArgList())

  def testGetExampleArgListPositional(self):
    """Tests that the presentation spec generates example args correctly."""
    info = info_holders.ResourceInfo(
        'A-BOOK',
        self.resource_spec,
        'The book to act upon.',
        {'book': 'A-BOOK', 'shelf': '--a-book-shelf',
         'project': '--book-project'},
        {})
    expected = [
        '--book-project=my-book-project',
        '--a-book-shelf=my-a-book-shelf',
        'my-a-book',
    ]
    self.assertEqual(expected, info.GetExampleArgList())

  def testBuildFullFallthroughsMap(self):
    """Tests fallthroughs map adds anchor fallthroughs."""
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})

    result = info.BuildFullFallthroughsMap()

    expected = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                deps.ArgFallthrough('--book'),
                self.resource_spec.collection_info,
                'projectsId'),
            deps.ArgFallthrough('--book-project')],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                deps.ArgFallthrough('--book'),
                self.resource_spec.collection_info,
                'shelvesId'),
            deps.ArgFallthrough('--shelf')
        ],
        'book': [
            deps.ArgFallthrough('--book')]}
    self.assertEqual(expected, result)

  def testBuildFullFallthroughsMapEmptyFallthroughs(self):
    """Tests building fallthroughs map with a skipped arg and prop fallthrough.
    """
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'project': '--book-project'},
        {'project': [deps.PropertyFallthrough(properties.VALUES.core.project)]})

    result = info.BuildFullFallthroughsMap()

    expected = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                deps.ArgFallthrough('--book'),
                self.resource_spec.collection_info,
                'projectsId'),
            deps.ArgFallthrough('--book-project'),
            deps.PropertyFallthrough(properties.VALUES.core.project)],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                deps.ArgFallthrough('--book'),
                self.resource_spec.collection_info,
                'shelvesId')
        ],
        'book': [
            deps.ArgFallthrough('--book')]}
    self.assertEqual(expected, result)

  @parameterized.named_parameters(
      ('Flag', '--book', False, True,
       [deps.ArgFallthrough('--book')]),
      ('Positional', 'BOOK', False, True,
       [deps.ArgFallthrough('BOOK')]),
      ('FlagPlural', '--books', True, True,
       [deps.ArgFallthrough('--books', plural=True)]),
      ('PositionalPlural', 'BOOKS', True, True,
       [deps.ArgFallthrough('BOOKS', plural=True)]))
  def testBuildFullFallthroughsMapAnchor(self, name, plural, required,
                                         expected_book_fallthroughs):
    """Tests fallthroughs map is properly built."""
    info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'The book to act upon.',
        {'book': name, 'shelf': '--shelf', 'project': '--book-project'},
        {'project': [deps.PropertyFallthrough(properties.VALUES.core.project)]},
        plural=plural,
        required=required)

    result = info.BuildFullFallthroughsMap()

    self.assertEqual(expected_book_fallthroughs, result['book'])

  @parameterized.named_parameters(
      ('Flag', '--book', 'book'),
      ('Positional', 'BOOK', 'BOOK'))
  def testParse(self, name, namespace_name):
    """Tests Parse method correctly parses with different anchor names."""
    info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'The book to act upon.',
        {'book': name, 'shelf': '--shelf', 'project': '--book-project'},
        {},
        required=True)
    args_dict = {namespace_name: 'examplebook',
                 'shelf': 'exampleshelf',
                 'book_project': 'exampleproject'}
    parsed_args = self._GetMockNamespace(**args_dict)

    parsed = info.Parse(parsed_args)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

  @parameterized.named_parameters(
      ('MissingProject',
       {'book': 'examplebook', 'shelf': 'exampleshelf'}, '[project]'),
      ('MissingShelf',
       {'book': 'examplebook', 'book_project': 'exampleproject'}, '[shelf]'))
  def testParseError(self, args_dict, error_msg):
    """Tests that Parse method raises InitializationError when necessary."""
    self.UnsetProject()
    info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'The book to act upon.',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {},
        required=True)
    parsed_args = self._GetMockNamespace(**args_dict)

    with self.assertRaisesRegex(concepts.InitializationError,
                                re.escape(error_msg)):
      info.Parse(parsed_args)


if __name__ == '__main__':
  test_case.main()
