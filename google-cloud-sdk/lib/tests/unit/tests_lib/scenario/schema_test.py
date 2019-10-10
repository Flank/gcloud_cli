# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for the session module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.scenario import reference_resolver
from tests.lib.scenario import schema
from tests.lib.scenario import session
from tests.lib.scenario import test_base
from tests.lib.scenario import updates

import mock


class SchemaTests(sdk_test_base.WithOutputCapture,
                  sdk_test_base.WithTempCWD,
                  parameterized.TestCase):
  """Tests of schema actions."""

  def SetUp(self):
    temp_file = self.Touch(self.root_path)
    self.scenario_context = schema.ScenarioContext(
        None, temp_file, None, calliope_base.ReleaseTrack.GA, None, [], None,
        None, None)

  def testSetPropertyAction(self):
    a = schema.SetPropertyAction.FromData(
        {'set_property': {'project': 'foo', 'compute/zone': 'bar'}})
    a.Execute(self.scenario_context)
    self.assertEqual('foo', properties.VALUES.core.project.Get())
    self.assertEqual('bar', properties.VALUES.compute.zone.Get())

  def testWriteFileAction(self):
    a = schema.WriteFileAction.FromData(
        {'write_file': {'path': 'foo/bar.txt', 'contents': 'hello'}})
    a.Execute(self.scenario_context)
    self.AssertFileEquals('hello', 'foo/bar.txt')

  def testWriteFileActionBinary(self):
    a = schema.WriteFileAction.FromData(
        {'write_file': {'path': 'foo/bar.txt', 'binary_contents': b'hello'}})
    a.Execute(self.scenario_context)
    self.AssertBinaryFileEquals(b'hello', 'foo/bar.txt')

  def testWriteFileActionResolveResources(self):
    a = schema.WriteFileAction.FromData(
        {'write_file': {'path': 'foo/bar.txt', 'contents': 'hello $$object$$'}})
    self.scenario_context.resource_ref_resolver.AddGeneratedResourceId('object',
                                                                       'world')
    a.Execute(self.scenario_context)
    self.AssertFileEquals('hello world', 'foo/bar.txt')

  def testLoadResourceAction(self):
    a = schema.LoadResourceAction.FromData(
        {'load_resource':
             {'path': 'tests/unit/tests_lib/scenario/test_data/subdir'}})
    a.Execute(self.scenario_context)
    self.AssertFileEquals('This is some nested data.\n',
                          'subdir/another/data.txt')

  def testGenerateResourceIdAction(self):
    a = schema.GenerateResourceIdAction.FromData(
        {'generate_resource_id': {'reference': 'instance1',
                                  'prefix': 'compute-vm'}})
    a.Execute(self.scenario_context)
    resource_id = self.scenario_context.resource_ref_resolver._resource_ids[
        'instance1']
    self.assertTrue(resource_id.startswith('compute-vm'))

    self.scenario_context.resource_ref_resolver.RemoveGeneratedResourceId(
        'instance1')
    self.assertEqual(
        self.scenario_context.resource_ref_resolver._resource_ids, {})

  def testGenerateResourceIdActionNoCleanup(self):
    a = schema.GenerateResourceIdAction.FromData(
        {'generate_resource_id': {'reference': 'instance1',
                                  'prefix': 'compute-vm',
                                  'requires_cleanup': False}})
    a.Execute(self.scenario_context)
    self.assertNotIn(
        'instance1', self.scenario_context.resource_ref_resolver._resource_ids)
    resource_id = self.scenario_context.resource_ref_resolver._references[
        'instance1']
    self.assertTrue(resource_id.startswith('compute-vm'))

  def testResolveResourceReferences(self):
    for x in range(3):
      a = schema.GenerateResourceIdAction.FromData(
          {'generate_resource_id': {'reference': 'instance' + str(x),
                                    'prefix': 'compute-vm'}})
      a.Execute(self.scenario_context)

    data = {'execute_command': {
        'command': 'some command $$instance0$$ --flag=$$instance1$$ '
                   '$$instance2$$'}}
    resolved = self.scenario_context.resource_ref_resolver.Resolve(data)
    id_regex = r'compute-vm-\d+-\d+-\w+'
    self.assertRegexpMatches(
        resolved['execute_command']['command'],
        r'some command {id} --flag={id} {id}'.format(id=id_regex))
    self.assertEqual(
        3, len(self.scenario_context.resource_ref_resolver._resource_ids))

  def testReverseResolveResourceReferencesLongestFirst(self):
    rrr = reference_resolver.ResourceReferenceResolver()
    rrr.SetExtractedId('ref1', 'my-group-instance-subthing')
    rrr.SetExtractedId('ref2', 'my-group')
    rrr.SetExtractedId('ref3', 'my-group-instance')

    data = 'my-group-instance my-group my-group-instance-subthing'
    resolved = rrr.ReverseResolve(data)
    self.assertEqual(resolved, '$$ref3$$ $$ref2$$ $$ref1$$')

  @parameterized.parameters(
      (0, 0),
      (True, True),
      ('foo', 'foo'),
      ('$$i$$', 'FAKE'),
      ([0, 'foo', '$$i$$'], [0, 'foo', 'FAKE']),
      ({'a': {'b': [0, 'foo', '$$i$$'], 'c': '$$i$$', 'd': 'asdf $$i$$ asdf'},
        'e': [{'f': 'g', 'h': '$$i$$'}],
        'i': '$$i$$'},
       {'a': {'b': [0, 'foo', 'FAKE'], 'c': 'FAKE', 'd': 'asdf FAKE asdf'},
        'e': [{'f': 'g', 'h': 'FAKE'}],
        'i': 'FAKE'})
  )
  def testResolveResourceReferencesDataTypes(self, data, expected):
    def FakeNameGenerator(*args, **kwargs):
      del args
      del kwargs
      yield 'FAKE'
    self.StartObjectPatch(e2e_utils, 'GetResourceNameGenerator',
                          side_effect=FakeNameGenerator)

    a = schema.GenerateResourceIdAction.FromData(
        {'generate_resource_id': {'reference': 'i', 'prefix': 'compute-vm'}})
    a.Execute(self.scenario_context)

    resolved = self.scenario_context.resource_ref_resolver.Resolve(data)
    self.assertEqual(expected, resolved)

  def testResolveResourceReferencesError(self):
    a = schema.GenerateResourceIdAction.FromData(
        {'generate_resource_id': {'reference': 'instance1',
                                  'prefix': 'compute-vm'}})
    a.Execute(self.scenario_context)
    with self.assertRaisesRegex(
        reference_resolver.UnknownReferenceError,
        r'Unknown reference \[Line: \?, Col: \?\]: \[instance0\]'):
      self.scenario_context.resource_ref_resolver.Resolve(
          'some command $$instance0$$')

  def testDefineReference(self):
    a1 = schema.DefineReferenceAction.FromData(
        {'define_reference': {
            'reference': 'foo', 'value': 'a', 'track_values': {'ALPHA': 'b'}}})
    a2 = schema.DefineReferenceAction.FromData(
        {'define_reference': {
            'reference': 'bar', 'value': 'a', 'track_values': {'GA': 'b'}}})
    a3 = schema.DefineReferenceAction.FromData(
        {'define_reference': {
            'reference': 'baz', 'track_values': {'ALPHA': 'b'}}})
    a4 = schema.DefineReferenceAction.FromData(
        {'define_reference': {
            'reference': 'empty', 'value': 'a', 'track_values': {'GA': ''}}})
    a1.Execute(self.scenario_context)
    a2.Execute(self.scenario_context)
    a3.Execute(self.scenario_context)
    a4.Execute(self.scenario_context)
    self.assertEqual(
        self.scenario_context.resource_ref_resolver._references,
        {'foo': 'a', 'bar': 'b', 'empty': ''})

  def testExecuteBinary(self):
    data = {
        'execute_binary': {
            'args': ['echo', 'foo'],
        }
    }
    a = schema.ExecuteBinaryAction.FromData(data)
    self.scenario_context.update_modes = [updates.Mode.RESULT]
    a.Execute(self.scenario_context)
    self.assertEqual(data, {
        'execute_binary': {
            'args': ['echo', 'foo'],
            'expect_exit': {'code': 0},
            'expect_stdout': 'foo\n'
        }
    })


