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
"""Tests for the resource_parameter_info module."""

from __future__ import absolute_import
from __future__ import unicode_literals
import copy

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.command_lib.util.concepts import resource_parameter_info
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.command_lib.util.apis import base as apis_base
from tests.lib.core import core_completer_test_base
import mock


class ResourceParameterInfoTest(concepts_test_base.ConceptsTestBase,
                                apis_base.Base,
                                parameterized.TestCase):

  def SetUp(self):
    self.mock_client = mock.MagicMock()
    self.StartObjectPatch(apis, 'GetClientInstance',
                          return_value=self.mock_client)
    self.presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'a resource',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False)
    self.resource_info = concept_parsers.ConceptParser(
        [self.presentation_spec]).GetInfo(self.presentation_spec.name)

  def SetUpBookParameterInfo(self, args):
    """Creates ResourceParameterInfo for book resource.

    Args:
      args: {str: str}, dict of flag names to values for the mock namespace.

    Returns:
      resource_parameter_info.ResourceParameterInfo, the parameter info object.
    """
    ns = core_completer_test_base.MockNamespace(
        args=args,
        handler_info=self.resource_info)
    argument = mock.MagicMock(dest='book')
    parameter_info = resource_parameter_info.ResourceParameterInfo(
        self.resource_info, ns, argument)
    return parameter_info

  def testParameterInfo(self):
    parameter_info = self.SetUpBookParameterInfo(
        {'--book': 'examplebook',
         '--shelf': 'exampleshelf',
         '--book-project': 'exampleproject'})

    self.assertEqual(
        'examplebook',
        parameter_info.GetValue('booksId'))
    self.assertEqual(
        'exampleshelf',
        parameter_info.GetValue('shelvesId'))
    self.assertEqual(
        'exampleproject',
        parameter_info.GetValue('projectsId'))

  def testGetValue(self):
    collections = [
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)

    parameter_info = self.SetUpBookParameterInfo(
        {'--book': 'examplebook',
         '--shelf': 'exampleshelf',
         '--book-project': 'exampleproject'})

    self.assertEqual('examplebook', parameter_info.GetValue('booksId'))
    self.assertEqual('exampleshelf', parameter_info.GetValue('shelvesId'))
    self.assertEqual('exampleproject', parameter_info.GetValue('projectsId'))

  def testGetValueIncomplete(self):
    collections = [
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)

    parameter_info = self.SetUpBookParameterInfo(
        {'--shelf': 'exampleshelf',
         '--book-project': 'exampleproject'})

    self.assertEqual('exampleshelf', parameter_info.GetValue('shelvesId'))
    self.assertEqual('exampleproject', parameter_info.GetValue('projectsId'))

  @parameterized.named_parameters(
      ('FlagAlreadyPresent', 'projectsId', {'--book-project': 'exampleproject'},
       'fake-project', 'exampleproject', None),
      ('FlagFromProp', 'projectsId', {}, 'fake-project', None,
       '--book-project=fake-project'),
      ('NoFlagNoProp', 'shelvesId', {}, None, None, None))
  def testGetFlag(self, parameter_name, args, project_config, parameter_value,
                  expected_result):
    properties.VALUES.core.project.Set(project_config)
    collections = [
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    parameter_info = self.SetUpBookParameterInfo(args)

    flag = parameter_info.GetFlag(parameter_name,
                                  parameter_value=parameter_value)

    self.assertEqual(expected_result, flag)

  @parameterized.named_parameters(
      ('True', True, '--book'),
      ('False', False, None))
  def testGetFlagBoolean(self, return_value, expected_flag):
    collections = [
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    parameter_info = self.SetUpBookParameterInfo({})
    self.StartObjectPatch(parameter_info, 'GetValue', return_value=return_value)

    flag = parameter_info.GetFlag('booksId', parameter_value=None)

    self.assertEqual(expected_flag, flag)

  def testGetFlagProject(self):
    properties.VALUES.core.project.Set(self.Project())
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'a resource',
        flag_name_overrides={},
        prefixes=False)
    resource_info = concept_parsers.ConceptParser(
        [presentation_spec]).GetInfo(presentation_spec.name)
    ns = core_completer_test_base.MockNamespace(
        args={},
        handler_info=resource_info)
    argument = mock.MagicMock(dest='book')
    parameter_info = resource_parameter_info.ResourceParameterInfo(
        resource_info, ns, argument)
    flag = parameter_info.GetFlag('projectsId')
    self.assertEqual('--project={}'.format(self.Project()), flag)

  def testGetFlagNoFlag(self):
    properties.VALUES.core.project.Set(self.Project())
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'a resource',
        flag_name_overrides={'shelvesId': ''},
        prefixes=False)
    resource_info = concept_parsers.ConceptParser(
        [presentation_spec]).GetInfo(presentation_spec.name)
    ns = core_completer_test_base.MockNamespace(
        args={},
        handler_info=resource_info)
    argument = mock.MagicMock(dest='book')
    parameter_info = resource_parameter_info.ResourceParameterInfo(
        resource_info, ns, argument)
    flag = parameter_info.GetFlag('shelvesId')
    self.assertEqual(None, flag)

  def testGetFlagNoProject(self):
    self.UnsetProject()
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        self.resource_spec,
        'a resource',
        flag_name_overrides={},
        prefixes=False)
    resource_info = concept_parsers.ConceptParser(
        [presentation_spec]).GetInfo(presentation_spec.name)
    ns = core_completer_test_base.MockNamespace(
        args={},
        handler_info=resource_info)
    argument = mock.MagicMock(dest='book')
    parameter_info = resource_parameter_info.ResourceParameterInfo(
        resource_info, ns, argument)
    flag = parameter_info.GetFlag('projectsId')
    self.assertEqual(None, flag)

  @parameterized.named_parameters(
      ('Basic', 'booksId', None, 'book'),
      ('FlagRename', 'projectsId', None, 'book_project'),
      ('PrefixNotUsed', 'booksId', 'prefix', 'book'),
      ('NonexistentParam', 'pagesId', None, None))
  def testGetDest(self, parameter_name, prefix, expected_result):
    collections = [
        ('example.projects.shelves.books', True)]
    self.MockGetListCreateMethods(*collections)
    parameter_info = self.SetUpBookParameterInfo({})

    dest = parameter_info.GetDest(parameter_name, prefix=prefix)

    self.assertEqual(expected_result, dest)

  def testGetValueWithFallthrough(self):
    spec = copy.deepcopy(self.resource_spec)
    spec.attributes[0].fallthroughs = [
        deps.PropertyFallthrough(properties.VALUES.core.project)]
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        spec,
        'a resource',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False)
    resource_info = concept_parsers.ConceptParser(
        [presentation_spec]).GetInfo(presentation_spec.name)
    ns = core_completer_test_base.MockNamespace(
        args={},
        handler_info=resource_info)
    argument = mock.MagicMock(dest='book')

    parameter_info = resource_parameter_info.ResourceParameterInfo(
        resource_info, ns, argument)

    self.assertEqual(
        self.Project(),
        parameter_info.GetValue('projectsId'))

  @parameterized.named_parameters(
      ('PromptingEnabled', False),
      ('PromptingDisabled', True))
  def testGetValueWithPromptingFallthrough(self, current_value):
    properties.VALUES.core.disable_prompts.Set(current_value)
    spec = copy.deepcopy(self.resource_spec)

    def GetValue():
      return console_io.PromptResponse('value? >')
    spec.attributes[0].fallthroughs = [deps.Fallthrough(GetValue, 'hint')]
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        '--book',
        spec,
        'a resource',
        flag_name_overrides={'project': '--book-project'},
        prefixes=False)
    resource_info = concept_parsers.ConceptParser(
        [presentation_spec]).GetInfo(presentation_spec.name)
    ns = core_completer_test_base.MockNamespace(
        args={},
        handler_info=resource_info)
    argument = mock.MagicMock(dest='book')

    parameter_info = resource_parameter_info.ResourceParameterInfo(
        resource_info, ns, argument)

    self.assertEqual(
        None,
        parameter_info.GetValue('projectsId'))
    # Ensure that the property is restored after GetValue.
    self.assertEqual(current_value,
                     properties.VALUES.core.disable_prompts.GetBool())
    properties.VALUES.core.disable_prompts.Set(True)


if __name__ == '__main__':
  test_case.main()
