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

"""Tests for the session module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.scenario import schema
from tests.lib.scenario import session
from tests.lib.scenario import test_base
from tests.lib.scenario import updates


class SchemaTests(sdk_test_base.WithOutputCapture,
                  sdk_test_base.WithTempCWD,
                  parameterized.TestCase):
  """Tests of schema actions."""

  def SetUp(self):
    self.scenario_context = schema.ScenarioContext(
        None, None, None, None, None, None, None)

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
    with self.assertRaisesRegex(ValueError,
                                r'Unknown resource reference: \[instance0\]'):
      self.scenario_context.resource_ref_resolver.Resolve(
          'some command $$instance0$$')


class ExecuteCommandActionTests(sdk_test_base.WithOutputCapture,
                                test_case.WithInput,
                                sdk_test_base.WithTempCWD,
                                parameterized.TestCase):

  def SetUp(self):
    self.rewrite_mock = self.StartObjectPatch(
        schema.CommandExecutionAction, '_RewriteScenario')

  def _MakeContext(self, run_func):
    return schema.ScenarioContext(
        None, None, None, session.ExecutionMode.LOCAL, [updates.Mode.RESULT],
        test_base.CreateStreamMocker(self), run_func)

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

    # Check that the file is rewritten.
    self.rewrite_mock.assert_called_once()


class ValidationTests(sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.StartObjectPatch(schema.Validator, '_Write', self.stderr.write)

  def testBadSchema(self):
    data = {'title': '', 'actions': [], 'foo': 'bar'}
    validator = schema.Validator(data)
    self.assertFalse(validator.Validate())

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
    self.assertFalse(validator.Validate())
    self.AssertErrEquals(
        'No cleanup_for rules found for generate_resource_id action: '
        '[my-device, my-device2]\n')

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
    self.assertFalse(validator.Validate())
    self.AssertErrEquals("""\
Duplicate generate_resource_id reference found: [my-device]
No cleanup_for rules found for generate_resource_id action: [my-device]
""")

  def testMissingMissingGenerated(self):
    data = {
        'title': '', 'actions': [
            {'execute_command': {'command': '', 'cleanup_for': 'asdf',
                                 'events': []}}
        ]}
    validator = schema.Validator(data)
    self.assertFalse(validator.Validate())
    self.AssertErrEquals(
        'cleanup_for reference [asdf] was not found in a generate_resource_id '
        'action\n')

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
    self.assertFalse(validator.Validate())
    self.AssertErrEquals('Duplicate cleanup_for reference found: [my-device]\n')


if __name__ == '__main__':
  test_case.main()
