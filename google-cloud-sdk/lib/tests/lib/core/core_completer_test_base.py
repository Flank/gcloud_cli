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

"""Unit test mixin for core resource completer unit tests."""

from __future__ import absolute_import
from __future__ import division

from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import log
from tests.lib import completer_test_data
from tests.lib import completion_cache_test_base

import six


_COMMAND_RESOURCES = {
    'compute.regions.list': completer_test_data.REGION_URIS,
    'compute.zones.list': completer_test_data.ZONE_URIS,
    'projects.list': completer_test_data.PROJECT_URIS,
}


class MockArgument(object):

  def __init__(self, name):
    self.name = name
    self.dest = parameter_info_lib.GetDestFromFlag(name)


class MockCommand(object):
  """Mock calliope Command."""

  def __init__(self, command_name):
    self._command_name = command_name
    self.ai = None

  def GetPath(self):
    return self._command_name


class MockNamespace(parser_extensions.Namespace):
  """Mocked parsed args Namespace."""

  def __init__(self, args=None, command_name='test', command_resources=None,
               cli=None, command_only=False, handler_info=None, **kwargs):
    self._calliope_command = MockCommand(command_name)
    self._cli = cli
    self._command_only = command_only
    parser = parser_extensions.ArgumentParser(
        add_help=False,
        prog=command_name,
        calliope_command=self._calliope_command)
    self._calliope_command.ai = parser_arguments.ArgumentInterceptor(parser)
    self._calls = {}
    self._commands = []
    self._command_resources = command_resources or {}
    self._handler_info = handler_info or {}
    dests = {}
    if args:
      for name, value in six.iteritems(args):
        self._calliope_command.ai.add_argument(name, help='Auxilio aliis.')
        dests[name.replace('-', '_').strip('_')] = value
    super(MockNamespace, self).__init__(**dests)

  def MockGetCalls(self):
    return self._calls

  def MockGetCommands(self):
    if not self._commands:
      return None
    elif len(self._commands) == 1:
      return self._commands[0]
    else:
      return self._commands

  def _GetCommand(self):
    return self._calliope_command

  def _Execute(self, command, call_arg_complete=False):
    """Mocks cache update command execution by indexing a mock results dict.

    The dotted command path and --flag=value args for the primary lookup key
    in self._command_resources.  If that fails then just the dotted command
    path is used.  Finally, if the command has an alpha or beta release track
    group as the first command path component then the dotted command path
    without that group is used.

    Args:
      command: The command path component list plust --flag=value args with
        leading 'gcloud' omitted.
      call_arg_complete: True if its OK to call arg completion. Ignored here
        because we are testing arg completion.

    Raises:
      ValueError: If there are no mocked resources for command.

    Returns:
      The list of mocked resources from the self._command_resources dict.
    """
    del call_arg_complete
    self._commands.append(command)
    if self._command_only:
      return
    common_flags = ['--format=disable', '--quiet', '--uri']
    # First try a key composed of command path and flags.
    key = '.'.join([arg for arg in command
                    if arg not in common_flags and '/' not in arg])
    resources = self._command_resources.get(key, _COMMAND_RESOURCES.get(key))
    if not resources:
      # Second try just the command path with no flags.
      key = '.'.join([arg for arg in command
                      if not arg.startswith('-') and '/' not in arg])
      resources = self._command_resources.get(key, _COMMAND_RESOURCES.get(key))
      if not resources and command[0] in ('alpha', 'beta'):
        # Finally try with no release track.
        key = '.'.join([arg for arg in command[1:]
                        if not arg.startswith('-') and '/' not in arg])
        resources = self._command_resources.get(
            key, self._command_resources.get(key))
      if not resources:
        if self._cli:
          # An e2e test or the caller mocked the API request/response.
          return self._cli.Execute(command, call_arg_complete=False)
        raise ValueError(
            'No mocked resources for command [{}].'.format(command))
    self._calls[key] = self._calls.get(key, 0) + 1
    if '--format=disable' not in command:
      # The list command produces parsable output.
      for item in resources:
        if isinstance(item, six.string_types):
          log.out.write(item + '\n')
    return resources

  @property
  def CONCEPTS(self):
    concept_info = self._handler_info

    class Concepts(object):

      def ArgNameToConceptInfo(self, arg_name):
        del arg_name
        return concept_info

    return Concepts()


class CoreCompleterBase(completion_cache_test_base.CompletionCacheBase):
  """Base class for testing core completers."""
