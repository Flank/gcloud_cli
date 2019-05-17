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

"""Tests all registered YAML commands in gcloud.

This module loads up a full gcloud CLI tree and loads all YAML commands it
finds. For each command, it runs a suite of tests against the specification
to catch common errors. This test suite should cover anything about a command
that can be statically analyzed.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import sys

from apitools.base.protorpclite import messages as _messages
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from googlecloudsdk.command_lib.util.apis import yaml_command_translator

from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import pkg_resources
import surface
from tests.lib import cli_test_base
from tests.lib import parameterized

import jsonschema
import six


class Validator(object):
  """A validator for an individual command."""

  def __init__(self, schema, path, command_data):
    """Constructs the validator.

    Args:
      schema: The parsed json yaml schema.
      path: [str], The path parts of the command name.
      command_data: The parsed yaml command data.
    """
    self.schema = schema
    self.path = path
    self.tracks_label = '/'.join(command_data.get('release_tracks', []))
    self.command_data = command_data
    self.builder = None
    self.errors = []
    self.fake_resource_ref = None

  def _SetBuilder(self, builder):
    self.builder = builder
    request_collection = self.builder.method.request_collection
    if request_collection:
      self.fake_resource_ref = resources.REGISTRY.Parse(
          'a',
          collection=request_collection.full_name,
          api_version=request_collection.api_version,
          params={p: 'a' for p in request_collection.detailed_params})

  def E(self, section, message, *args):
    """Logs an error.

    Args:
      section: str, The schema section the error occurred in.
      message: str, The error message potentially with format strings.
      *args: The strings to template into the error message.
    """
    if args:
      message = message.format(*args)
    self.errors.append(
        'In section [{}] for tracks [{}]: {}'.format(
            section, self.tracks_label, message))

  def _GetFieldFromMessage(self, message, field_path, section):
    """Digs into the given message to extract the dotted field.

    If the field does not exist, and error is logged.

    Args:
      message: The apitools message to dig into.
      field_path: str, The dotted path of attributes and sub-attributes.
      section: str, The schema section being process (for error reporting).

    Returns:
      The Field or None if that attribute does not exist.
    """
    if not field_path:
      return None
    try:
      return arg_utils.GetFieldFromMessage(message, field_path)
    except arg_utils.UnknownFieldError as e:
      self.E(section, str(e))
      return None

  def Validate(self):
    """Performs all validations."""
    if not self.ValidateSchema():
      self.E('GLOBAL', 'Skipping additional validation because command does not'
                       ' match schema.')
      return

    builder = self.ValidateBuild()
    if not builder:
      self.E(
          'GLOBAL',
          'Skipping additional validation because command could not be built.')
      return
    self._SetBuilder(builder)
    self.ValidateRequestSection()
    self.ValidateResponseSection()
    self.ValidateAsyncSection()
    self.ValidateArgumentsSection()
    self.ValidateInput()

  def ValidateSchema(self):
    try:
      jsonschema.validate(self.command_data, self.schema)
      return True
    # pylint: disable=broad-except, We are just logging it here.
    except Exception as e:
      self.E('GLOBAL', 'Schema validation failed: ' + str(e))
      return False

  def ValidateBuild(self):
    try:
      # Implicitly ensures that all python hooks are valid.
      spec = yaml_command_schema.CommandData(self.path[-1], self.command_data)
      # The ensures that the api collection, version, and method are all valid.
      c = yaml_command_translator.CommandBuilder(spec, ['abc', 'xyz', 'list'])
      c.Generate()
      return c
    # pylint: disable=broad-except, We are just logging it here.
    except Exception as e:
      self.E('GLOBAL', 'Command loading failed: ' + str(e))

  def ValidateRequestSection(self):
    self._CheckResourceMethodParams()
    self._CheckStaticFields()
    # TODO(b/64147277): Check that hooks have the right method signature.

  def _CheckResourceMethodParams(self):
    params = self.builder.spec.request.resource_method_params
    if self.builder.method.request_collection:
      method_params = self.builder.method.request_collection.params
      # For create commands we want to account for query params as well
      method_query_params = self.builder.method.query_params
      ref_params = (
          self.builder.method.resource_argument_collection.detailed_params)
      for param, ref_param in six.iteritems(params):
        if param not in method_params + method_query_params:
          self.E('request.resource_method_params',
                 'Parameter [{}] does not exist on API method', param)
        if ref_param not in ref_params:
          self.E('request.resource_method_params',
                 'Resource reference parameter [{}] does not exist on resource '
                 'reference', ref_param)

  def _CheckStaticFields(self):
    request_type = self.builder.method.GetRequestType()
    for field in self.builder.spec.request.static_fields.keys():
      self._GetFieldFromMessage(request_type, field, 'request.static_fields')

  def ValidateResponseSection(self):
    response_type = self.builder.method.GetEffectiveResponseType()
    self._GetFieldFromMessage(
        response_type, self.builder.spec.response.result_attribute,
        'response.result_attribute')

    self._GetFieldFromMessage(
        response_type, self.builder.spec.response.id_field,
        'response.id_field')

    self._CheckErrorFields()

  def _CheckErrorFields(self):
    error = self.builder.spec.response.error
    if not error:
      return

    response_type = self.builder.method.GetEffectiveResponseType()
    error_field = self._GetFieldFromMessage(
        response_type, error.field, 'error.field')
    if not error_field:
      return

    for section, f in six.iteritems({'error.code': error.code,
                                     'error.message': error.message}):
      self._GetFieldFromMessage(error_field.type, f, section)

  def ValidateAsyncSection(self):
    if not self.builder.spec.async:
      return

    try:
      # Checks that the method is valid.
      poller = yaml_command_translator.AsyncOperationPoller(
          self.builder.spec, self.fake_resource_ref, None)
    except registry.Error as e:
      self.E('async.collection/api_version/method', '{}', e)
      return

    self._GetFieldFromMessage(
        self.builder.method.GetEffectiveResponseType(),
        self.builder.spec.async.response_name_field,
        'async.response_name_field')

    self._CheckAsyncGetOperation(poller)
    self._CheckAsyncState(poller)
    self._CheckResourceExtraction(poller)

  def _CheckAsyncGetOperation(self, poller):
    asynchronous = self.builder.spec.async
    method_params = poller.method.request_collection.params
    poller_request_params = poller.method.request_collection.detailed_params
    operation_ref = resources.REGISTRY.Parse(
        'a',
        params={p: 'a' for p in poller_request_params},
        collection=asynchronous.collection)
    ref_params = list(operation_ref.AsDict().keys())
    for param, ref_param in (
        six.iteritems(asynchronous.operation_get_method_params)):
      if param not in method_params:
        self.E('async.operation_get_method_params',
               'Parameter [{}] does not exist on API method', param)
      if ref_param not in ref_params:
        self.E('async.operation_get_method_params',
               'Resource reference parameter [{}] does not exist on resource '
               'reference', ref_param)

  def _CheckAsyncState(self, poller):
    asynchronous = self.builder.spec.async
    op_response = poller.method.GetEffectiveResponseType()
    for section, f in six.iteritems({
        'async.response_name_field': asynchronous.response_name_field,
        'async.state.field': asynchronous.state.field,
        'async.error.field': asynchronous.error.field}):
      self._GetFieldFromMessage(op_response, f, section)

    # Check that success and error fields are mutually exclusive.
    if (set(asynchronous.state.success_values) &
        set(asynchronous.state.error_values)):
      self.E('async.state.success_values/error_values',
             'Collections contain overlapping values')

  def _CheckResourceExtraction(self, poller):
    asynchronous = self.builder.spec.async
    if not asynchronous.extract_resource_result:
      return

    try:
      self._GetFieldFromMessage(
          poller._ResourceGetMethod().GetEffectiveResponseType(),
          asynchronous.result_attribute, 'async.result_attribute')
    except registry.Error as e:
      self.E('async.resource_get_method', '{}', e)
      return

  def ValidateArgumentsSection(self):
    self._CheckArgumentsResource()
    self._CheckArguments(self.builder.spec.arguments.params)
    self._CheckNoUnusedArguments(self.builder.spec.arguments.params)

  def _CheckArgumentsResource(self):
    # Resource parameters are validated when the command generator is
    # constructed.
    request_collection = self.builder.method.request_collection
    if (request_collection and request_collection.params and
        not (self.builder.spec.arguments.resource or
             self.builder.spec.arguments.additional_arguments_hook or
             self.builder.spec.request.disable_resource_check)):
      # Currently, an additional_arguments_hook is the only way to workaround
      # declarative limitation of only one resource arg per command. However,
      # using such a hook means that a resource argument will not be defined in
      # the yaml spec itself so this check here is best is approximation for
      # insuring that resource args are fully specified in the command. E.g:
      # 'If request requires a resource AND that resource has params AND
      # neither an explicit resource arg OR additional argument hook
      # [which should provide resource params] is defined in yaml, then
      # FAIL with an error.'
      self.E('arguments.resource',
             'API collection [{}] has resource parameters but no resource spec '
             'was provided.', self.builder.method.request_collection.name)

  def _CheckArguments(self, arguments):
    request_type = self.builder.method.GetRequestType()
    for arg in arguments:
      if isinstance(arg, yaml_command_schema.ArgumentGroup):
        self._CheckArguments(arg.arguments)
      else:
        self._CheckArgument(arg, 'arguments.params')
        field = self._GetFieldFromMessage(
            request_type, arg.api_field, 'arguments.params')
        if field:
          if arg.choices and field.variant == _messages.Variant.ENUM:
            for choice in arg.choices:
              try:
                arg_utils.ChoiceToEnum(choice.enum_value, field.type)
              except KeyError:
                self.E('arguments.params.choices',
                       'The enum value [{}] for choice [{}] for argument [{}] '
                       'does not exist.',
                       choice.enum_value, choice.arg_value, arg.arg_name)

  def _CheckArgument(self, arg, section):
    expr = re.compile(r'[a-z][a-z\-]+')
    if not expr.match(arg.arg_name):
      self.E(section,
             'Argument [{}] does not match style guidelines', arg.arg_name)

  def _CheckNoUnusedArguments(self, arguments):
    """Checks for unused arguments (may have false negatives)."""
    params_without_api_field = []
    for param in arguments:
      if isinstance(param, yaml_command_schema.ArgumentGroup):
        self._CheckNoUnusedArguments(param.arguments)
      elif param.api_field is None:
        params_without_api_field.append(param)
    arguments_hook = self.builder.spec.arguments.additional_arguments_hook
    modify_request_hooks = [
        any(self.builder.spec.request.modify_request_hooks),
        self.builder.spec.request.create_request_hook,
        self.builder.spec.request.issue_request_hook
    ]
    modify_response_hooks = self.builder.spec.response.modify_response_hooks

    unmapped_arguments = (params_without_api_field or arguments_hook)
    if (unmapped_arguments and not any(modify_request_hooks)
        and not any(modify_response_hooks)):
      msg = ('Command has {} but no {{modify,create,issue}}_request_hook or '
             'modify_response_hooks. These arguments are unused.')
      reasons = []
      if params_without_api_field:
        reasons.append('parameters with no api_field ([{}])'.format(
            ', '.join([p.arg_name for p in params_without_api_field])))
      if arguments_hook:
        reasons.append('an additional_arguments_hook')
      reason = ' and '.join(reasons)
      self.E('arguments.params', msg.format(reason))

  def ValidateInput(self):
    self._CheckConfirmationPrompt()

  def _CheckConfirmationPrompt(self):
    """Ensures prompt format string attributes all exist in the resource ref."""
    prompt = self.builder.spec.input.confirmation_prompt
    if not prompt:
      return
    try:
      self.builder._Format(prompt, self.fake_resource_ref)
    except KeyError as e:
      self.E(
          'input.confirmation_prompt',
          'Confirmation prompt contains key [{}] not found as an attribute of '
          'the resource reference.', e.message)


class _GlobalDataHolder(object):
  """A global data holder for the auto-generated tests.

  This is not best practice, but is the only reasonable way we can have a test
  generated for each YAML command we want to validate. The general approach is
  to search the surface tree for all implementations and compile a list of all
  those that exist while this module is being loaded. That allows us to use
  that list of commands as the seed to parameterize the test in the next class.

  We can't do this during test run time, because once tests are running, pytest
  has already loaded the test suite and further modifying it does not have any
  effect. It must be modified during module load time.
  """
  SCHEMA = yaml.load(pkg_resources.GetResourceFromFile(
      os.path.join(os.path.dirname(yaml_command_schema.__file__),
                   'yaml_command_schema.yaml')))

  COMMANDS = []
  surface = os.path.dirname(surface.__file__)
  prefix_len = len(surface)
  for root, dirs, files in os.walk(surface):
    for f in files:
      if f.endswith('.yaml') and f != '__init__.yaml':
        file_path = os.path.join(root, f)
        # Chop off the surface directory (plus extra '/') and the .yaml
        # extension.
        path = (file_path[prefix_len + 1:-5]
                .replace('/', '.').replace('\\', '.').split('.'))
        COMMANDS.append((path, file_path))


class StubTranslator(command_loading.YamlCommandTranslator):
  """Implements the YAML translator but just constructs a validator."""

  def Translate(self, path, command_data):
    return Validator(_GlobalDataHolder.SCHEMA, path, command_data)


class YAMLCommandTests(cli_test_base.CliTestBase, parameterized.TestCase):
  """Global validation tests for yaml commands."""

  @parameterized.named_parameters(
      [('_' + '_'.join(path), path, file_path)
       for (path, file_path) in _GlobalDataHolder.COMMANDS])
  def testCommand(self, path, file_path):
    # There are potentially several implementations for different release tracks
    # in the same file.
    impls = command_loading._GetAllImplementations(
        [file_path], path, None, True, StubTranslator())
    for func, _ in impls:
      validator = func()
      validator.Validate()

      if validator.errors:
        for e in validator.errors:
          sys.__stderr__.write(e + '\n')
        self.fail('Validator failed.')

  def testEmptyArgumentGroupParams(self):
    data = {
        'help_text': {
            'brief': 'help',
            'description': 'Help.',
        },
        'request': {
            'collection': 'foo.instances',
        },
        'response': {},
        'arguments': {
            'params': [
                {
                    'required': True,
                    'mutex': True,
                    'params': [],  # No params is an error.
                },
            ],
        },
        'input': {
            'confirmation_prompt': 'asdf',
        },
        'output': {
            'format': 'yaml',
        },
    }
    with self.assertRaises(jsonschema.ValidationError):
      jsonschema.validate(data, _GlobalDataHolder.SCHEMA)

  def testSingletonArgumentGroupParams(self):
    data = {
        'help_text': {
            'brief': 'help',
            'description': 'Help.',
        },
        'request': {
            'collection': 'foo.instances',
        },
        'arguments': {
            'params': [
                {
                    'group': {
                        'required': True,
                        'mutex': True,
                        'params': [
                            {
                                'help_text': 'a-help',
                                'api_field': 'aaa',
                                'arg_name': 'a',
                            },
                        ],
                    },
                },
            ],
        },
        'input': {
            'confirmation_prompt': 'asdf',
        },
        'output': {
            'format': 'yaml',
        },
    }
    jsonschema.validate(data, _GlobalDataHolder.SCHEMA)


if __name__ == '__main__':
  cli_test_base.main()
