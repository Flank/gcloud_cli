# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests of the events flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import flags
from tests.lib import cli_test_base
from tests.lib.calliope import util as calliope_test_util
from tests.lib.surface.run import base


class FlagsTest(base.ServerlessBase):

  def SetUp(self):
    self.parser = calliope_test_util.ArgumentParser()
    flags.AddParametersFlags(self.parser)
    flags.AddSecretsFlag(self.parser)

  def _MakeEventType(self, include_props=False, include_secret_props=False):
    """Creates a source CRD with parameters and an event type."""
    self.source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    self.event_type = custom_resource_definition.EventType(
        self.source_crd,
        type='google.source.my.type',
        description='desc')
    self.source_crd.event_types = [self.event_type]
    spec_properties = []
    required_properties = []
    if include_props:
      start = len(spec_properties)
      spec_properties.extend([
          self._SpecParameterAdditionalProperty('prop{}'.format(i), 'string',
                                                'desc{}'.format(i))
          for i in range(start, start + 3)
      ])
      required_properties.append('prop{}'.format(start))
    if include_secret_props:
      start = len(spec_properties)
      spec_properties.extend([
          self._SpecParameterAdditionalProperty('prop{}Secret'.format(i),
                                                'object', 'desc{}'.format(i))
          for i in range(start, start + 2)
      ])
      required_properties.append('prop{}Secret'.format(start))
    self.source_crd.spec.validation = (
        self.crd_messages.CustomResourceValidation(
            openAPIV3Schema=self._SourceSchemaProperties(
                spec_properties, required_properties)))

  def testParseSecretParameters(self):
    args = self.parser.parse_args(
        ['--secrets=someSecret=name:value,otherSecret=name:value'])
    expected = {
        'someSecret': {'name': 'name', 'key': 'value'},
        'otherSecret': {'name': 'name', 'key': 'value'}
    }
    self.assertDictEqual(expected, flags._ParseSecretParameters(args))

  def testParseSecretParametersMultipleColons(self):
    args = self.parser.parse_args(
        ['--secrets=someSecret=name:value:andmore'])
    expected = {'someSecret': {'name': 'name', 'key': 'value:andmore'}}
    self.assertDictEqual(expected, flags._ParseSecretParameters(args))

  def testParseSecretParametersNotSpecified(self):
    args = self.parser.parse_args([])
    expected = {}
    self.assertDictEqual(expected, flags._ParseSecretParameters(args))

  def testParseSecretParametersFailsWithoutColon(self):
    args = self.parser.parse_args(
        ['--secrets=someSecret=name:value,otherSecret=justname'])
    with self.assertRaises(calliope_exceptions.InvalidArgumentException):
      flags._ParseSecretParameters(args)

  def testGetAndValidateSecretParameters(self):
    self._MakeEventType(include_secret_props=True)
    args = self.parser.parse_args(
        ['--secrets=prop0Secret=name:value,prop1Secret=name:value'])
    expected = {
        'prop0Secret': {'name': 'name', 'key': 'value'},
        'prop1Secret': {'name': 'name', 'key': 'value'}
    }
    self.assertDictEqual(
        expected, flags.GetAndValidateParameters(args, self.event_type))

  def testGetAndValidateSecretParametersUnknown(self):
    self._MakeEventType(include_secret_props=True)
    args = self.parser.parse_args(
        ['--secrets=prop0Secret=name:value,unknownSecret=name:value'])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknownSecret', str(ctx.exception))

  def testGetAndValidateSecretParametersUnknownMultiple(self):
    self._MakeEventType(include_secret_props=True)
    args = self.parser.parse_args(
        ['--secrets=prop0Secret=name:value,unknownSecret=name:value,'
         'anotherUnknownSecret=name:value'])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknownSecret', str(ctx.exception))
    self.assertIn('anotherUnknownSecret', str(ctx.exception))

  def testGetAndValidateSecretParametersMissingRequired(self):
    self._MakeEventType(include_secret_props=True)
    args = self.parser.parse_args(['--secrets=prop1Secret=name:value'])
    with self.assertRaises(
        exceptions.MissingRequiredEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('prop0Secret', str(ctx.exception))

  def testGetAndValidateSecretParametersMissingRequiredNotSpecified(self):
    self._MakeEventType(include_secret_props=True)
    args = self.parser.parse_args([])
    with self.assertRaises(
        exceptions.MissingRequiredEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('prop0Secret', str(ctx.exception))

  def _MakeTempFile(self, data):
    return self.Touch(
        self.temp_path, 'test.yaml', contents=data, makedirs=True)

  def testParametersAndParametersFromFileMutex(self):
    filename = self._MakeTempFile('key: value')
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args(
          ['--parameters=key=value', '--parameters-from-file', filename])

  def testGetAndValidateParameters(self):
    self._MakeEventType(include_props=True)
    args = self.parser.parse_args(
        ['--parameters=prop0=value,prop1=value,prop2=value'])
    expected = {'prop0': 'value', 'prop1': 'value', 'prop2': 'value'}
    self.assertDictEqual(
        expected, flags.GetAndValidateParameters(args, self.event_type))

  def testGetAndValidateParametersFromFile(self):
    self._MakeEventType(include_props=True)
    filename = self._MakeTempFile("""
    prop0: value
    prop1: value
    prop2: value
    """)
    args = self.parser.parse_args(['--parameters-from-file', filename])
    expected = {'prop0': 'value', 'prop1': 'value', 'prop2': 'value'}
    self.assertDictEqual(
        expected, flags.GetAndValidateParameters(args, self.event_type))

  def testGetAndValidateParametersUnknown(self):
    self._MakeEventType(include_props=True)
    args = self.parser.parse_args(
        ['--parameters=prop0=value,unknown=value'])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknown', str(ctx.exception))

  def testGetAndValidateParametersFromFileUnknown(self):
    self._MakeEventType(include_props=True)
    filename = self._MakeTempFile("""
    prop0: value
    unknown: value
    """)
    args = self.parser.parse_args(['--parameters-from-file', filename])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknown', str(ctx.exception))

  def testGetAndValidateParametersUnknownMultiple(self):
    self._MakeEventType(include_props=True)
    args = self.parser.parse_args(
        ['--parameters=prop0=value,unknown=value,'
         'anotherUnknown=name'])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknown', str(ctx.exception))
    self.assertIn('anotherUnknown', str(ctx.exception))

  def testGetAndValidateParametersFromFileUnknownMultiple(self):
    self._MakeEventType(include_props=True)
    filename = self._MakeTempFile("""
    prop0: value
    unknown: value
    anotherUnknown: name
    """)
    args = self.parser.parse_args(['--parameters-from-file', filename])
    with self.assertRaises(exceptions.UnknownEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('unknown', str(ctx.exception))
    self.assertIn('anotherUnknown', str(ctx.exception))

  def testGetAndValidateParametersMissingRequired(self):
    self._MakeEventType(include_props=True)
    args = self.parser.parse_args(['--parameters=prop1=value,prop2=value'])
    with self.assertRaises(
        exceptions.MissingRequiredEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('prop0', str(ctx.exception))

  def testGetAndValidateParametersFromFileMissingRequired(self):
    self._MakeEventType(include_props=True)
    filename = self._MakeTempFile("""
    prop1: value
    prop2: value
    """)
    args = self.parser.parse_args(['--parameters-from-file', filename])
    with self.assertRaises(
        exceptions.MissingRequiredEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('prop0', str(ctx.exception))

  def testGetAndValidateParametersMissingRequiredNotSpecified(self):
    self._MakeEventType(include_props=True)
    args = self.parser.parse_args([])
    with self.assertRaises(
        exceptions.MissingRequiredEventTypeParameters) as ctx:
      flags.GetAndValidateParameters(args, self.event_type)
    self.assertIn('prop0', str(ctx.exception))

  def testGetAndValidateParametersAndSecretParameters(self):
    self._MakeEventType(include_props=True, include_secret_props=True)
    args = self.parser.parse_args([
        '--parameters=prop0=value,prop1=value,prop2=value',
        '--secrets=prop3Secret=name:value,prop4Secret=name:value'
    ])
    expected = {
        'prop0': 'value', 'prop1': 'value', 'prop2': 'value',
        'prop3Secret': {'name': 'name', 'key': 'value'},
        'prop4Secret': {'name': 'name', 'key': 'value'}
    }
    self.assertDictEqual(
        expected, flags.GetAndValidateParameters(args, self.event_type))

  def testGetAndValidateParametersFromFileAndSecretParameters(self):
    self._MakeEventType(include_props=True, include_secret_props=True)
    filename = self._MakeTempFile("""
    prop0: value
    prop1: value
    prop2: value
    """)
    args = self.parser.parse_args([
        '--parameters-from-file', filename,
        '--secrets=prop3Secret=name:value,prop4Secret=name:value'
    ])
    expected = {
        'prop0': 'value', 'prop1': 'value', 'prop2': 'value',
        'prop3Secret': {'name': 'name', 'key': 'value'},
        'prop4Secret': {'name': 'name', 'key': 'value'}
    }
    self.assertDictEqual(
        expected, flags.GetAndValidateParameters(args, self.event_type))
