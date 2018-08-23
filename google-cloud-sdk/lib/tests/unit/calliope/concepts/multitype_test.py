# -*- coding: utf-8 -*- #
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

"""Tests for the concepts module.

There are three main types of multitype concepts being tested here: 1) a
"two-way" resource (all attributes of the subtype are the same except that one
pair is different such as project versus organization); 2) a "four-way" resource
(two pairs differ, such as project versus organization and region versus zone,
or in this case, shelf versus case); 3) a "parent-child" resource where all
attributes are the same except that the "child" type has one extra, such as a
zone and instance resource or in this case a shelf and book resource.

Each is tested to make sure that if the user specifies *enough* information to
determine the type, the concept initializes properly; that if the user specifies
*too little* information to determine the type on the command line, the concept
fails to initialize; that if the user specifies *incompatible* attributes on the
command line, the concept fails to initialize.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import multitype
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util


class MultitypeTestsGeneral(concepts_test_base.MultitypeTestBase):
  """Tests for creating multitype resources."""

  def testCreateMultiTypeResource(self):
    project_book_resource = util.GetBookResource(name='projectbook')
    organization_book_resource = util.GetOrgShelfBookResource(name='orgbook')
    resource = multitype.MultitypeResourceSpec(
        'book',
        project_book_resource,
        organization_book_resource)
    expected_attributes = (
        project_book_resource.attributes +
        organization_book_resource.attributes[:1])
    self.assertEqual(
        expected_attributes,
        resource.attributes)
    self.assertNotEqual(resource.type_enum['projectbook'],
                        resource.type_enum['orgbook'])
    self.assertEqual(
        {'project': [resource.type_enum['projectbook']],
         'organization': [resource.type_enum['orgbook']],
         'shelf': [resource.type_enum['projectbook'],
                   resource.type_enum['orgbook']],
         'book': [resource.type_enum['projectbook'],
                  resource.type_enum['orgbook']]},
        resource._attribute_to_types_map)

  def testCreateMultiTypeConceptRenamesTypes(self):
    project_book_resource = util.GetBookResource()
    organization_book_resource = util.GetOrgShelfBookResource()
    resource = multitype.MultitypeConceptSpec(
        'book',
        project_book_resource,
        organization_book_resource)
    self.assertNotEqual(resource.type_enum['book_project_shelf_book'],
                        resource.type_enum['book_organization_shelf_book'])

  def testCreateMultiTypeResourceRenamesTypes(self):
    project_book_resource = util.GetBookResource()
    organization_book_resource = util.GetOrgShelfBookResource()
    resource = multitype.MultitypeResourceSpec(
        'book',
        project_book_resource,
        organization_book_resource)
    self.assertNotEqual(
        resource.type_enum['example.projects.shelves.books'],
        resource.type_enum['example.organizations.shelves.books'])

  def testCreateMultitypeResourceFailsWithDuplicateCollection(self):
    project_book_resource = util.GetBookResource()
    with self.assertRaisesRegexp(ValueError, 'projects.shelves.books'):
      multitype.MultitypeResourceSpec(
          'book',
          project_book_resource,
          project_book_resource)

  def testCreateMultiTypeResourceFailsWithMismatchedAttribute(self):
    book_resource = util.GetBookResource()
    # Create a second resource with an attribute named "project" that doesn't
    # match the book resource's project attribute.
    project_resource = concepts.ResourceSpec(
        'example.projects',
        'project',
        projectsId=concepts.ResourceParameterAttributeConfig(
            name='project',
            help_text='The Cloud project of the {resource}.'))
    with self.assertRaisesRegexp(
        multitype.ConfigurationError,
        re.escape('[project]')):
      multitype.MultitypeResourceSpec(
          'book',
          book_resource,
          project_resource)


class MultitypeTestsTwoWay(concepts_test_base.MultitypeTestBase,
                           parameterized.TestCase):
  """Tests for a two-way multitype concept (project or organization)."""

  def SetUp(self):
    """Get resource with two possible top-level params."""
    project_book_resource = util.GetBookResource(name='projectbook')
    organization_book_resource = util.GetOrgShelfBookResource(name='orgbook')
    self.resource = multitype.MultitypeResourceSpec(
        'book',
        project_book_resource,
        organization_book_resource)

  @parameterized.named_parameters(
      ('Simple', True, None, False,
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # If both project and org are specified, but only one is "active," use
      # the active one.
      ('ActiveOverNonActive', False, 'my-org', True,
       'organizations/my-org/shelves/my-shelf/books/my-book'),
      # If both project and org have "active" fallthroughs but one does not
      # return a value, use the one that does.
      ('AllActiveSomeSpecified', True, None, True,
       'projects/my-project/shelves/my-shelf/books/my-book'))
  def testInitialize(self, proj_active, org_value, org_active,
                     expected):
    fallthroughs_map = {
        'project': [deps.Fallthrough(lambda: 'my-project', 'h',
                                     active=proj_active)],
        'organization': [
            deps.Fallthrough(lambda: org_value, 'h', active=org_active)],
        'shelf': [deps.Fallthrough(lambda: 'my-shelf', 'h')],
        'book': [deps.Fallthrough(lambda: 'my-book', 'h', active=True)]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # Should initialize directly from the anchor.
      ('FullySpecifiedProj', None, None, None,
       'projects/my-project/shelves/my-shelf/books/my-book',
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('FullySpecifiedOrg', None, None, None,
       'organizations/my-org/shelves/my-shelf/books/my-book',
       'organizations/my-org/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedProj', 'my-proj', None, 'my-shelf', 'my-book',
       'projects/my-proj/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedOrg', None, 'my-org', 'my-shelf', 'my-book',
       'organizations/my-org/shelves/my-shelf/books/my-book'))
  def testInitializeWithAnchor(self, proj_value, org_value, shelf_value,
                               book_value, expected):
    book_fallthrough = deps.Fallthrough(lambda: book_value, 'h', active=True)
    fallthroughs_map = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'projectsId'),
            deps.Fallthrough(lambda: proj_value, 'h', active=True)],
        'organization': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'organizationsId'),
            deps.Fallthrough(lambda: org_value, 'h', active=True)],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'shelvesId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'shelvesId'),
            deps.Fallthrough(lambda: shelf_value, 'h')],
        'book': [book_fallthrough]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # Fail if both project and organization are specified.
      ('ConflictingAttributes', 'my-project', 'my-org',
       '[project, shelf, book, organization]'),
      # Fail if neither project nor organization specified.
      ('Underspecified', None, None, '[shelf, book]'))
  def testInitializeError(self, proj_value, org_value, expected_error):
    fallthroughs_map = {
        'project': [
            deps.Fallthrough(lambda: proj_value, 'h', active=True)],
        'organization': [
            deps.Fallthrough(lambda: org_value, 'h', active=True)],
        'shelf': [deps.Fallthrough(lambda: 'my-shelf', 'h', active=True)],
        'book': [deps.Fallthrough(lambda: 'my-book', 'h', active=True)]}
    with self.assertRaisesRegexp(
        multitype.ConflictingTypesError,
        re.escape(expected_error)):
      self.resource.Initialize(fallthroughs_map).result.RelativeName()

  def testInitializeNotFullySpecified(self):
    book_fallthrough = deps.Fallthrough(lambda: 'my-book', 'h', active=True)
    fallthroughs_map = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'projectsId'),
            deps.Fallthrough(lambda: 'my-project', 'h')],
        'organization': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'organizationsId'),
            deps.Fallthrough(lambda: 'my-org', 'h', active=True)],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'shelvesId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'shelvesId'),
            deps.Fallthrough(lambda: None, 'h')],
        'book': [book_fallthrough]}
    with self.assertRaisesRegexp(
        concepts.InitializationError,
        re.escape('[shelf]')):
      self.resource.Initialize(fallthroughs_map).result.RelativeName()


class MultitypeTestsFourWay(concepts_test_base.MultitypeTestBase,
                            parameterized.TestCase):
  """Test for a multitype resource with four possible types."""

  def SetUp(self):
    self.resource = self.four_way_resource

  @parameterized.named_parameters(
      # If only three attributes are specified, use the matching type.
      ('Simple', True, True, True, True,
       'my-project', None, 'my-shelf', None,
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # Same test, complementary attributes.
      ('OtherSimple', True, True, True, True,
       None, 'my-org', None, 'my-case',
       'organizations/my-org/cases/my-case/books/my-book'),
      # If all are specified but only three are actively specified, use the
      # type matching the actively specified.
      ('ActiveOverNonActive', True, False, True, False,
       'my-project', 'my-org', 'my-shelf', 'my-case',
       'projects/my-project/shelves/my-shelf/books/my-book'))
  def testInitialize(
      self, proj_active, org_active, shelf_active, case_active,
      proj_value, org_value, shelf_value, case_value, expected):
    fallthroughs_map = {
        'project': [
            deps.Fallthrough(lambda: proj_value, 'h', active=proj_active)],
        'organization': [
            deps.Fallthrough(lambda: org_value, 'h', active=org_active)],
        'shelf': [
            deps.Fallthrough(lambda: shelf_value, 'h', active=shelf_active)],
        'case': [
            deps.Fallthrough(lambda: case_value, 'h', active=case_active)],
        'book': [deps.Fallthrough(lambda: 'my-book', 'h', active=True)]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # Should initialize directly from the anchor.
      ('FullySpecifiedProjShelf', None, None, None, None,
       'projects/my-project/shelves/my-shelf/books/my-book',
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('FullySpecifiedOrgCase', None, None, None, None,
       'organizations/my-org/cases/my-case/books/my-book',
       'organizations/my-org/cases/my-case/books/my-book'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedProjCase', 'my-proj', None, None, 'my-case',
       'my-book', 'projects/my-proj/cases/my-case/books/my-book'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedOrgShelf', None, 'my-org', 'my-shelf', None,
       'my-book', 'organizations/my-org/shelves/my-shelf/books/my-book'))
  def testInitializeWithAnchor(self, proj_value, org_value, shelf_value,
                               case_value, book_value, expected):
    book_fallthrough = deps.Fallthrough(lambda: book_value, 'h', active=True)
    fallthroughs_map = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'projectsId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.proj_case_book_collection,
                'projectsId'),
            deps.Fallthrough(lambda: proj_value, 'h', active=True)],
        'organization': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'organizationsId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_case_book_collection,
                'organizationsId'),
            deps.Fallthrough(lambda: org_value, 'h', active=True)],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_shelf_book_collection,
                'shelvesId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'shelvesId'),
            deps.Fallthrough(lambda: shelf_value, 'h', active=True)],
        'case': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.proj_case_book_collection,
                'casesId'),
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.org_case_book_collection,
                'casesId'),
            deps.Fallthrough(lambda: case_value, 'h', active=True)],
        'book': [book_fallthrough]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # If both project and org are specified, fail.
      ('ConflictingAttributesTop', 'my-project', 'my-org', 'my-shelf', None,
       '[project, shelf, book, organization]'),
      # If both shelf and case are specified, fail.
      ('ConflictingAttributesMiddle', 'my-project', None, 'my-shelf', 'my-case',
       '[project, shelf, book, case]'),
      # If neither project nor org is specified, fail.
      ('UnderspecifiedTop', None, None, None, 'my-case', '[book, case]'),
      # If neither shelf nor case is specified, fail.
      ('UnderspecifiedMiddle', 'my-project', None, None, None,
       '[project, book]'))
  def testInitializeError(self, proj_value, org_value, shelf_value, case_value,
                          expected_error):
    fallthroughs_map = {
        'project': [deps.Fallthrough(lambda: proj_value, 'h', active=True)],
        'organization': [
            deps.Fallthrough(lambda: org_value, 'h', active=True)],
        'shelf': [deps.Fallthrough(lambda: shelf_value, 'h', active=True)],
        'case': [deps.Fallthrough(lambda: case_value, 'h', active=True)],
        'book': [deps.Fallthrough(lambda: 'my-book', 'h', active=True)]}
    with self.assertRaisesRegexp(
        multitype.ConflictingTypesError, re.escape(expected_error)):
      self.resource.Initialize(fallthroughs_map)

  def testInitializeConceptNotFullySpecified(self):
    fallthroughs_map = {
        'project': [deps.Fallthrough(lambda: 'my-project', 'h')],
        'organization': [
            deps.Fallthrough(lambda: 'my-org', 'h', active=True)],
        'shelf': [deps.Fallthrough(lambda: 'my-shelf', 'h', active=True)],
        'case': [deps.Fallthrough(lambda: None, 'h')],
        'book': [deps.Fallthrough(lambda: None, 'h')]}
    with self.assertRaisesRegexp(
        concepts.InitializationError,
        re.escape('[book]')):
      self.resource.Initialize(fallthroughs_map)

  @parameterized.named_parameters(
      ('Flag', '--book', 'book', False, False,
       'examplebook', 'exampleshelf', 'exampleproject',
       'projects/exampleproject/shelves/exampleshelf/books/examplebook',
       'Type.projectbook'),
      ('Positional', 'BOOK', 'BOOK', False, False,
       'examplebook', 'exampleshelf', 'exampleproject',
       'projects/exampleproject/shelves/exampleshelf/books/examplebook',
       'Type.projectbook'),
      ('Plural', '--books', 'books', True, False,
       ['example1', 'example2'], 'exampleshelf', 'exampleproject',
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'projects/exampleproject/shelves/exampleshelf/books/example2'],
       ['Type.projectbook', 'Type.projectbook']),
      ('PluralAnchors', '--books', 'books', True, False,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'organizations/exampleorg/cases/examplecase/books/example2'],
       None, None,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'organizations/exampleorg/cases/examplecase/books/example2'],
       ['Type.projectbook', 'Type.orgcasebook']),
      ('Empty', '--book', 'book', False, True, None, None, None,
       None, 'None'),
      ('PluralEmpty', '--book', 'book', True, True, [], None, None,
       [], []))
  def testParse(self, name, namespace_name, plural, allow_empty, book_arg,
                shelf_arg, project_arg, expected, expected_type):
    """Tests Parse method correctly parses with different anchor names."""
    attribute_to_args_map = {
        'book': name, 'shelf': '--shelf', 'project': '--book-project',
        'organization': '--organization', 'case': '--case'}
    args_dict = {namespace_name: book_arg,
                 'shelf': shelf_arg,
                 'book_project': project_arg,
                 'organization': None,
                 'case': None}
    parsed_args = self._GetMockNamespace(**args_dict)

    parsed = self.resource.Parse(
        attribute_to_args_map,
        {},
        parsed_args=parsed_args,
        allow_empty=allow_empty,
        plural=plural)
    if not plural:
      if expected is None:
        self.assertIsNone(parsed.result)
      else:
        self.assertEqual(
            expected, parsed.result.RelativeName())
      self.assertEqual(expected_type, str(parsed.type_))
    else:
      self.assertEqual(
          expected, [r.result.RelativeName() for r in parsed])
      self.assertEqual(
          expected_type, [str(r.type_) for r in parsed])

  @parameterized.named_parameters(
      ('RequiredMissingAnchor', False, False,
       {'book': [deps.Fallthrough(lambda: None, 'h')]},
       {'book_project': 'p1', 'shelf': 's1'},
       concepts.InitializationError, '[book]'),
      ('RequiredEmpty', False, False,
       {}, {}, concepts.InitializationError, '[book]'),
      ('RequiredPluralMissingAnchor', True, False,
       {'book': [deps.Fallthrough(lambda: None, 'h')]},
       {'book_project': 'p1', 'shelf': 's1'},
       concepts.InitializationError, '[book]'),
      ('RequiredPluralEmpty', True, False,
       {}, {}, concepts.InitializationError, '[book]'),
      ('NotFullySpecified', False, False,
       {}, {'book_project': 'p1', 'shelf': 's1'},
       concepts.InitializationError, '[book]'),
      ('PluralNotFullySpecified', True, False,
       {}, {'book_project': 'p1', 'shelf': 's1'},
       concepts.InitializationError, '[book]'))
  def testParseError(self, plural, allow_empty, fallthroughs, args_dict,
                     expected_error, expected_msg):
    """Tests Parse method correctly parses with different anchor names."""
    attribute_to_args_map = {
        'book': '--book', 'shelf': '--shelf', 'project': '--book-project',
        'organization': '--organization', 'case': '--case'}
    parsed_args = self._GetMockNamespace(**args_dict)

    with self.assertRaisesRegexp(expected_error, re.escape(expected_msg)):
      self.resource.Parse(
          attribute_to_args_map,
          fallthroughs,
          parsed_args=parsed_args,
          allow_empty=allow_empty,
          plural=plural)


class MultitypeTestsParentChild(concepts_test_base.MultitypeTestBase,
                                parameterized.TestCase):
  """Tests for a parent-child resource (could be a resource or its parent type).
  """

  def SetUp(self):
    # The child.
    book_resource = util.GetBookResource(name='book')
    # Shelves are the parent - they contain books.
    shelf_resource = util.GetProjShelfResource(name='shelf')
    self.resource = multitype.MultitypeResourceSpec(
        'shelfbook',
        book_resource,
        shelf_resource)

  @parameterized.named_parameters(
      # If the child is actively specified, use the child type.
      ('ChildActivelySpecified', True,
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # Otherwise, use the parent type.
      ('ChildNotActivelySpecified', False,
       'projects/my-project/shelves/my-shelf'))
  def testInitialize(self, child_active, expected):
    fallthroughs_map = {
        'project': [
            deps.Fallthrough(lambda: 'my-project', 'h', active=True)],
        'shelf': [deps.Fallthrough(lambda: 'my-shelf', 'h', active=True)],
        'book': [deps.Fallthrough(lambda: 'my-book', 'h',
                                  active=child_active)]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # Should initialize directly from the anchor.
      ('FullySpecifiedBook', None, None,
       'projects/my-project/shelves/my-shelf/books/my-book',
       'projects/my-project/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('FullySpecifiedShelf', None, 'projects/my-proj/shelves/my-shelf',
       None, 'projects/my-proj/shelves/my-shelf'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedBook', 'my-proj', 'my-shelf', 'my-book',
       'projects/my-proj/shelves/my-shelf/books/my-book'),
      # Should initialize directly from the anchor.
      ('PartiallySpecifiedShelf', 'my-proj', 'my-shelf', None,
       'projects/my-proj/shelves/my-shelf'))
  def testInitializeWithAnchor(self, proj_value, shelf_value, book_value,
                               expected):
    book_fallthrough = deps.Fallthrough(lambda: book_value, 'h', active=True)
    shelf_fallthrough = deps.Fallthrough(lambda: shelf_value, 'h', active=True)
    fallthroughs_map = {
        'project': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'projectsId'),
            deps.FullySpecifiedAnchorFallthrough(
                shelf_fallthrough,
                self.shelf_collection,
                'projectsId'),
            deps.Fallthrough(lambda: proj_value, 'h', active=True)],
        'shelf': [
            deps.FullySpecifiedAnchorFallthrough(
                book_fallthrough,
                self.book_collection,
                'shelvesId'),
            deps.Fallthrough(lambda: shelf_value, 'h')],
        'book': [book_fallthrough]}
    self.assertEqual(
        expected,
        self.resource.Initialize(fallthroughs_map).result.RelativeName())

  @parameterized.named_parameters(
      # Will raise error for both anchors since book is not given.
      ('ShelfNotFullySpecified',
       'exampleproject', True, None, True, None, True,
       'The [shelfbook] resource is not properly specified.'),
      # Will attempt to initialize book
      ('BookNotFullySpecified',
       'exampleproject', False, None, False, 'examplebook', True,
       'The [book] resource is not properly specified.'))
  def testInitializeError(self, proj_value, proj_active, shelf_value,
                          shelf_active, book_value, book_active,
                          expected_error):
    fallthroughs_map = {
        'project': [
            deps.Fallthrough(lambda: proj_value, 'h', active=proj_active)],
        'shelf': [
            deps.Fallthrough(lambda: shelf_value, 'h', active=shelf_active)],
        'book': [
            deps.Fallthrough(lambda: book_value, 'h', active=book_active)]}
    with self.assertRaisesRegexp(
        concepts.InitializationError,
        re.escape(expected_error)):
      self.resource.Initialize(fallthroughs_map)

  def testInitializeNotFullySpecified(self):
    fallthroughs_map = {
        'project': [
            deps.Fallthrough(lambda: 'exampleproject', 'h', active=True)],
        'shelf': [deps.Fallthrough(lambda: None, 'h')],
        'book': [deps.Fallthrough(lambda: 'examplebook', 'h', active=True)]}
    with self.assertRaisesRegexp(
        concepts.InitializationError,
        re.escape('[shelf]')):
      self.resource.Initialize(fallthroughs_map).RelativeName()

  @parameterized.named_parameters(
      ('Child', '--book', 'book', False, False,
       'examplebook', 'exampleshelf', 'exampleproject',
       'projects/exampleproject/shelves/exampleshelf/books/examplebook',
       'Type.book'),
      ('Parent', '--book', 'book', False, False,
       None, 'exampleshelf', 'exampleproject',
       'projects/exampleproject/shelves/exampleshelf',
       'Type.shelf'),
      ('Plural', '--books', 'books', True, False,
       ['example1', 'example2'], 'exampleshelf', 'exampleproject',
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'projects/exampleproject/shelves/exampleshelf/books/example2'],
       ['Type.book', 'Type.book']),
      ('PluralAnchors', '--books', 'books', True, False,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'projects/exampleproject/shelves/exampleshelf/books/example2'],
       None, None,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'projects/exampleproject/shelves/exampleshelf/books/example2'],
       ['Type.book', 'Type.book']),
      ('PluralEmpty', '--books', 'books', True, True, [], None, None,
       [], []),
      ('PluralParent', '--books', 'books', True, True, [], 'exampleshelf',
       'exampleproject', ['projects/exampleproject/shelves/exampleshelf'],
       ['Type.shelf']),
      ('PluralParentRequired', '--books', 'books', True, False, [],
       'exampleshelf', 'exampleproject',
       ['projects/exampleproject/shelves/exampleshelf'], ['Type.shelf']))
  def testParse(self, name, namespace_name, plural, allow_empty, book_arg,
                shelf_arg, project_arg, expected, expected_type):
    """Tests Parse method correctly parses with different anchor names."""
    attribute_to_args_map = {
        'book': name, 'shelf': '--shelf', 'project': '--book-project'}
    args_dict = {namespace_name: book_arg,
                 'shelf': shelf_arg,
                 'book_project': project_arg}
    parsed_args = self._GetMockNamespace(**args_dict)

    parsed = self.resource.Parse(
        attribute_to_args_map,
        {},
        parsed_args=parsed_args,
        allow_empty=allow_empty,
        plural=plural)

    if not plural:
      if expected is None:
        self.assertIsNone(parsed.result)
      else:
        self.assertEqual(
            expected, parsed.result.RelativeName())
      self.assertEqual(expected_type, str(parsed.type_))
    else:
      self.assertEqual(
          expected, [r.result.RelativeName() for r in parsed])
      self.assertEqual(
          expected_type, [str(r.type_) for r in parsed])

  @parameterized.named_parameters(
      ('ParentInChild', False,
       'projects/exampleproject/shelves/exampleshelf',
       'The [book] resource'),
      ('PluralParentsInChild', True,
       ['projects/exampleproject/shelves/exampleshelf',
        'projects/exampleproject/shelves/exampleshelf2'],
       'The [book] resource'))
  def testParseError(self, plural, book_arg, error):
    attribute_to_args_map = {
        'book': '--book', 'shelf': '--shelf', 'project': '--book-project'}
    args_dict = {'book': book_arg,
                 'shelf': None,
                 'book_project': None}
    parsed_args = self._GetMockNamespace(**args_dict)

    with self.assertRaisesRegex(concepts.InitializationError, re.escape(error)):
      self.resource.Parse(
          attribute_to_args_map,
          {},
          parsed_args=parsed_args,
          allow_empty=False,
          plural=plural)


class MultitypeTestsFourWayParentChild(concepts_test_base.MultitypeTestBase,
                                       parameterized.TestCase):
  """Tests for a multitype resource that can be parent/child or org/project."""

  def SetUp(self):
    # Just for convenience.
    self.resource = self.four_way_parent_child_resource

  @parameterized.named_parameters(
      ('ProjChild', '--book', 'book', False,
       'examplebook', 'exampleshelf', 'exampleproject', None,
       'projects/exampleproject/shelves/exampleshelf/books/examplebook',
       'Type.example.projects.shelves.books'),
      ('OrgChild', '--book', 'book', False,
       'examplebook', 'exampleshelf', None, 'exampleorg',
       'organizations/exampleorg/shelves/exampleshelf/books/examplebook',
       'Type.example.organizations.shelves.books'),
      ('ProjParent', '--book', 'book', False,
       None, 'exampleshelf', 'exampleproject', None,
       'projects/exampleproject/shelves/exampleshelf',
       'Type.example.projects.shelves'),
      ('OrgParent', '--book', 'book', False,
       None, 'exampleshelf', None, 'exampleorg',
       'organizations/exampleorg/shelves/exampleshelf',
       'Type.example.organizations.shelves'),
      ('Plural', '--books', 'books', True,
       ['example1', 'example2'], 'exampleshelf', 'exampleproject', None,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'projects/exampleproject/shelves/exampleshelf/books/example2'],
       ['Type.example.projects.shelves.books',
        'Type.example.projects.shelves.books']),
      ('PluralAnchors', '--books', 'books', True,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'organizations/exampleorg/shelves/exampleshelf/books/example2'],
       None, None, None,
       ['projects/exampleproject/shelves/exampleshelf/books/example1',
        'organizations/exampleorg/shelves/exampleshelf/books/example2'],
       ['Type.example.projects.shelves.books',
        'Type.example.organizations.shelves.books']))
  def testParseFourWayParentChild(self, name, namespace_name, plural, book_arg,
                                  shelf_arg, project_arg, org_arg, expected,
                                  expected_type):
    """Tests Parse method correctly parses with different anchor names."""
    attribute_to_args_map = {
        'book': name, 'shelf': '--shelf', 'project': '--book-project',
        'organization': '--organization'}
    args_dict = {namespace_name: book_arg,
                 'shelf': shelf_arg,
                 'book_project': project_arg,
                 'organization': org_arg}
    parsed_args = self._GetMockNamespace(**args_dict)

    parsed = self.resource.Parse(
        attribute_to_args_map,
        {},
        parsed_args=parsed_args,
        allow_empty=False,
        plural=plural)

    if not plural:
      self.assertEqual(
          expected, parsed.result.RelativeName())
      self.assertEqual(expected_type, str(parsed.type_))
    else:
      self.assertEqual(
          expected, [r.result.RelativeName() for r in parsed])
      self.assertEqual(
          expected_type, [str(r.type_) for r in parsed])


if __name__ == '__main__':
  test_case.main()
