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
"""Tests for the handlers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import info_holders
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util


class HandlersTest(concepts_test_base.MultitypeTestBase,
                   parameterized.TestCase):
  """Test methods for ConceptInfo objects and Parse function."""

  @property
  def default_arg_list(self):
    return ['--book', 'examplebook', '--shelf', 'exampleshelf',
            '--book-project', 'exampleproject']

  def SetUpResourceInfo(self, name):
    """Sets up a test ConceptInfo for a ResourcePresentationSpec.

    Uses an example resource.

    Args:
      name: str, the name of the anchor argument for the concept spec.

    Returns:
      (handlers.ConceptInfo) the concept handler.
    """
    resource_info = info_holders.ResourceInfo(
        name,
        self.resource_spec,
        'a resource',
        {'book': name, 'shelf': '--shelf', 'project': '--book-project'},
        {})
    return resource_info

  def SetUpConceptParser(self, name, plural=False, required=False):
    concept_parsers.ConceptParser.ForResource(
        name,
        self.resource_spec,
        'a resource',
        flag_name_overrides={
            'project': '{}-project'.format(
                name if name.startswith('--') else '--' + name.lower())},
        plural=plural,
        required=required
    ).AddToParser(self.parser)

  def SetUpConceptParserWithFallthroughs(self, name, fallthroughs_map=None):
    resource_spec = util.GetBookResource()
    fallthroughs_map = fallthroughs_map or {}
    for attribute in resource_spec.attributes:
      fallthroughs = fallthroughs_map.get(attribute.name, [])
      attribute.fallthroughs = fallthroughs
    flag_name_overrides = {'project': '--book-project'}
    concept_parsers.ConceptParser(
        [presentation_specs.ResourcePresentationSpec(
            name,
            resource_spec,
            'a resource',
            flag_name_overrides=flag_name_overrides)
        ]
    ).AddToParser(self.parser)

  def SetUpConceptParserForMultitypeWithFallthroughs(
      self, name, fallthroughs_map=None):
    resource_spec = self.two_way_resource
    fallthroughs_map = fallthroughs_map or {}
    for attribute in resource_spec.attributes:
      fallthroughs = fallthroughs_map.get(attribute.name, [])
      attribute.fallthroughs = fallthroughs
    flag_name_overrides = {'project': '--book-project'}
    concept_parsers.ConceptParser(
        [presentation_specs.MultitypeResourcePresentationSpec(
            name,
            resource_spec,
            'a resource',
            flag_name_overrides=flag_name_overrides)
        ]
    ).AddToParser(self.parser)

  def testParsedArgs(self):
    """Test for simple ParsedArgs() method."""
    handler = handlers.RuntimeHandler()
    parsed_args = self.parser.parser.parse_args([])
    handler.parsed_args = parsed_args
    self.assertEqual(parsed_args, handler.ParsedArgs())

  def testRuntimeHandlerAddConcept(self):
    """Tests that AddConcept adds attributes correctly to RuntimeHandler."""
    resource_infos = [self.SetUpResourceInfo('--book'),
                      self.SetUpResourceInfo('--other-book')]
    runtime_handler = handlers.RuntimeHandler()
    runtime_handler.AddConcept('book', resource_infos[0])
    runtime_handler.AddConcept('other_book', resource_infos[1])
    self.assertTrue(hasattr(runtime_handler, 'book'))
    self.assertTrue(hasattr(runtime_handler, 'other_book'))

  def testRuntimeHandlerAddConceptFailsForRepeatedName(self):
    """Tests that AddConcept fails adding attributes if name is repeated."""
    resource_infos = [self.SetUpResourceInfo('--book'),
                      self.SetUpResourceInfo('--other-book'),
                      self.SetUpResourceInfo('--a-third-book')]
    runtime_handler = handlers.RuntimeHandler()
    runtime_handler.AddConcept('book', resource_infos[0])
    runtime_handler.AddConcept('other_book', resource_infos[1])
    with self.assertRaises(handlers.RepeatedConceptName):
      runtime_handler.AddConcept('book', resource_infos[2])

  def testRuntimeHandlerArgNameToConceptInfo(self):
    resource_info = info_holders.ResourceInfo(
        '--book',
        self.resource_spec,
        'group help',
        {'book': '--book', 'shelf': '--shelf', 'project': '--book-project'},
        {})
    runtime_handler = handlers.RuntimeHandler()
    runtime_handler.AddConcept('book', resource_info)
    self.assertEqual(
        resource_info, runtime_handler.ArgNameToConceptInfo('book'))
    self.assertEqual(
        resource_info, runtime_handler.ArgNameToConceptInfo('shelf'))
    self.assertEqual(
        resource_info, runtime_handler.ArgNameToConceptInfo('book_project'))

  def testParseCached(self):
    """Tests that the result of parsing a resource argument is cached."""
    project_ids = ['my-project']  # one entry, so calling pop() twice will error
    fallthroughs = {'project': [deps_lib.Fallthrough(project_ids.pop, 'hint')]}
    self.SetUpConceptParserWithFallthroughs('--book', fallthroughs)
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--shelf', 'exampleshelf'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/my-project/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

    parsed = parsed_args.CONCEPTS.book.Parse()
    self.assertEqual(
        'projects/my-project/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

  def testClearCache(self):
    """Tests that ClearCache method allows new resource to be parsed."""
    project_ids = ['another-project', 'my-project']
    fallthroughs = {'project': [deps_lib.Fallthrough(project_ids.pop, 'hint')]}
    self.SetUpConceptParserWithFallthroughs('--book', fallthroughs)
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--shelf', 'exampleshelf'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/my-project/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

    # After clearing cache, should parse a new value.
    resource_info = parsed_args.CONCEPTS.ArgNameToConceptInfo('book')
    resource_info.ClearCache()
    new_parsed = parsed_args.CONCEPTS.book.Parse()
    self.assertEqual(
        'projects/another-project/shelves/exampleshelf/books/examplebook',
        new_parsed.RelativeName())

  def testParseCachedMultitype(self):
    shelf_ids = ['my-shelf']  # one entry, so calling pop() twice will error
    fallthroughs = {'shelf': [deps_lib.Fallthrough(shelf_ids.pop, 'hint')]}
    self.SetUpConceptParserForMultitypeWithFallthroughs('--book', fallthroughs)
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--book-project', 'exampleproject'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/exampleproject/shelves/my-shelf/books/examplebook',
        parsed.result.RelativeName())

    parsed = parsed_args.CONCEPTS.book.Parse()
    self.assertEqual(
        'projects/exampleproject/shelves/my-shelf/books/examplebook',
        parsed.result.RelativeName())

  def testClearCacheMultitype(self):
    shelf_ids = ['another-shelf', 'my-shelf']
    fallthroughs = {'shelf': [deps_lib.Fallthrough(shelf_ids.pop, 'hint')]}
    self.SetUpConceptParserForMultitypeWithFallthroughs('--book', fallthroughs)
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--book-project', 'exampleproject'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/exampleproject/shelves/my-shelf/books/examplebook',
        parsed.result.RelativeName())

    resource_info = parsed_args.CONCEPTS.ArgNameToConceptInfo('book')
    resource_info.ClearCache()

    new_parsed = parsed_args.CONCEPTS.book.Parse()
    self.assertEqual(
        'projects/exampleproject/shelves/another-shelf/books/examplebook',
        new_parsed.result.RelativeName())

  def testReset(self):
    """Tests that ClearCache method allows new resource to be parsed."""
    project_ids = ['another-project', 'my-project']
    fallthroughs = {'project': [deps_lib.Fallthrough(project_ids.pop, 'hint')]}
    self.SetUpConceptParserWithFallthroughs('--book', fallthroughs)
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--shelf', 'exampleshelf'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/my-project/shelves/exampleshelf/books/examplebook',
        parsed.RelativeName())

    # After resetting runtime handler, should parse a new value.
    parsed_args.CONCEPTS.Reset()
    new_parsed = parsed_args.CONCEPTS.book.Parse()
    self.assertEqual(
        'projects/another-project/shelves/exampleshelf/books/examplebook',
        new_parsed.RelativeName())

  def testParseWithPropertyFallthrough(self):
    """Tests Parse method correctly parses with a property fallthrough."""
    self.SetUpConceptParserWithFallthroughs(
        '--book',
        {'project': [
            deps_lib.PropertyFallthrough(properties.VALUES.core.project)]})
    parsed_args = self.parser.parser.parse_args(
        ['--book', 'examplebook', '--shelf', 'exampleshelf'])

    parsed = parsed_args.CONCEPTS.book.Parse()

    self.assertEqual(
        'projects/{}/shelves/exampleshelf/books/examplebook'.format(
            self.Project()),
        parsed.RelativeName())

  @parameterized.named_parameters(
      ('Positional', 'BOOKS', False,
       ['example', 'example2', '--shelf', 'exampleshelf']),
      ('PositionalRequired', 'BOOKS', True,
       ['example', 'example2', '--shelf', 'exampleshelf']),
      ('Flag', '--books', False,
       ['--books', 'example,example2', '--shelf', 'exampleshelf']),
      ('FlagRequired', '--books', True,
       ['--books', 'example,example2', '--shelf', 'exampleshelf'])
  )
  def testParsePlural(self, name, required, args):
    """Test Parse method with plural resources."""
    self.SetUpConceptParser(name, plural=True, required=required)

    namespace = self.parser.parser.parse_args(args)
    books = namespace.CONCEPTS.books.Parse()
    expected_names = [
        'projects/{}/shelves/exampleshelf/books/example'.format(
            self.Project()),
        'projects/{}/shelves/exampleshelf/books/example2'.format(
            self.Project())]
    self.assertEqual(expected_names,
                     [book.RelativeName() for book in books])

  @parameterized.named_parameters(
      ('Positional', 'BOOKS'),
      ('Flag', '--books')
  )
  def testParsePluralEmpty(self, name):
    """Test Parse method with plural resources."""
    self.SetUpConceptParser(name, plural=True, required=False)
    namespace = self.parser.parser.parse_args([])
    books = namespace.CONCEPTS.books.Parse()
    self.assertEqual([], books)

  @parameterized.named_parameters(
      ('Positional', 'BOOK', False, None),
      ('Flag', '--book', False, None),
      ('PositionalPlural', 'BOOK', True, []),
      ('FlagPlural', '--book', True, []),
  )
  def testParseEmptyRequired(self, name, plural, return_value):
    """Test Parse method with plural resources."""
    concept_parsers.ConceptParser.ForResource(
        name,
        self.SetUpFallthroughSpec(
            deps_lib.Fallthrough(lambda: return_value, hint='h')),
        'a resource',
        plural=plural,
        required=True).AddToParser(self.parser)
    namespace = self.parser.parser.parse_args([])
    with self.assertRaises(handlers.ParseError):
      namespace.CONCEPTS.book.Parse()

  @parameterized.named_parameters(
      ('Overrides',
       ['projects/project1/shelves/shelf1/books/book1',
        'projects/project2/shelves/shelf2/books/book2',
        '--shelf', 'shelf3']),
      ('OneOverride',
       ['book1', 'projects/project2/shelves/shelf2/books/book2',
        '--shelf', 'shelf1', '--books-project', 'project1'])
  )
  def testParsePluralResourceWithURIs(self, args):
    """Test Parse method with plural resources given URI args."""
    self.SetUpConceptParser('BOOKS', plural=True)

    namespace = self.parser.parser.parse_args(args)
    books = namespace.CONCEPTS.books.Parse()
    self.assertEqual(
        ['projects/project1/shelves/shelf1/books/book1',
         'projects/project2/shelves/shelf2/books/book2'],
        [book.RelativeName() for book in books])

  @parameterized.named_parameters(
      ('Flag', '--book', False, 'book', None),
      ('FlagPlural', '--books', True, 'books', []),
      ('Positional', 'BOOK', False, 'book', None),
      ('PositionalPlural', 'BOOKS', True, 'books', [])
  )
  def testParseNonRequiredArgs(self, name, plural, dest, expected):
    """Test Parse method with plural resources."""
    self.SetUpConceptParser(name, plural=plural, required=False)
    args = self.parser.parser.parse_args([])
    self.assertEqual(expected, getattr(args.CONCEPTS, dest).Parse())

  @parameterized.named_parameters(
      ('Used',
       ['--book', 'examplebook', '--book-project', 'exampleproject',
        '--other-flag', 'exampleshelf']),
      ('NotUsed',
       ['--book',
        'projects/exampleproject/shelves/exampleshelf/books/examplebook']))
  def testParseWithArbitraryArgFallthrough(self, args_to_parse):
    fallthroughs_map = {'shelf': [deps_lib.ArgFallthrough('--other-flag')]}
    self.SetUpConceptParserWithFallthroughs(
        '--book',
        fallthroughs_map)
    self.parser.add_argument('--other-flag', help='h')
    parsed_args = self.parser.parser.parse_args(args_to_parse)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf/books/examplebook',
        parsed_args.CONCEPTS.book.Parse().RelativeName())


if __name__ == '__main__':
  test_case.main()
