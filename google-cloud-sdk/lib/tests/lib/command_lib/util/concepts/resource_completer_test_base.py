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

"""Unit test mixin for resource argument completers.

The mixin handles some of the mocks for testing, including the projects list
API calls. To use this to test a completer on a certain resource spec (FooSpec)
and an attribute named 'bar':

  # Mock the API output using the test base for the API.
  class FooCopmleterTest(ResourceCompleterBase):

    def testFooCompleter(self):
      self.ExpectListBars(list_request, ListResponse(bars=['b0', 'b1'])

  # Call RunCompleter with the resource spec, the name of the attribute being
  # completed, the prefix, and the expected completions. Use projects kwarg
  # if the project needs to be completed as well, and args to represent
  # args that have already been parsed.
      properties.VALUES.core.project.Set(None)
      self.RunCompleter(
          FooSpec(), 'bar', args={},
          prefix='', projects=['p0'],
          expected_completions=[
              'b0 --project=p0', 'b1 --project=p0'])  # ['b0:p0', 'b1:p0']
                                                      # for GRI style.
      self.RunCompleter(
          FooSpec(), 'bar', args={'project': 'p0'},
          prefix='',
          expected_completions=['b0', 'b1'])

  # To test the completer attached to an arg in a command.
    def testFooArgHasResourceCompleter(self):
      self.AssertCommandArgResourceCopmleter(
        command='surface subcommand',
        arg='instance',  # OR '--foo-flag')
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.util.concepts import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from tests.lib import completer_test_base

import mock

_COMPLETER_MODULE_PATH = 'command_lib.util.concepts.completers.Completer'


class ResourceCompleterBase(completer_test_base.CompleterBase):
  """Mixin for testing resource arg auto-generated completers."""

  def SetUp(self):
    # Mock the projects client since it is used for many concepts.
    self.mock_projects_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=core_apis.GetClientInstance(
            'cloudresourcemanager', 'v1', no_http=True))
    self.mock_projects_client.Mock()
    self.addCleanup(self.mock_projects_client.Unmock)
    self.projects_messages = core_apis.GetMessagesModule(
        'cloudresourcemanager', 'v1')
    self.StartPatch('time.sleep')

  def AssertCommandArgResourceCompleter(self, command, arg):
    """Asserts that arg in command has a resource argument completer."""
    self.AssertCommandArgCompleter(command, arg, _COMPLETER_MODULE_PATH)

  def _ExpectListProjects(self, projects):
    """Add expected call and response for a projects list call."""
    self.mock_projects_client.projects.List.Expect(
        self.projects_messages.CloudresourcemanagerProjectsListRequest(
            filter='lifecycleState:ACTIVE'),
        self.projects_messages.ListProjectsResponse(
            projects=[
                self.projects_messages.Project(
                    projectId=p, name='name') for p in projects]))

  def RunResourceCompleter(self, resource_spec, attribute_name, prefix='',
                           expected_completions=None, args=None,
                           presentation_name=None, dest=None,
                           flag_name_overrides=None, projects=None):
    """Run a test of a resource completer.

    Args:
      resource_spec: googlecloudsdk.calliope.concepts.concepts.ResourceSpec,
        the resource spec.
      attribute_name: str, the name of the attribute.
      prefix: str, the value to be completed if any. Defaults to ''.
      expected_completions: [str], the list of expected results if any.
      args: {str: str}, a dict of args to be parsed into the mock namespace.
      presentation_name: str, the name of the presentation spec. Defaults to
        the resource name (i.e. a positional arg).
      dest: str, the name of the argument for which completion is running.
        Defaults to the name of the attribute.
      flag_name_overrides: {str: str} | None, the flag name overrides for the
        presentation spec, if any.
      projects: [str], a list of project IDs to be returned by a list projects
        call if the project argument needs to be completed. If None, no list
        projects call is expected.
    """
    args = args or {}
    flag_name_overrides = flag_name_overrides or {}
    presentation_name = presentation_name or resource_spec.name
    dest = dest or attribute_name
    expected_completions = expected_completions or []
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        presentation_name,
        resource_spec,
        'Help text',
        prefixes=False,
        flag_name_overrides=flag_name_overrides)
    resource_info = concept_parsers.ConceptParser([presentation_spec]).GetInfo(
        presentation_spec.name)
    if projects is not None:
      self._ExpectListProjects(projects)

    completer = self.Completer(
        completers.CompleterForAttribute(
            resource_spec,
            attribute_name),
        args=args,
        handler_info=resource_info,
        cli=self.cli)
    argument = mock.MagicMock(dest=dest)
    parameter_info = completer.ParameterInfo(self.parsed_args, argument)

    completions = completer.Complete(prefix, parameter_info)
    self.assertEqual(expected_completions, completions)
