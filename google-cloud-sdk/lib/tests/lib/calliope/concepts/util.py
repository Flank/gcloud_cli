# -*- coding: utf-8 -*- #
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
"""Utils for testing the Calliope concepts library.

Used for tests.lib.calliope.concepts.concepts_test_base.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import properties
import six


def MakeAttributeConfigs(with_completers=False, attribute_names=None):
  """Makes default attribute configs for the test book resource."""
  attribute_names = attribute_names or ['projectsId', 'shelvesId', 'booksId']
  project_completer = None
  shelf_completer = None
  book_completer = None
  case_completer = None
  org_completer = None
  if with_completers:
    project_completer = MockProjectCompleter
    shelf_completer = MockShelfCompleter
    book_completer = MockBookCompleter
    case_completer = MockCaseCompleter
    org_completer = MockOrgCompleter
  attribute_config_dict = {
      'projectsId': concepts.ResourceParameterAttributeConfig(
          name='project',
          help_text='The Cloud Project of the {resource}.',
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.core.project)],
          completer=project_completer),
      'shelvesId': concepts.ResourceParameterAttributeConfig(
          name='shelf',
          help_text='The shelf of the {resource}. Shelves hold books.',
          completer=shelf_completer),
      'booksId': concepts.ResourceParameterAttributeConfig(
          name='book',
          help_text='The book of the {resource}.',
          completer=book_completer),
      'casesId': concepts.ResourceParameterAttributeConfig(
          name='case',
          help_text='The bookcase of the {resource}.',
          completer=case_completer),
      'organizationsId': concepts.ResourceParameterAttributeConfig(
          name='organization',
          help_text='The Cloud Organization of the {resource}.',
          completer=org_completer)}
  return {k: v for k, v in six.iteritems(attribute_config_dict)
          if k in attribute_names}


def _GetFakeResource(collection_name, name, attribute_names=None,
                     with_completers=False, auto_completers=False):
  return concepts.ResourceSpec(
      collection_name,
      name,
      disable_auto_completers=not auto_completers,
      **MakeAttributeConfigs(
          attribute_names=attribute_names,
          with_completers=with_completers))


def GetBookResource(name='book', with_completers=False, auto_completers=False):
  """Makes the test book resource."""
  return _GetFakeResource(
      'example.projects.shelves.books',
      name,
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetProjShelfResource(name='shelf', with_completers=False,
                         auto_completers=False):
  """Makes the test shelf resource."""
  return _GetFakeResource(
      'example.projects.shelves',
      name,
      attribute_names=['projectsId', 'shelvesId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetProjCaseBookResource(name='book', with_completers=False,
                            auto_completers=False):
  """Makes the test book resource."""
  return _GetFakeResource(
      'example.projects.cases.books',
      name,
      attribute_names=['projectsId', 'casesId', 'booksId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetOrgCaseBookResource(name='book', with_completers=False,
                           auto_completers=False):
  """Makes the test book resource."""
  return _GetFakeResource(
      'example.organizations.cases.books',
      name,
      attribute_names=['organizationsId', 'casesId', 'booksId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetOrgShelfBookResource(name='book', with_completers=False,
                            auto_completers=False):
  """Makes the test book resource."""
  return _GetFakeResource(
      'example.organizations.shelves.books',
      name,
      attribute_names=['organizationsId', 'shelvesId', 'booksId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetOrgShelfResource(name='shelf', with_completers=False,
                        auto_completers=False):
  """Makes the test shelf resource."""
  return _GetFakeResource(
      'example.organizations.shelves',
      name,
      attribute_names=['organizationsId', 'shelvesId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


def GetOrgCaseResource(name='shelf', with_completers=False,
                       auto_completers=False):
  """Makes the test shelf resource."""
  return _GetFakeResource(
      'example.organizations.cases',
      name,
      attribute_names=['organizationsId', 'casesId'],
      with_completers=with_completers,
      auto_completers=auto_completers)


class MockProjectCompleter(completers.ListCommandCompleter):

  def __init__(self):
    super(MockProjectCompleter, self).__init__(
        collection='example.projects',
        list_command='example.projects.list')


class MockShelfCompleter(completers.ListCommandCompleter):

  def __init__(self):
    super(MockShelfCompleter, self).__init__(
        collection='example.projects.shelves',
        list_command='example.projects.shelves.list')


class MockBookCompleter(completers.ListCommandCompleter):

  def __init__(self):
    super(MockBookCompleter, self).__init__(
        collection='example.projects.shelves.books',
        list_command='example.projects.shelves.books.list')


class MockCaseCompleter(completers.ListCommandCompleter):

  def __init__(self):
    super(MockCaseCompleter, self).__init__(
        collection='example.projects.cases',
        list_command='example.projects.cases.list')


class MockOrgCompleter(completers.ListCommandCompleter):

  def __init__(self):
    super(MockOrgCompleter, self).__init__(
        collection='example.organizations',
        list_command='example.organizations.list')
