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

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import properties


def MakeAttributeConfigs(with_completers=False):
  """Makes default attribute configs for the test book resource."""
  return {
      'projectsId': concepts.ResourceParameterAttributeConfig(
          name='project',
          help_text='The Cloud Project of the {resource}.',
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.core.project)],
          completer=MockProjectCompleter if with_completers else None),
      'shelvesId': concepts.ResourceParameterAttributeConfig(
          name='shelf',
          help_text='The shelf of the {resource}. Shelves hold books.',
          completer=MockShelfCompleter if with_completers else None),
      'booksId': concepts.ResourceParameterAttributeConfig(
          name='book',
          help_text='The book of the {resource}.',
          completer=MockBookCompleter if with_completers else None)}


def GetBookResource(with_completers=False, auto_completers=False):
  """Makes the test book resource."""
  return concepts.ResourceSpec(
      'example.projects.shelves.books',
      'book',
      disable_auto_completers=not auto_completers,
      **MakeAttributeConfigs(with_completers=with_completers))


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
