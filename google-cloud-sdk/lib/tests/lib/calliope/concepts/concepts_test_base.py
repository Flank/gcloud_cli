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

"""Test base for the Calliope concepts library."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.calliope import util as calliope_util
from tests.lib.calliope.concepts import util
import six


class ConceptsTestBase(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):
  """Mixin for testing concepts library."""

  # TODO(b/66911840): Remove if and when strange test interactions with the
  # [core/project] property do not require multiple steps to unset.
  def UnsetProject(self):
    """Helper method to unset project."""
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)

  def SetUp(self):
    registry = resources.REGISTRY
    registry.registered_apis['example'] = ['v1']
    self.book_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'projects.shelves.books',
        'projects/{projectsId}/shelves/{shelvesId}/books/{booksId}',
        {'': 'projects/{projectsId}/shelves/{shelvesId}/books/{booksId}'},
        ['projectsId', 'shelvesId', 'booksId'])
    self.shelf_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'projects.shelves', 'projects/{projectsId}/shelves/{shelvesId}',
        {'': 'projects/{projectsId}/shelves/{shelvesId}'},
        ['projectsId', 'shelvesId'])
    self.project_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'projects', 'projects/{projectsId}', {'': 'projects/{projectsId}'},
        ['projectsId'])

    # pylint:disable=protected-access
    registry._RegisterCollection(self.book_collection)
    registry._RegisterCollection(self.shelf_collection)
    registry._RegisterCollection(self.project_collection)
    # pylint:enable=protected-access

    # Set up a sample argparse parser.
    command = calliope_util.MockCommand('command')
    argparser = parser_extensions.ArgumentParser(
        calliope_command=command)
    self.parser = parser_arguments.ArgumentInterceptor(
        parser=argparser,
        cli_generator=None,
        allow_positional=True)
    command.ai = self.parser

  def _GetMockNamespace(self, **kwargs):

    class MockNamespace(object):
      """A mock class to store the values of parsed args."""

      def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
          setattr(self, k, v)

    return MockNamespace(**kwargs)

  def _MakeAttributeConfigs(self, with_completers=False):
    """Makes default attribute configs."""
    return util.MakeAttributeConfigs(with_completers=with_completers)

  @property
  def resource_spec(self):
    """A basic resource spec for the fake "book" resource."""
    # Lazy creation allows checking of the GetCollectionInfo mock.
    return util.GetBookResource()

  @property
  def resource_spec_completers(self):
    """A basic resource spec for the fake "book" resource, with completers."""
    return util.GetBookResource(with_completers=True)

  @property
  def resource_spec_auto_completers(self):
    """A basic resource spec for the fake "book" resource with auto complete."""
    # Lazy creation allows checking of the GetCollectionInfo mock.
    return util.GetBookResource(auto_completers=True)

  def SetUpFallthroughSpec(self, return_value):
    def Fallthrough():
      return return_value
    return concepts.ResourceSpec(
        'example.projects.shelves.books',
        'project',
        projectsId=concepts.ResourceParameterAttributeConfig(
            name='project', help_text='Auxilio aliis.',
            fallthroughs=[deps.Fallthrough(Fallthrough, hint='hint')]),
        shelvesId=concepts.ResourceParameterAttributeConfig(
            name='shelf', help_text='Auxilio aliis.',
            fallthroughs=[deps.Fallthrough(Fallthrough, hint='hint')]),
        booksId=concepts.ResourceParameterAttributeConfig(
            name='book', help_text='Auxilio aliis.',
            fallthroughs=[deps.Fallthrough(Fallthrough, hint='hint')]))


class MultitypeTestBase(ConceptsTestBase):
  """Test base for testing with multitype concepts."""

  def SetUp(self):
    registry = resources.REGISTRY
    self.proj_case_book_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'projects.cases.books',
        'projects/{projectsId}/cases/{casesId}/books/{booksId}',
        {'': 'projects/{projectsId}/cases/{casesId}/books/{booksId}'},
        ['projectsId', 'casesId', 'booksId'])
    self.proj_case_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'projects.cases',
        'projects/{projectsId}/cases/{casesId}',
        {'': 'projects/{projectsId}/cases/{casesId}'},
        ['projectsId', 'casesId'])
    self.org_shelf_book_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'organizations.shelves.books',
        'organizations/{organizationsId}/shelves/{shelvesId}/books/{booksId}',
        {'':
         'organizations/{organizationsId}/shelves/{shelvesId}/books/{booksId}'},
        ['organizationsId', 'shelvesId', 'booksId'])
    self.org_shelf_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'organizations.shelves',
        'organizations/{organizationsId}/shelves/{shelvesId}',
        {'': 'organizations/{organizationsId}/shelves/{shelvesId}'},
        ['organizationsId', 'shelvesId'])
    self.organization_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'organizations', 'organizations/{organizationsId}',
        {'': 'organizations/{organizationsId}'},
        ['organizationsId'])
    self.org_case_book_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'organizations.cases.books',
        'organizations/{organizationsId}/cases/{casesId}/books/{booksId}',
        {'': 'organizations/{organizationsId}/cases/{casesId}/books/{booksId}'},
        ['organizationsId', 'casesId', 'booksId'])
    self.org_case_collection = resource_util.CollectionInfo(
        'example', 'v1', 'https://example.googleapis.com/v1/', '',
        'organizations.cases',
        'organizations/{organizationsId}/cases/{casesId}',
        {'': 'organizations/{organizationsId}/cases/{casesId}'},
        ['organizationsId', 'casesId'])

    for collection in [
        self.proj_case_book_collection,
        self.proj_case_collection,
        self.org_shelf_book_collection,
        self.org_shelf_collection,
        self.organization_collection,
        self.org_case_book_collection,
        self.org_case_collection]:
      registry._RegisterCollection(collection)  # pylint:disable=protected-access

  @property
  def four_way_resource(self):
    """A multitype concept spec with four types."""
    project_shelf_book_resource = util.GetBookResource(name='projectbook')
    organization_shelf_book_resource = util.GetOrgShelfBookResource(
        name='orgshelfbook')
    project_case_book_resource = util.GetProjCaseBookResource(
        name='projcasebook')
    organization_case_book_resource = util.GetOrgCaseBookResource(
        name='orgcasebook')
    return multitype.MultitypeConceptSpec(
        'book',
        project_shelf_book_resource,
        organization_shelf_book_resource,
        project_case_book_resource,
        organization_case_book_resource)