class ExecuteCommandActionTests(sdk_test_base.WithOutputCapture,
                                test_case.WithInput,
                                sdk_test_base.WithTempCWD,
                                parameterized.TestCase):

  def SetUp(self):
    self.rewrite_mock = self.StartObjectPatch(
        schema.ScenarioContext, 'RewriteScenario')

  def _MakeContext(self, run_func, execution_mode=session.ExecutionMode.LOCAL,
                   update_modes=None):
    return schema.ScenarioContext(
        None, None, None, calliope_base.ReleaseTrack.GA,
        execution_mode,
        update_modes if update_modes is not None else [updates.Mode.RESULT],
        test_base.CreateStreamMocker(self), run_func)

  def testExecuteCommandUntil(self):
    stdout_values = ['first', 'second', 'done']
    stderr_values = ['firsterr', 'seconderr', 'doneerr']
    def _Run(command):
      self.assertEqual('foo bar FAKE0', command)
      sys.stdout.write(stdout_values.pop(0))
      sys.stderr.write(stderr_values.pop(0))
      if stdout_values:
        raise exceptions.Error('error')

    context = self._MakeContext(
        _Run, execution_mode=session.ExecutionMode.REMOTE)
    context.resource_ref_resolver.AddGeneratedResourceId('instance0', 'FAKE0')
    a = schema.ExecuteCommandUntilAction.FromData({
        'execute_command_until': {
            'command': 'foo bar $$instance0$$',
            'stdout': 'done',
            'stderr': 'doneerr',
            'exit_code': 0,
        }
    })
    a.Execute(context)
    # All values were consumed.
    self.assertEqual([], stdout_values)
    self.assertEqual([], stderr_values)

  def testExecute(self):
    """Basic tests of all functionality in the command execution action.

    This doesn't test a lot of details because the events themselves are heavily
    tested separately. We want to make sure that the resource ref substitution
    happens, a command is called, updates are triggered, and the scenario is
    updated.
    """
    def _Run(command):
      # Check that references get resolved for execution.
      sys.stdout.write(command)
      self.assertEqual('some command FAKE0 --flag=FAKE1 FAKE2', command)

    context = self._MakeContext(_Run)
    context.resource_ref_resolver.AddGeneratedResourceId('instance0', 'FAKE0')
    context.resource_ref_resolver.AddGeneratedResourceId('instance1', 'FAKE1')
    context.resource_ref_resolver.AddGeneratedResourceId('instance2', 'FAKE2')

    data = {'execute_command': {
        'command': 'some command $$instance0$$ --flag=$$instance1$$ '
                   '$$instance2$$',
        'cleanup_for': 'instance0',
        'label': 'Test label.',
        'events': [
            {'expect_stdout': 'some command $$instance0$$ --flag=$$instance1$$ '
                              '$$instance2$$'},
            {'expect_exit': {'code': 1}},
        ]
    }}
    a = schema.CommandExecutionAction.FromData(data)

    a.Execute(context)

    # Check that resource ref cleanup was removed.
    self.assertIsNone(
        context.resource_ref_resolver._resource_ids.get('instance0'))

    # Check that updates happened to the data.
    self.assertEqual(
        0, data['execute_command']['events'][1]['expect_exit']['code'])
    self.assertEqual(
        'some command $$instance0$$ --flag=$$instance1$$ $$instance2$$',
        data['execute_command']['command'])
    self.assertEqual(
        'some command $$instance0$$ --flag=$$instance1$$ $$instance2$$',
        data['execute_command']['events'][0]['expect_stdout'])
    self.assertEqual('Test label.', data['execute_command']['label'])

    # Check that the file is rewritten.
    self.rewrite_mock.assert_called_once()

  def testValidationOnlyLocal(self):
    """Validation only commands are not run in LOCAL mode."""
    run_mock = mock.MagicMock()
    context = self._MakeContext(
        run_mock, execution_mode=session.ExecutionMode.LOCAL)
    data = {'execute_command': {
        'command': 'some command',
        'validation_only': True,
        'events': [{'expect_exit': {'code': 0}},]
    }}
    a = schema.CommandExecutionAction.FromData(data)
    a.Execute(context)
    run_mock.assert_not_called()

  def testValidateRemoteAPICallsLocal(self):
    """In LOCAL mode validate_remote_api_calls set to False has no effect."""
    def _Run(command):
      del command
      http.Http().request(
          'https://example.com', method='GET', body='{"body": "foo"}',
          headers={'foo': 'bar'})

    context = self._MakeContext(
        _Run, execution_mode=session.ExecutionMode.LOCAL,
        update_modes=[updates.Mode.API_REQUESTS])
    data = {'execute_command': {
        'command': 'some command',
        'validate_remote_api_calls': False,
        'events': [{'expect_exit': {'code': 0}},]
    }}
    a = schema.CommandExecutionAction.FromData(data)
    with self.assertRaises(session.PauseError):
      # A pause error indicates that the session is validating the API request,
      # added it to the scenario, but doesn't have response data for it yet.
      a.Execute(context)

  @parameterized.named_parameters([
      ('ValidationOnly', {'validation_only': True}),
      ('ValidateRemoteAPICalls', {'validate_remote_api_calls': False}),
  ])
  def testAPICallValidationRemote(self, settings):
    """In REMOTE mode, don't validate api calls for either of these settings."""
    def _Run(command):
      del command
      http.Http().request('https://example.com', method='GET')

    context = self._MakeContext(
        _Run, execution_mode=session.ExecutionMode.REMOTE, update_modes=[])
    # Disabling validation makes API calls just pass through.
    request_mock = self.StartPatch('httplib2.Http.request')
    request_mock.return_value = ({'status': '200'}, b'')

    data = {'execute_command': {
        'command': 'some command',
        'events': [{'expect_exit': {'code': 0}},]
    }}
    data['execute_command'].update(settings)

    a = schema.CommandExecutionAction.FromData(data)
    # No errors are raised because we don't validate api calls.
    a.Execute(context)
    # Real call is made.
    self.assertEqual(1, request_mock.call_count)


