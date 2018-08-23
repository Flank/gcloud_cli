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
"""Tests for the completers and resource_parameter_info modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.concepts import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.calliope.concepts import util
from tests.lib.command_lib.util.apis import base as apis_base
from tests.lib.command_lib.util.concepts import resource_completer_test_base

import mock
import six
from six.moves import zip  # pylint: disable=redefined-builtin


class ShelvesMessage(messages.Message):
  """Fake shelves list response."""

  class Shelf(messages.Message):
    name = messages.StringField(1)

  shelves = messages.MessageField('Shelf', 1, repeated=True)


class BooksMessage(messages.Message):
  """Fake books list response."""

  class Book(messages.Message):
    name = messages.StringField(1)

  books = messages.MessageField('Book', 1, repeated=True)


class ProjectsMessage(messages.Message):
  """Fake projects list response."""

  class Project(messages.Message):
    projectId = messages.StringField(1)  # pylint: disable=invalid-name

  projects = messages.MessageField('Project', 1, repeated=True)


class CompleterTest(concepts_test_base.ConceptsTestBase,
                    apis_base.Base,
                    parameterized.TestCase,
                    resource_completer_test_base.ResourceCompleterBase):

  def SetUp(self):
    self.mock_client = mock.MagicMock()
    self.StartObjectPatch(apis, 'GetClientInstance',
                          return_value=self.mock_client)
    self.presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec_auto_completers,
        'a resource',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False)
    self.resource_info = concept_parsers.ConceptParser(
        [self.presentation_spec]).GetInfo(self.presentation_spec.name)

  def BuildBooksList(self, books):
    """Helper function to build return message for fake books List method."""
    return BooksMessage(
        books=[
            BooksMessage.Book(name=book) for book in books])

  def BuildShelvesList(self, shelves):
    """Helper function to build return message for fake shelves List method."""
    return ShelvesMessage(
        shelves=[
            ShelvesMessage.Shelf(name=shelf) for shelf in shelves])

  def BuildProjectsList(self, projects):
    """Helper function to build return message for fake projects List method."""
    return ProjectsMessage(
        projects=[
            ProjectsMessage.Project(projectId=project) for project in projects]
    )

  def _PatchProjectReturnType(self):
    """Patch project resource method to have certain return type messages."""
    projects_method = registry.GetMethod('cloudresourcemanager.projects',
                                         'list')
    self.StartObjectPatch(projects_method, 'GetResponseType',
                          return_value=ProjectsMessage)

  def _PatchBookReturnType(self):
    """Patch book resource method to have certain return type messages."""
    books_method = registry.GetMethod('example.projects.shelves.books', 'list')
    self.StartObjectPatch(books_method, 'GetResponseType',
                          return_value=BooksMessage)

  def PatchBookResourceReturnTypes(self):
    """Patch each resource method to have certain return type messages."""
    self._PatchProjectReturnType()
    shelves_method = registry.GetMethod('example.projects.shelves', 'list')
    self.StartObjectPatch(shelves_method, 'GetResponseType',
                          return_value=ShelvesMessage)
    self._PatchBookReturnType()

  def SetUpAttrCompleterAndParameterInfo(self, attribute_name, argument_dest,
                                         args=None, static_params=None,
                                         id_field=None):
    """Creates a ResourceParameterInfo and a ResourceArgCompleter.

    Args:
      attribute_name: the name of the attribute for which to get a completer.
      argument_dest: the argument name to be given to the attribute (must
        match the argument that would be created by self.presentation_spec).
      args: {str: str} | None, the dict of arg names to values for the mock
        namespace.
      static_params: {str: str} | None, if given, overrides static fields in the
        list query.
      id_field: str | None, the completion_id_field configured for the resource
        attribute, if any.

    Returns:
      (Completer, ResourceParameterInfo), a tuple of the completer and the
        resource parameter info.
    """
    args = args or {}
    static_params = static_params or {}
    resource_spec = self.resource_spec
    book_collection = self.book_collection
    shelf_collection = self.shelf_collection
    project_collection = self.project_collection

    class BookCompleter(completers.ResourceArgumentCompleter):

      def __init__(self, **kwargs):
        super(BookCompleter, self).__init__(
            resource_spec,
            book_collection,
            registry.GetMethod('example.projects.shelves.books', 'list'),
            param='booksId',
            static_params=static_params,
            id_field=id_field,
            **kwargs)

    class ShelfCompleter(completers.ResourceArgumentCompleter):

      def __init__(self, **kwargs):
        super(ShelfCompleter, self).__init__(
            resource_spec,
            shelf_collection,
            registry.GetMethod('example.projects.shelves', 'list'),
            param='shelvesId',
            static_params=static_params,
            id_field=id_field,
            **kwargs)

    class ProjectCompleter(completers.ResourceArgumentCompleter):

      def __init__(self, **kwargs):
        super(ProjectCompleter, self).__init__(
            resource_spec,
            project_collection,
            registry.GetMethod('cloudresourcemanager.projects', 'list'),
            param='projectsId',
            static_params=static_params,
            id_field=id_field,
            **kwargs)

    attribute_completers = {
        'book': BookCompleter,
        'shelf': ShelfCompleter,
        'project': ProjectCompleter}
    completer = self.Completer(
        attribute_completers.get(attribute_name),
        args=args,
        handler_info=self.resource_info,
        cli=self.cli)
    argument = mock.MagicMock(dest=argument_dest)
    parameter_info = completer.ParameterInfo(self.parsed_args, argument)
    return completer, parameter_info

  @parameterized.named_parameters(
      ('Anchor', 'book',
       {'--shelf': 'exampleshelf', '--book-project': 'exampleproject'},
       'projects/exampleproject/shelves/exampleshelf'),
      ('Middle', 'shelf', {'--book-project': 'exampleproject'},
       'projects/exampleproject'))
  def testGetParentRef(self, attribute_name, args, expected_result):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        attribute_name,
        attribute_name,
        args=args)

    self.assertEqual(
        expected_result,
        completer.GetParentRef(parameter_info).RelativeName())

  @parameterized.named_parameters(
      # This is always None - no parent collection
      ('First', 'project', {}),
      # These should be None if there is not enough information.
      ('AnchorNotEnoughInfo', 'book', {}),
      ('MiddleNotEnoughInfo', 'shelf', {}))
  def testGetParentRefIsNone(self, attribute_name, args):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        attribute_name,
        args=args)

    self.assertIsNone(completer.GetParentRef(parameter_info))

  def testMethodProperty(self):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    completer, _ = self.SetUpAttrCompleterAndParameterInfo('book', 'book')
    method = completer.method
    self.assertEqual(self.book_collection, method.collection)
    self.assertEqual(method.name, 'list')

  @parameterized.named_parameters(
      ('WithParent', 'book',
       {'--shelf': 'exampleshelf', '--book-project': 'exampleproject'},
       'projects/exampleproject/shelves/exampleshelf'),
      ('NoParentFound', 'book', {}, None),
      ('MiddleWithParent', 'shelf', {'--book-project': 'exampleproject'},
       'projects/exampleproject'),
      ('Project', 'project', {}, None))
  def testBuildQuery(self, attribute_name, args, expected_parent):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        attribute_name, attribute_name, args=args)

    query = completer.BuildListQuery(parameter_info)

    self.assertEqual(expected_parent, query.parent)

  def testBuildQueryStaticParams(self):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)

    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        'book',
        args={'--shelf': 'exampleshelf',
              '--book-project': 'exampleproject'},
        static_params={'staticField': 'val'})

    query = completer.BuildListQuery(parameter_info)

    self.assertEqual(
        'projects/exampleproject/shelves/exampleshelf',
        query.parent)
    self.assertEqual(
        'val',
        query.staticField)

  @parameterized.named_parameters(
      ('Anchor', 'book',
       {'--shelf': 'exampleshelf', '--book-project': 'exampleproject'},
       {'shelvesId': 'exampleshelf', 'projectsId': 'exampleproject'}),
      ('MiddleParam', 'shelf', {'--book-project': 'exampleproject'},
       {'projectsId': 'exampleproject'}))
  def testBuildQueryAtomic(self, attribute_name, args, expected_fields):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', False),
        ('example.projects.shelves.books', False)]
    self.MockGetListCreateMethods(*collections)
    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        attribute_name, attribute_name, args=args)

    query = completer.BuildListQuery(parameter_info)
    for key, value in six.iteritems(expected_fields):
      self.assertEqual(value, getattr(query, key))

  @parameterized.named_parameters(
      ('Relative', True),
      ('NotRelative', False))
  def testUpdate(self, is_relative):
    collections = [
        ('cloudresourcemanager.projects', is_relative),
        ('example.projects.shelves', is_relative),
        ('example.projects.shelves.books', is_relative)]
    self.MockGetListCreateMethods(*collections)
    self.PatchBookResourceReturnTypes()

    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        'book',
        args={'--shelf': 'exampleshelf',
              '--book-project': 'exampleproject'})
    parent_name = 'projects/exampleproject/shelves/exampleshelf'
    self.mock_client.projects_shelves_books.List.return_value = (
        self.BuildBooksList(
            ['{}/books/b0'.format(parent_name),
             '{}/books/b1'.format(parent_name)]))

    updates = completer.Update(parameter_info, {})

    self.assertEqual(
        [['exampleproject', 'exampleshelf', 'b0'],
         ['exampleproject', 'exampleshelf', 'b1']],
        updates)

  def testUpdateWithIdField(self):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', False),
        ('example.projects.shelves.books', False)]
    self.MockGetListCreateMethods(*collections)

    class ListResponseMessage(messages.Message):

      class B(messages.Message):
        booksId = messages.StringField(1)  # pylint: disable=invalid-name

      books = messages.MessageField('B', 1, repeated=True)
    books_method = registry.GetMethod('example.projects.shelves.books', 'list')
    self.StartObjectPatch(books_method, 'GetResponseType',
                          return_value=ListResponseMessage)
    # Set up return value
    parent_name = 'projects/exampleproject/shelves/exampleshelf'
    self.mock_client.projects_shelves_books.List.return_value = (
        ListResponseMessage(
            books=[
                ListResponseMessage.B(
                    booksId='{}/books/b0'.format(parent_name)),
                ListResponseMessage.B(
                    booksId='{}/books/b1'.format(parent_name))]))

    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        'book',
        args={'--shelf': 'exampleshelf',
              '--book-project': 'exampleproject'},
        id_field='booksId')
    updates = completer.Update(parameter_info, {})

    self.assertEqual(
        [['exampleproject', 'exampleshelf', 'b0'],
         ['exampleproject', 'exampleshelf', 'b1']],
        updates)

  @parameterized.named_parameters(
      ('ValidationError', {}, 'may not have enough information'),
      ('HttpError',
       {'--book-project': 'exampleproject', '--shelf': 'exampleshelf'},
       'test'))
  def testUpdateFails(self, args, expected_error):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    books_method = registry.GetMethod('example.projects.shelves.books', 'list')
    self.PatchBookResourceReturnTypes()

    class ListRequestMessage(messages.Message):
      """Fake books list query."""
      parent = messages.StringField(1, required=True)

    self.StartObjectPatch(books_method, 'GetRequestType',
                          return_value=ListRequestMessage)

    # Mimic validation done during method.Call.
    def Validate(query):
      if query.parent is None:
        raise messages.ValidationError
      else:
        raise http_error.MakeHttpError(message='test')
    self.StartObjectPatch(books_method, 'Call', side_effect=Validate)

    completer, parameter_info = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        'book',
        args=args)

    with self.AssertRaisesExceptionMatches(completers.Error, expected_error):
      completer.Update(parameter_info, {})

  def testParameterInfo(self):
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    args = {'--shelf': 'exampleshelf'}
    completer, _ = self.SetUpAttrCompleterAndParameterInfo(
        'book',
        'book',
        args=args)
    argument = mock.MagicMock(dest='book')
    result = completer.ParameterInfo(self.parsed_args, argument)
    self.assertEqual(self.resource_info, result.resource_info)
    self.assertEqual(self.parsed_args, result.parsed_args)
    self.assertEqual(argument, result.argument)
    self.assertEqual(2, len(list(result._updaters.keys())))
    self.assertEqual(result._updaters['shelvesId'][1], True)
    self.assertEqual(result._updaters['shelvesId'][0]().collection,
                     'example.projects.shelves')
    self.assertEqual(result._updaters['projectsId'][1], True)
    self.assertEqual(result._updaters['projectsId'][0]().collection,
                     'example.projects')

  def testCompleterForAttribute(self):
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    expected_completer = completers.ResourceArgumentCompleter(
        self.resource_spec,
        self.book_collection,
        registry.GetMethod('example.projects.shelves.books', 'list'),
        param='booksId',
        static_params={})
    completer = completers.CompleterForAttribute(self.resource_spec, 'book')()
    self.assertEqual(expected_completer, completer)
    expected_completer = completers.ResourceArgumentCompleter(
        self.resource_spec,
        self.shelf_collection,
        registry.GetMethod('example.projects.shelves', 'list'),
        param='shelvesId',
        static_params={})
    completer = completers.CompleterForAttribute(self.resource_spec, 'shelf')()
    self.assertEqual(expected_completer, completer)
    expected_completer = completers.ResourceArgumentCompleter(
        self.resource_spec,
        self.project_collection,
        registry.GetMethod('cloudresourcemanager.projects', 'list'),
        param='projectsId',
        static_params={})
    completer = completers.CompleterForAttribute(
        self.resource_spec, 'project')()
    self.assertEqual(expected_completer, completer)

  def testAddCompleter(self):
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    info = concept_parsers.ConceptParser([self.presentation_spec]).GetInfo(
        self.presentation_spec.name)

    attribute_args = info.GetAttributeArgs()

    for arg, attribute_name in zip(attribute_args,
                                   ['project', 'shelf', 'book']):
      expected_completer = completers.CompleterForAttribute(
          self.resource_spec_auto_completers,
          attribute_name)
      actual_completer = arg.kwargs['completer']
      self.assertEqual(expected_completer(), actual_completer())

  @parameterized.named_parameters(
      ('Flags', 'flags'),
      ('GRI', 'gri'))
  def testComplete(self, style):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    self.PatchBookResourceReturnTypes()
    parent_name = 'projects/exampleproject/shelves/s0'
    self.mock_client.projects_shelves_books.List.return_value = (
        self.BuildBooksList(['{}/books/b0'.format(parent_name),
                             '{}/books/b1'.format(parent_name)]))
    expected_results = ['b0', 'b1']
    self.RunResourceCompleter(
        self.resource_spec_auto_completers,
        'book',
        presentation_name='--book',
        dest='book',
        args={'--book-project': 'exampleproject',
              '--shelf': 's0'},
        flag_name_overrides={'project': '--book-project'},
        expected_completions=expected_results)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['b0 --shelf=s0', 'b1 --shelf=s1']),
      ('GRI', 'gri', ['b0:s0', 'b1:s1']))
  def testCompleteWithUpdates(self, style, expected_results):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    self.PatchBookResourceReturnTypes()
    parent_name = 'projects/exampleproject'
    self.mock_client.projects_shelves.List.return_value = self.BuildShelvesList(
        ['{}/shelves/s0'.format(parent_name),
         '{}/shelves/s1'.format(parent_name)])
    self.mock_client.projects_shelves_books.List.side_effect = [
        self.BuildBooksList(['{}/shelves/s0/books/b0'.format(parent_name)]),
        self.BuildBooksList(['{}/shelves/s1/books/b1'.format(parent_name)])]

    self.RunResourceCompleter(
        self.resource_spec_auto_completers,
        'book',
        presentation_name='--book',
        dest='book',
        args={'--book-project': 'exampleproject'},
        flag_name_overrides={'project': '--book-project'},
        expected_completions=expected_results)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['b0 --book-project=p0', 'b1 --book-project=p1']),
      ('GRI', 'gri', ['b0:exampleshelf:p0', 'b1:exampleshelf:p1']))
  def testCompleteWithGivenMiddleArgAndUpdates(self, style, expected_results):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self.UnsetProject()
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    self.PatchBookResourceReturnTypes()
    self.mock_client.projects.List.return_value = self.BuildProjectsList(
        ['projects/p0', 'projects/p1'])
    self.mock_client.projects_shelves_books.List.side_effect = [
        self.BuildBooksList(['projects/p0/shelves/exampleshelf/books/b0']),
        self.BuildBooksList(['projects/p1/shelves/exampleshelf/books/b1'])]

    self.RunResourceCompleter(
        self.resource_spec_auto_completers,
        'book',
        presentation_name='--book',
        dest='book',
        args={'--shelf': 'exampleshelf'},
        flag_name_overrides={'project': '--book-project'},
        expected_completions=expected_results)

  @parameterized.named_parameters(
      ('Flags', 'flags', ['b0 --book-project=p0', 'b1 --book-project=p1'],
       {'project': '--book-project'}),
      ('GRI', 'gri', ['b0:exampleshelf:p0', 'b1:exampleshelf:p1'],
       {'project': '--book-project'}),
      ('NoOverridesFlags', 'flags', ['b0 --project=p0', 'b1 --project=p1'],
       {}),
      ('NoOverridesGRI', 'gri', ['b0:exampleshelf:p0', 'b1:exampleshelf:p1'],
       {}))
  def testCompleteWithStaticArgAndUpdates(self, style, expected_results,
                                          flag_name_overrides):
    properties.VALUES.core.enable_gri.Set(True)
    properties.VALUES.core.resource_completion_style.Set(style)
    self.UnsetProject()
    # Completer should still work and build updates if there is no list method
    # for the --shelf argument.
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    self._PatchProjectReturnType()
    self._PatchBookReturnType()
    self.mock_client.projects.List.return_value = self.BuildProjectsList(
        ['projects/p0', 'projects/p1'])
    self.mock_client.projects_shelves_books.List.side_effect = [
        self.BuildBooksList(['projects/p0/shelves/exampleshelf/books/b0']),
        self.BuildBooksList(['projects/p1/shelves/exampleshelf/books/b1'])]

    self.RunResourceCompleter(
        self.resource_spec_auto_completers,
        'book',
        presentation_name='--book',
        dest='book',
        args={'--shelf': 'exampleshelf'},
        flag_name_overrides=flag_name_overrides,
        expected_completions=expected_results)

  def testCompleterIsNoneIfNoMethod(self):
    collections = [
        ('cloudresourcemanager.projects', True),
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    self._PatchProjectReturnType()
    self._PatchBookReturnType()
    self.assertIsNone(completers.CompleterForAttribute(
        self.resource_spec_auto_completers,
        'shelf'))

  def testCompleterWithArbitraryArgFallthrough(self):
    collections = [
        ('example.projects.shelves.books', True),
        ('example.projects.shelves', True),
        ('cloudresourcemanager.projects', True)]
    self.MockGetListCreateMethods(*collections)
    self.PatchBookResourceReturnTypes()
    parent_name = 'projects/exampleproject/shelves/s0'
    self.mock_client.projects_shelves_books.List.return_value = (
        self.BuildBooksList(['{}/books/b0'.format(parent_name),
                             '{}/books/b1'.format(parent_name)]))
    resource_spec = util.GetBookResource()
    resource_spec.attributes[1].fallthroughs.append(
        deps.ArgFallthrough('--other'))

    expected_results = ['b0', 'b1']
    self.RunResourceCompleter(
        resource_spec,
        'book',
        presentation_name='--book',
        dest='book',
        args={'--book-project': 'exampleproject',
              '--other': 's0'},
        flag_name_overrides={'project': '--book-project'},
        expected_completions=expected_results)


if __name__ == '__main__':
  test_case.main()
