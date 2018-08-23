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

"""Unit test mixin for resource completers.

Completers for resources with required parameters require the completion cache.
The mixin handles args and CLI mocks for testing. To test the completers in
api_lib.foo.completers:

  # Define the mocked list command output in a dict indexed by the dotted
  # command path.
  COMMAND_RESOURCES = {
    'foo.instances.list': [
        'https://...',
        'https://...',
    ],
  }

  # OR define the mocked resources search output in a dict indexed by
  # collection.
  SEARCH_RESOURCES = {
    'foo.instances': [
        'https://...',
        'https://...',
    ],
  }

  # Mix in the completer_test_base.CompleterBase base class.
  class FooCompleterTest(completer_test_base.CompleterBase):

    def testFooCompleter(self):
      # Instantiate a completer object with optional args dict. The args
      # provide default values for underspecified resouirce parameters.
      completer = self.Completer(foo.completers.FooCompleter,
                                 args={'project': 'my_project'},
                                 command_resources=COMMAND_RESOURCES,
                                 search_resources=SEARCH_RESOURCES)

      # Get the completions matching prefix.
      completions = completer.Complete(prefix, self.parameter_info)

      # Get the completions matching another prefix.
      completions = completer.Complete(another_prefix, self.parameter_info)

  # To test the completer attached to an arg in a command.
    def testFooArgHasBarCompleter(self):
      self.AssertCommandArgCompleter(
        command='surface subcommand',
        arg='instance',  # OR '--foo-flag'
        module_path='command_lib.surface.completers.BarCompleter')
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.api_lib.util import resource_search
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_filter
from tests.lib.core import core_completer_test_base

import six


class CompleterBase(core_completer_test_base.CoreCompleterBase):
  """Base class for testing completers."""

  def SetUp(self):
    self.calls = None
    self.completer = None
    self.parsed_args = core_completer_test_base.MockNamespace({
        '--project': 'default-x-project',
    })

  def AssertCommandArgCompleter(self, command, arg, module_path):
    """Checks that arg in command line has completer module_path."""

    # find and verify the cli entry for command
    cmd = self.cli._TopElement()  # pylint: disable=protected-access
    for part in command.split():
      cmd = cmd.LoadSubElement(part)
      if not cmd:
        self.fail(
            '[{part}] is not a valid group or command in [{command}].'.format(
                part=part, command=command))

    # find and verify the arg within command
    if arg.startswith('--'):
      args = cmd.ai.flag_args
    else:
      args = cmd.ai.positional_args
    actual_arg = None
    for a in args:
      if arg == (a.option_strings[0] if a.option_strings else a.dest):
        actual_arg = a
        break
    if not actual_arg:
      self.fail(
          'Command [{command}] does not have a [{arg}] argument {dests}.'.
          format(command=command, arg=arg, dests=[a.dest for a in args]))
    if getattr(actual_arg, 'completer', None):
      completer_class = actual_arg.completer._completer_class  # pylint: disable=protected-access
      path = completer_class.__module__
      actual_module_path = '.'.join([path.split('.', 1)[1],
                                     completer_class.__name__])
    else:
      actual_module_path = None
    if module_path != actual_module_path:
      self.fail('Expected completer [{module_path}] for arg [{arg}] in '
                'command [{command}], got [{actual_module_path}].'.format(
                    module_path=module_path,
                    arg=arg,
                    command=command,
                    actual_module_path=actual_module_path))

  def Resources(self, args=None, cli=None, command_resources=None,
                search_resources=None, command_only=False, handler_info=None):
    """Sets up resources and mocks for completer tests."""
    self.parsed_args = core_completer_test_base.MockNamespace(
        args=args,
        cli=cli,
        command_resources=command_resources,
        command_only=command_only,
        handler_info=handler_info)
    self.calls = self.parsed_args._calls  # pylint: disable=protected-access

    if search_resources:
      def _ResourceSearchList(limit=None, page_size=None, query=None,
                              sort_by=None, uri=False):
        """resource_search.list mock."""

        del limit, page_size, sort_by, uri
        results = None
        select_resource = resource_filter.Compile(query).Evaluate
        for name, value in six.iteritems(search_resources):
          if select_resource({'@type': name}):
            if results is None:
              results = []
            results += value
        if results is None:
          raise resource_search.CollectionNotIndexed(
              'Collection [{}] not indexed for search.'.format(query))
        return results

      self.StartObjectPatch(
          resource_search, 'List', side_effect=_ResourceSearchList)

  def Completer(self, completer_class, args=None, cli=None, command_only=False,
                command_resources=None, search_resources=None, cache=True,
                handler_info=None):
    if cache:
      completer = completer_class(cache=self.cache)
    else:
      completer = completer_class()
    dest = 'id'
    args_with_common_instance = {dest: None}
    if args:
      args_with_common_instance.update(args)
    self.Resources(args=args_with_common_instance,
                   cli=cli,
                   command_only=command_only,
                   command_resources=command_resources,
                   search_resources=search_resources,
                   handler_info=handler_info)
    self.parameter_info = completer.ParameterInfo(
        self.parsed_args, self.parsed_args.GetPositionalArgument(dest))
    return completer

  def RunCompleter(self, completer_class, expected_command=None,
                   prefix='', expected_completions=None, args=None,
                   cli=None, command_only=False, command_resources=None,
                   search_resources=None, cache=True, info=True,
                   handler_info=None):
    """Runs a completer and checks the commands and completions."""
    if info:
      log.SetVerbosity(logging.INFO)
    completer = self.Completer(
        completer_class, args=args, cli=cli, command_only=command_only,
        command_resources=command_resources, search_resources=search_resources,
        cache=cache, handler_info=handler_info)
    completions = completer.Complete(prefix, self.parameter_info)
    actual_commands = self.parsed_args.MockGetCommands()
    self.assertEqual(expected_command, actual_commands)
    if expected_completions or completions != ['']:
      six.assertCountEqual(self, expected_completions or [], completions)


class FlagCompleterBase(CompleterBase):
  """Base class for testing flag resource string completion style."""

  def SetUp(self):
    self.old_resource_completion_style = (
        properties.VALUES.core.resource_completion_style.Set('flags'))

  def TearDown(self):
    properties.VALUES.core.resource_completion_style.Set(
        self.old_resource_completion_style)


class GRICompleterBase(CompleterBase):
  """Base class for testing GRI resource string completion style."""

  def SetUp(self):
    self.old_resource_completion_style = (
        properties.VALUES.core.resource_completion_style.Set('gri'))

  def TearDown(self):
    properties.VALUES.core.resource_completion_style.Set(
        self.old_resource_completion_style)