class ValidationTests(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.StartObjectPatch(schema.Validator, '_Write', self.stderr.write)

  def testBadSchema(self):
    data = {'title': '', 'actions': [], 'foo': 'bar'}
    validator = schema.Validator(data)
    with self.assertRaises(schema.ValidationError):
      validator.Validate()

  def testMissingCleanup(self):
    data = {
        'title': '', 'actions': [
            {'generate_resource_id': {'reference': 'my-device',
                                      'prefix': 'iot-device'}},
            {'generate_resource_id': {'reference': 'my-device2',
                                      'prefix': 'iot-device'}},
            {'execute_command': {'command': '', 'events': []}}
        ]}
    validator = schema.Validator(data)
    with self.assertRaisesRegex(
        schema.ValidationError,
        r'No cleanup_for rules found for generate_resource_id action: '
        r'\[my-device\]\n'
        r'No cleanup_for rules found for generate_resource_id action: '
        r'\[my-device2\]\n'):
      validator.Validate()

  def testDuplicateGenerated(self):
    data = {
        'title': '', 'actions': [
            {'generate_resource_id': {'reference': 'my-device',
                                      'prefix': 'iot-device'}},
            {'generate_resource_id': {'reference': 'my-device',
                                      'prefix': 'iot-device'}},
            {'execute_command': {'command': '', 'events': []}}
        ]}
    validator = schema.Validator(data)
    with self.assertRaisesRegex(
        schema.ValidationError,
        r'Duplicate generate_resource_id reference found: \[my-device\]\n'
        r'No cleanup_for rules found for generate_resource_id action: '
        r'\[my-device\]'):
      validator.Validate()

  def testMissingMissingGenerated(self):
    data = {
        'title': '', 'actions': [
            {'execute_command': {'command': '', 'cleanup_for': 'asdf',
                                 'events': []}}
        ]}
    validator = schema.Validator(data)
    with self.assertRaisesRegex(
        schema.ValidationError,
        r'cleanup_for reference \[asdf\] was not found in a '
        r'generate_resource_id action'):
      validator.Validate()

  def testDuplicateCleanup(self):
    data = {
        'title': '', 'actions': [
            {'generate_resource_id': {'reference': 'my-device',
                                      'prefix': 'iot-device'}},
            {'execute_command': {'command': '', 'cleanup_for': 'my-device',
                                 'events': []}},
            {'execute_command': {'command': '', 'cleanup_for': 'my-device',
                                 'events': []}},
        ]}
    validator = schema.Validator(data)
    with self.assertRaisesRegex(
        schema.ValidationError,
        r'Duplicate cleanup_for reference found: \[my-device\]'):
      validator.Validate()

  def testUnnecessaryCleanup(self):
    data = {
        'title': '', 'actions': [
            {'generate_resource_id': {'reference': 'my-device',
                                      'prefix': 'iot-device',
                                      'requires_cleanup': False}},
            {'execute_command': {'command': '', 'cleanup_for': 'my-device',
                                 'events': []}},
        ]}
    validator = schema.Validator(data)
    with self.assertRaisesRegex(
        schema.ValidationError,
        r'cleanup_for reference \[my-device\] was marked as not requiring '
        r'cleanup'):
      validator.Validate()


if __name__ == '__main__':
  test_case.main()
