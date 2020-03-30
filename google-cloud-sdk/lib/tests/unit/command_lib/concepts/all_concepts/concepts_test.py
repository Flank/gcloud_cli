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

"""Tests for concepts v2 types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import datetime
import functools

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.concepts import concept_managers
from googlecloudsdk.command_lib.concepts import dependency_managers
from googlecloudsdk.command_lib.concepts import exceptions
from googlecloudsdk.command_lib.concepts.all_concepts import concepts
from googlecloudsdk.core.util import semver
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.command_lib.concepts import concepts_test_base
from tests.lib.core import core_completer_test_base
from tests.lib.parameterized_line_no import LabelLineNo as T


# Dummy objects for parameterized tests.
_COMPLETER = object()
_FALLTHROUGH = object()


class ConceptParseViewBase(concepts_test_base.ConceptArgsTestBase,
                           parameterized.TestCase):
  """Base for concept.Parse(DependencyView) tests."""

  def ParseView(self, concept_type, expected, dependency_view, attr, kwargs):
    """Runs a concept type test case."""
    if kwargs is None:
      kwargs = {}
    exception = kwargs.pop('exception', None)
    exception_regex = kwargs.pop('exception_regex', None)

    attr.update(kwargs)

    if not exception:
      concept = concept_type(**attr)
      actual = concept.Parse(dependency_view)
      self.assertEqual(expected, actual)
    elif not exception_regex:
      with self.assertRaises(exception):
        concept = concept_type(**attr)
        concept.Parse(dependency_view)
    else:
      with self.assertRaisesRegex(exception, exception_regex):
        concept = concept_type(**attr)
        concept.Parse(dependency_view)


class ConceptParseArgsBase(concepts_test_base.ConceptArgsTestBase,
                           parameterized.TestCase):
  """Base for args.CONCEPT_ARGS.ParseConcepts() tests."""

  def ParseArgs(self, concept_type, expected, args, attr, kwargs):
    """Runs a full parse concept type test case."""
    if kwargs is None:
      kwargs = {}
    exception = kwargs.pop('exception', None)
    exception_regex = kwargs.pop('exception_regex', None)

    attr.update(kwargs)

    if not exception:
      concept = concept_type(**attr)
      manager = concept_managers.ConceptManager()
      manager.AddConcept(concept)
      manager.AddToParser(self.parser)
      args = self.parser.parser.parse_args(args)
      args.CONCEPT_ARGS.ParseConcepts()
      actual = getattr(args, concept.name)
      self.assertEqual(expected, actual)
    elif not exception_regex:
      with self.assertRaises(exception):
        concept = concept_type(**attr)
        manager = concept_managers.ConceptManager()
        manager.AddConcept(concept)
        manager.AddToParser(self.parser)
        args = self.parser.parser.parse_args(args)
        args.CONCEPT_ARGS.ParseConcepts()
        getattr(args, concept.name)
    else:
      with self.assertRaisesRegex(exception, exception_regex):
        concept = concept_type(**attr)
        manager = concept_managers.ConceptManager()
        manager.AddConcept(concept)
        manager.AddToParser(self.parser)
        args = self.parser.parser.parse_args(args)
        args.CONCEPT_ARGS.ParseConcepts()
        getattr(args, concept.name)


class StringTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', 'arg', None, 'arg'),
      T('FromFallthrough', None, 'fall', 'fall'),
      T('FromArgsFirst', 'arg', 'fall', 'arg'),

      T('RegexOK', 'Value', None, 'Value', regex=r'\b[A-Z][a-z_0-9]*\b'),

      T('RegexBad1', 'nope', None, None, regex=r'\b[A-Z][a-z_0-9]*\b',
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--str\]. Value \[nope\] does '
                         r'not match \[\\b\[A-Z\]\[a-z_0-9\]\*\\b\].')),
      T('RegexBad2', '00ps', None, None, regex=r'\b[A-Z][a-z_0-9]*\b',
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--str\]. Value \[00ps\] does '
                         r'not match \[\\b\[A-Z\]\[a-z_0-9\]\*\\b\].')),

      T('NotAnInterval', 'not_interval', None, None,
        min_endpoint=concepts.Endpoint('jk'),
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'min_endpoint'"),
      T('NotANumber', 'unlimited', None, None, unlimited=True,
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'unlimited'"),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'str': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--str'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'str', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.String, expected_result, dependency_view,
                   attr, kwargs)

  def testParseNotRequired(self):
    dv = dependency_managers.DependencyViewFromValue(lambda: None)
    self.assertIsNone(self.string_concept.Parse(dv))

  def testBuildHelpText(self):
    concept = concepts.String(name='c', help_text='Raw help text.')
    self.assertEqual('Raw help text.',
                     concept.BuildHelpText())

  @parameterized.named_parameters(
      # Default values for concept lead to default values for Attribute object.
      T('Defaults', {}, '--c', [],
        {'required': False, 'hidden': False, 'metavar': None,
         'completer': None, 'help': 'h', 'action': None, 'default': None,
         'choices': None}),
      # Test that various kwargs are passed to the Attribute object.
      T('NonDefaults',
        {'name': 'arg_name', 'positional': True, 'required': True,
         'hidden': True, 'metavar': 'MY_CONCEPT', 'completer': _COMPLETER},
        'ARG_NAME', [],
        {'required': True, 'hidden': True, 'completer': _COMPLETER,
         'metavar': 'MY_CONCEPT', 'help': 'h', 'action': None,
         'default': None, 'choices': None}),
      # Fallthroughs don't affect attribute.required if concept is not required.
      T('DefaultsWithFallthroughs', {'fallthroughs': [_FALLTHROUGH]},
        '--c', [_FALLTHROUGH],
        {'required': False, 'hidden': False, 'metavar': None,
         'completer': None, 'help': 'h', 'action': None, 'default': None,
         'choices': None}),
      # attribute.required is false if there are fallthroughs.
      T('RequiredWithFallthroughs',
        {'fallthroughs': [_FALLTHROUGH], 'required': True},
        '--c', [_FALLTHROUGH],
        {'required': False, 'hidden': False, 'completer': None,
         'metavar': None, 'help': 'h', 'action': None, 'default': None,
         'choices': None}),
  )
  def testAttribute(self, kwargs, expected_name, expected_fallthroughs,
                    expected_kwargs):
    name = kwargs.pop('name') if 'name' in kwargs else 'c'
    concept = concepts.String(name, help_text='h', **kwargs)

    attribute = concept.Attribute()

    self.assertEqual(expected_name, attribute.arg_name)
    self.assertEqual(expected_fallthroughs, attribute.fallthroughs)
    self.assertEqual(expected_kwargs, attribute.kwargs)

  @parameterized.named_parameters(
      T('Flag', 'foo_bar', False, '--foo-bar'),
      T('Positional', 'foo_bar', True, 'FOO_BAR'),
      T('PositionalToFlag', 'FOO_BAR', False, '--foo-bar'),
      T('FlagToPositional', '--foo-bar', True, 'FOO_BAR'),
  )
  def testGetPresentationName(self, name, positional, expected_name):
    concept = concepts.String(name=name, positional=positional, help_text='h')
    self.assertEqual(expected_name, concept.GetPresentationName())


class BooleanTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', 'true', None, True),
      T('FromFallthrough', None, 'True', True),
      T('FromArgsFirst', 'FALSE', 'TRUE', False),
      T('Zero', '0', None, False),
      T('One', '1', None, True),
      T('Hunnert', '100', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--boolean\]. Invalid Boolean '
                         r'value \[100\].')),
      T('Invalid', 'truthiness', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--boolean\]. Invalid Boolean '
                         r'value \[truthiness\].')),

      T('NotARegex', 'true', None, None,
        regex='foo',
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'regex'"),
      T('NotAnInterval', 'not_interval', None, None,
        min_endpoint=concepts.Endpoint('jk'),
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'min_endpoint'"),
      T('NotANumber', 'unlimited', None, None, unlimited=True,
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'unlimited'"),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'boolean': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--boolean'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'boolean', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.Boolean, expected_result, dependency_view,
                   attr, kwargs)

  def testBuildHelpText(self):
    concept = concepts.Boolean(name='c', help_text='Raw help text.')
    self.assertEqual('Raw help text.',
                     concept.BuildHelpText())


class EnumTest(ConceptParseViewBase):

  _CHOICES = {
      'curses': 'Foiled again.',
      'go': 'Go gadget.',
      'up': 'Up and away.',
      'STOP': 'Wait, hold on.'
  }

  @parameterized.named_parameters(
      T('FromArgs', 'up', None, 'up'),
      T('FromFallthrough', None, 'GO', 'go'),
      T('FromArgsFirst', 'Go', 'curses', 'go'),
      T('IgnoreCase', 'stop', None, 'stop'),
      T('Invalid', 'foo', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--enum\]. Invalid choice \[foo\], '
                         r'must be one of \[STOP,curses,go,up\].')),

      T('NotARegex', 'true', None, None,
        regex='foo',
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'regex'"),
      T('NotAnInterval', 'not_interval', None, None,
        min_endpoint=concepts.Endpoint('jk'),
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'min_endpoint'"),
      T('NotANumber', 'unlimited', None, None, unlimited=True,
        exception=TypeError,
        exception_regex="got an unexpected keyword argument 'unlimited'"),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'enum': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--enum'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {
        'name': 'enum',
        'help_text': 'help',
        'required': True,
        'choices': self._CHOICES,
    }
    self.ParseView(concepts.Enum, expected_result, dependency_view,
                   attr, kwargs)

  def testBuildHelpText(self):
    concept = concepts.Enum(name='c', help_text='Pick a card, any card.',
                            choices=self._CHOICES)
    self.assertEqual("""\
Pick a card, any card. Must be one of the following values:
+
*STOP*::: Wait, hold on.
*curses*::: Foiled again.
*go*::: Go gadget.
*up*::: Up and away.
""",
                     concept.BuildHelpText())


class IntegerTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', '12', None, 12),
      T('FromFallthrough', None, '-34', -34),
      T('FromArgsFirst', '123', '456', 123),
      T('ConvertFromFallthrough', None, '789', 789),
      T('UnlimitedArg', 'unlimited', None, None, unlimited=True),
      T('UnlimitedFallthrough', None, 'unlimited', None, unlimited=True),

      T('MinClosedGT', '1', None, 1,
        min_endpoint=concepts.Endpoint('0')),
      T('MinClosedEQ', '0', None, 0,
        min_endpoint=concepts.Endpoint('0')),
      T('MinClosedLT', '-1', None, None,
        min_endpoint=concepts.Endpoint('0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[-1\] must be '
                         r'greater than or equal to \[0\].')),

      T('MinOpenGT', '1', None, 1,
        min_endpoint=concepts.Endpoint('0', closed=False)),
      T('MinOpenEQ', '0', None, None,
        min_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[0\] must be '
                         r'greater than \[0\].')),
      T('MinOpenLT', '-1', None, None,
        min_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[-1\] must be '
                         r'greater than \[0\].')),

      T('MaxClosedGT', '1', None, None,
        max_endpoint=concepts.Endpoint('0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[1\] must be '
                         r'less than or equal to \[0\].')),
      T('MaxClosedEQ', '0', None, 0,
        max_endpoint=concepts.Endpoint('0')),
      T('MaxClosedLT', '-1', None, -1,
        max_endpoint=concepts.Endpoint('0')),

      T('MaxOpenGT', '1', None, None,
        max_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[1\] must be '
                         r'less than \[0\].')),
      T('MaxOpenEQ', '0', None, None,
        max_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--int\]. Value \[0\] must be '
                         r'less than \[0\].')),
      T('MaxOpenLT', '-1', None, -1,
        max_endpoint=concepts.Endpoint('0', closed=False)),

      T('MinBad', '1', None, None,
        min_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid min endpoint \[abc\] for \[--int\]. Invalid "
                         r"literal for int\(\) with base 10: 'abc'.")),
      T('MaxBad', '0', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid max endpoint \[xyz\] for \[--int\]. Invalid "
                         r"literal for int\(\) with base 10: 'xyz'.")),

      T('UnlimitedInvalid', None, 'unlimited', None,
        exception=exceptions.ParseError,
        exception_regex=(r"Failed to parse \[--int\]. Invalid literal for "
                         r"int\(\) with base 10: 'unlimited'.")),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r"Failed to parse \[--int\]. Invalid literal for "
                         r"int\(\) with base 10: 'xyz'.")),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r"Failed to parse \[--int\]. Invalid literal for "
                         r"int\(\) with base 10: 'xyz'.")),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'int': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--int'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'int', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.Integer, expected_result, dependency_view,
                   attr, kwargs)

  def testBuildHelpText(self):
    concept = concepts.Integer('int', help_text='Provide an integer.')
    self.assertEqual('Provide an integer. Must be a string representing an '
                     'integer.', concept.BuildHelpText())

  def testParseNotRequired(self):
    dv = dependency_managers.DependencyViewFromValue(lambda: None)
    self.assertIsNone(self.integer_concept.Parse(dv))

  def testAttribute(self):
    concept = concepts.Integer('number', help_text='Provide a number.')
    attribute = concept.Attribute()
    self.assertEqual('--number', attribute.arg_name)
    self.assertEqual(concept, attribute.concept)
    self.assertEqual([], attribute.fallthroughs)
    self.assertEqual(
        {
            'action': None,
            'choices': None,
            'completer': None,
            'default': None,
            'help': ('Provide a number. Must be a string representing an '
                     'integer.'),
            'hidden': False,
            'metavar': None,
            'required': False,
        },
        attribute.kwargs)

  @parameterized.named_parameters(
      T('Flag', 'foo_bar', False, '--foo-bar'),
      T('Positional', 'foo_bar', True, 'FOO_BAR'),
  )
  def testGetPresentationName(self, name, positional, expected_name):
    concept = concepts.Integer(name, positional=positional, help_text='h')
    self.assertEqual(expected_name, concept.GetPresentationName())

  @parameterized.named_parameters(
      T('NoNameGivenFlag', None, False, '--int'),
      T('NoNameGivenPositional', None, True, 'INT'),
  )
  def testGetPresentationNone(self, name, positional, expected_name):
    with self.assertRaisesRegex(exceptions.InitializationError,
                                'Concept name required.'):
      concepts.Integer(name, positional=positional, help_text='h')


class ScaledIntegerTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', '1k', None, 1000),
      T('FromFallthrough', None, '2ki', 2048),
      T('FromArgsFirst', '1MiB', '2MB', 1048576),
      T('ConvertFromFallthrough', None, '3GiB', 3221225472),
      T('ZeroNoUnit', '0', None, 0),
      T('NoUnit', '1234', None, 1234),
      T('DefaultUnit', '1234', None, 1234000, default_unit='k'),
      T('DefaultOutputUnit', '1234', None, 1234,
        default_unit='k', output_unit='k'),
      T('OutputUnit', '8GiB', None, 8, output_unit='GiB'),
      T('DefaultOutputUnitTooBig', '8GiB', None, 8,
        default_unit='GiB', output_unit='GiB',
        max_endpoint=concepts.Endpoint('4'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[8GiB\] must '
                         r'be less than or equal to \[4GiB\].')),
      T('DefaultUnitBad', '8GiB', None, None, default_unit='XYZ',
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid default scaled integer unit \[XYZ\] for '
                         r'\[sizes\]. Invalid type \[YZ\] in \[XYZ\], expected '
                         r'\[B\] or nothing.')),
      T('OutputUnitBad', '8GiB', None, None, output_unit='123',
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid output scaled integer unit \[123\] for '
                         r'\[sizes\]. Invalid type \[23\] in \[123\], expected '
                         r'\[B\] or nothing.')),

      T('MinClosedLT', '3KiB', None, 1024,
        min_endpoint=concepts.Endpoint('1MiB'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[3kiB\] must '
                         r'be greater than or equal to \[1MiB\].')),
      T('MinClosedEQ', '1MiB', None, 1048576,
        min_endpoint=concepts.Endpoint('1MiB')),
      T('MinClosedGT', '5GB', None, 5000000000,
        min_endpoint=concepts.Endpoint('1MiB')),

      T('MinOpenLT', '1KB', None, 1,
        min_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1kB\] must '
                         r'be greater than \[1MiB\].')),
      T('MinOpenEQ', '1MiB', None, None,
        min_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1MiB\] must '
                         r'be greater than \[1MiB\].')),
      T('MinOpenGT', '8GB', None, 8000000000,
        min_endpoint=concepts.Endpoint('1MiB', closed=False)),

      T('MaxClosedLT', '256', None, 256,
        max_endpoint=concepts.Endpoint('1MiB')),
      T('MaxClosedEQ', '1MiB', None, 1048576,
        max_endpoint=concepts.Endpoint('1MiB')),
      T('MaxClosedGT', '2MiB', None, None,
        max_endpoint=concepts.Endpoint('1MiB'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[2MiB\] must '
                         r'be less than or equal to \[1MiB\].')),

      T('MaxOpenLT', '10K', None, 10000,
        max_endpoint=concepts.Endpoint('1MiB', closed=False)),
      T('MaxOpenEQ', '1Mi', None, None,
        max_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1MiB\] must '
                         r'be less than \[1MiB\].')),
      T('MaxOpenGT', '1Gi', None, -1,
        max_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1GiB\] must '
                         r'be less than \[1MiB\].')),

      T('MinBad', '1', None, None,
        max_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[abc\] for \[--sizes\]. '
                         r'Failed to parse binary/decimal scaled integer '
                         r'\[abc\]: \[abc\] must the form INTEGER\[UNIT\]\[B\] '
                         r'where units may be one of '
                         r'\[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
      T('MaxBad', '0', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[xyz\] for \[--sizes\]. '
                         r'Failed to parse binary/decimal scaled integer '
                         r'\[xyz\]: \[xyz\] must the form INTEGER\[UNIT\]\[B\] '
                         r'where units may be one of '
                         r'\[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),

      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--sizes\]. Failed to parse '
                         r'binary/decimal scaled integer \[xyz\]: \[xyz\] must '
                         r'the form INTEGER\[UNIT\]\[B\] where units may be '
                         r'one of \[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--sizes\]. Failed to parse '
                         r'binary/decimal scaled integer \[xyz\]: \[xyz\] must '
                         r'the form INTEGER\[UNIT\]\[B\] where units may be '
                         r'one of \[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
  )
  def testScaledIntegerParse(self, arg_fallthrough_value, fallthrough_value,
                             expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'sizes': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--sizes'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'sizes', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.ScaledInteger, expected_result, dependency_view,
                   attr, kwargs)

  def testScaledIntegerBuildHelpText(self):
    concept = concepts.ScaledInteger('int', help_text='Provide an integer.')
    self.assertEqual('Provide an integer. Must be a string representing an '
                     'ISO/IEC Decimal/Binary scaled integer. For example, '
                     '1k == 1000 and 1ki == 1024. The default type '
                     'abbreviation is `B`. See '
                     'https://en.wikipedia.org/wiki/Binary_prefix for details.',
                     concept.BuildHelpText())

  @parameterized.named_parameters(
      T('FromArgs', '1k', None, 1024),
      T('FromFallthrough', None, '2ki', 2048),
      T('FromArgsFirst', '1MiB', '2MB', 1048576),
      T('ConvertFromFallthrough', None, '3GiB', 3221225472),
      T('ZeroNoUnit', '0', None, 0),
      T('NoUnit', '1234', None, 1234),
      T('DefaultUnit', '1234', None, 1263616, default_unit='k'),

      T('MinClosedLT', '3KiB', None, 1024,
        min_endpoint=concepts.Endpoint('1MiB'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[3kiB\] must '
                         r'be greater than or equal to \[1MiB\].')),
      T('MinClosedEQ', '1MiB', None, 1048576,
        min_endpoint=concepts.Endpoint('1MiB')),
      T('MinClosedGT', '5GB', None, 5368709120,
        min_endpoint=concepts.Endpoint('1MiB')),

      T('MinOpenLT', '1KB', None, 1,
        min_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1kiB\] must '
                         r'be greater than \[1MiB\].')),
      T('MinOpenEQ', '1MiB', None, None,
        min_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1MiB\] must '
                         r'be greater than \[1MiB\].')),
      T('MinOpenGT', '8GB', None, 8589934592,
        min_endpoint=concepts.Endpoint('1MiB', closed=False)),

      T('MaxClosedLT', '256', None, 256,
        max_endpoint=concepts.Endpoint('1MiB')),
      T('MaxClosedEQ', '1MiB', None, 1048576,
        max_endpoint=concepts.Endpoint('1MiB')),
      T('MaxClosedGT', '2MiB', None, None,
        max_endpoint=concepts.Endpoint('1MiB'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[2MiB\] must '
                         r'be less than or equal to \[1MiB\].')),

      T('MaxOpenLT', '10K', None, 10240,
        max_endpoint=concepts.Endpoint('1MiB', closed=False)),
      T('MaxOpenEQ', '1Mi', None, None,
        max_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1MiB\] must '
                         r'be less than \[1MiB\].')),
      T('MaxOpenGT', '1Gi', None, -1,
        max_endpoint=concepts.Endpoint('1MiB', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--sizes\]. Value \[1GiB\] must '
                         r'be less than \[1MiB\].')),

      T('MinBad', '1', None, None,
        min_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid min endpoint \[abc\] for \[--sizes\]. '
                         r'Failed to parse binary scaled integer '
                         r'\[abc\]: \[abc\] must the form INTEGER\[UNIT\]\[B\] '
                         r'where units may be one of '
                         r'\[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
      T('MaxBad', '0', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[xyz\] for \[--sizes\]. '
                         r'Failed to parse binary scaled integer '
                         r'\[xyz\]: \[xyz\] must the form INTEGER\[UNIT\]\[B\] '
                         r'where units may be one of '
                         r'\[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),

      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--sizes\]. Failed to parse '
                         r'binary scaled integer \[xyz\]: \[xyz\] must '
                         r'the form INTEGER\[UNIT\]\[B\] where units may be '
                         r'one of \[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--sizes\]. Failed to parse '
                         r'binary scaled integer \[xyz\]: \[xyz\] must '
                         r'the form INTEGER\[UNIT\]\[B\] where units may be '
                         r'one of \[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
  )
  def testBinaryScaledIntegerParse(self, arg_fallthrough_value,
                                   fallthrough_value, expected_result,
                                   kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'sizes': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--sizes'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'sizes', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.BinaryScaledInteger, expected_result,
                   dependency_view, attr, kwargs)

  def testBinaryScaledIntegerBuildHelpText(self):
    concept = concepts.BinaryScaledInteger('int',
                                           help_text='Provide an integer.')
    self.assertEqual('Provide an integer. Must be a string representing binary '
                     'scaled integer where all ISO/IEC prefixes are powers of '
                     '2. For example, 1k == 1ki == 1024. The default type '
                     'abbreviation is `B`. See '
                     'https://en.wikipedia.org/wiki/Binary_prefix for details.',
                     concept.BuildHelpText())


class FloatTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', '1.2', None, 1.2),
      T('FromFallthrough', None, '-3.4', -3.4),
      T('FromArgsFirst', '1.23', '4.56', 1.23),
      T('ConvertFromFallthrough', None, '789', 789.0),
      T('UnlimitedArg', 'unlimited', None, None, unlimited=True),
      T('UnlimitedFallthrough', None, 'unlimited', None, unlimited=True),

      T('MinClosedGT', '1.5', None, 1.5,
        min_endpoint=concepts.Endpoint('0')),
      T('MinClosedEQ', '0.0', None, 0.0,
        min_endpoint=concepts.Endpoint('0')),
      T('MinClosedLT', '-1.3', None, None,
        min_endpoint=concepts.Endpoint('0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[-1.3\] must '
                         r'be greater than or equal to \[0.0\].')),

      T('MinOpenGT', '1.5', None, 1.5,
        min_endpoint=concepts.Endpoint('0', closed=False)),
      T('MinOpenEQ', '0.0', None, None,
        min_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[0.0\] must '
                         r'be greater than \[0.0\].')),
      T('MinOpenLT', '-1.4', None, None,
        min_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[-1.4\] must '
                         r'be greater than \[0.0\].')),

      T('MaxClosedGT', '1.6', None, None,
        max_endpoint=concepts.Endpoint('0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[1.6\] must '
                         r'be less than or equal to \[0.0\].')),
      T('MaxClosedEQ', '0.0', None, 0,
        max_endpoint=concepts.Endpoint('0')),
      T('MaxClosedLT', '-1.8', None, -1.8,
        max_endpoint=concepts.Endpoint('0')),

      T('MaxOpenGT', '1.9', None, None,
        max_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[1.9\] must '
                         r'be less than \[0.0\].')),
      T('MaxOpenEQ', '0.0', None, None,
        max_endpoint=concepts.Endpoint('0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--float\]. Value \[0.0\] must '
                         r'be less than \[0.0\].')),
      T('MaxOpenLT', '-1.9', None, -1.9,
        max_endpoint=concepts.Endpoint('0', closed=False)),

      T('MinBad', '1', None, None,
        min_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid min endpoint \[abc\] for \[--float\]. "
                         r"Failed to parse floating point number \[abc\]: "
                         r"Could not convert string to float: '?abc'?.")),
      T('MaxBad', '0', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid max endpoint \[xyz\] for \[--float\]. "
                         r"Failed to parse floating point number \[xyz\]: "
                         r"Could not convert string to float: '?xyz'?.")),

      T('UnlimitedInvalid', None, 'unlimited', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--float\]. Failed to parse '
                         r'floating point number \[unlimited\]: Could not '
                         r"convert string to float: '?unlimited'?.")),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--float\]. Failed to parse '
                         r'floating point number \[xyz\]: Could not convert '
                         r"string to float: '?xyz'?.")),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--float\]. Failed to parse '
                         r'floating point number \[xyz\]: Could not convert '
                         r"string to float: '?xyz'?.")),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'float': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--float'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'float', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.Float, expected_result, dependency_view,
                   attr, kwargs)

  def testBuildHelpText(self):
    concept = concepts.Float('float', help_text='Provide a float.')
    self.assertEqual('Provide a float. Must be a string representing a '
                     'floating point number.', concept.BuildHelpText())


class DayOfWeekTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', 'MON', None, 'MON'),
      T('FromFallthrough', None, 'MON', 'MON'),
      T('FromArgsFirst', 'MON', 'TUE', 'MON'),
      T('FromArgs_ThreeChars', 'Monfoo', None, 'MON'),
      T('ConvertFromArgs', 'Sunday', None, 'SUN'),
      T('ConvertFromFallthrough', None, 'Sunday', 'SUN'),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--day\]. A day of week value '
                         r'\[xyz\] must be one of: \[SUN, MON, TUE, WED, THU, '
                         r'FRI, SAT\].')),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--day\]. A day of week value '
                         r'\[xyz\] must be one of: \[SUN, MON, TUE, WED, THU, '
                         r'FRI, SAT\].')),
      T('InvalidPartialMatch', 'Fooday', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--day\]. A day of week value '
                         r'\[Fooday\] must be one of: \[SUN, MON, TUE, WED, '
                         r'THU, FRI, SAT\].')),
  )
  def testParse(self, arg_fallthrough_value, fallthrough_value,
                expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'day': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--day'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'day', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.DayOfWeek, expected_result, dependency_view,
                   attr, kwargs)

  def testParseNotRequired(self):
    dv = dependency_managers.DependencyViewFromValue(lambda: None)
    self.assertIsNone(self.day_of_week_concept.Parse(dv))

  def testBuildHelpText(self):
    concept = concepts.DayOfWeek('day', help_text='Provide a day of the week.')
    self.assertEqual('Provide a day of the week. Must be a string representing '
                     'a day of the week in English, such as \'MON\' or '
                     '\'FRI\'. Case is ignored, and any characters after the '
                     'first three are ignored.',
                     concept.BuildHelpText())

  def testAttribute(self):
    concept = concepts.DayOfWeek('start_day',
                                 help_text='Provide a day of the week.')
    attribute = concept.Attribute()
    self.assertEqual('--start-day', attribute.arg_name)
    self.assertEqual(concept, attribute.concept)
    self.assertEqual([], attribute.fallthroughs)
    self.assertEqual(
        {
            'action': None,
            'choices': None,
            'completer': None,
            'default': None,
            'help': ("Provide a day of the week. Must be a string representing "
                     "a day of the week in English, such as 'MON' or 'FRI'. "
                     "Case is ignored, and any characters after the first "
                     "three are ignored."),
            'hidden': False,
            'metavar': None,
            'required': False,
        },
        attribute.kwargs)

  @parameterized.named_parameters(
      T('Flag', 'foo_bar', False, '--foo-bar'),
      T('Positional', 'foo_bar', True, 'FOO_BAR'),
  )
  def testGetPresentationName(self, name, positional, expected_name):
    concept = concepts.DayOfWeek(name, positional=positional, help_text='h')
    self.assertEqual(expected_name, concept.GetPresentationName())

  @parameterized.named_parameters(
      T('NoNameGivenFlag', None, False, '--day'),
      T('NoNameGivenPositional', None, True, 'DAY'),
  )
  def testGetPresentationNone(self, name, positional, expected_name):
    with self.assertRaisesRegex(exceptions.InitializationError,
                                'Concept name required.'):
      concepts.DayOfWeek(name, positional=positional, help_text='h')


class DurationTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', '1h2m', None, 3720),
      T('FromFallthrough', None, '2m5s', 125),
      T('FromArgsFirst', '8h', '3m20s', 28800),
      T('ConvertFromFallthrough', None, '1d', 86400),
      T('ZeroNoUnit', '0', None, 0),
      T('NoUnit', '1234', None, 1234),

      T('MinClosedLT', '20m', None, None,
        min_endpoint=concepts.Endpoint('1h'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[20m\] '
                         r'must be greater than or equal to \[1h\].')),
      T('MinClosedEQ', '1h', None, 3600.0,
        min_endpoint=concepts.Endpoint('1h')),
      T('MinClosedGT', '3h', None, 10800,
        min_endpoint=concepts.Endpoint('1h')),

      T('MinOpenLT', '20m', None, None,
        min_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[20m\] '
                         r'must be greater than \[1h\].')),
      T('MinOpenEQ', '1h', None, None,
        min_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[1h\] must '
                         r'be greater than \[1h\].')),
      T('MinOpenGT', '3h', None, 10800,
        min_endpoint=concepts.Endpoint('1h', closed=False)),
      T('MaxClosedLT', '59m59s', None, 3599,
        max_endpoint=concepts.Endpoint('1h')),
      T('MaxClosedEQ', '1h', None, 3600,
        max_endpoint=concepts.Endpoint('1h')),
      T('MaxClosedGT', '1h1s', None, None,
        max_endpoint=concepts.Endpoint('1h'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[1h1s\] '
                         r'must be less than or equal to \[1h\].')),
      T('MaxOpenLT', '45m', None, 2700,
        max_endpoint=concepts.Endpoint('1h', closed=False)),
      T('MaxOpenEQ', '1h', None, None,
        max_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[1h\] must '
                         r'be less than \[1h\].')),
      T('MaxOpenGT', '2h', None, None,
        max_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--delay\]. Value \[2h\] must '
                         r'be less than \[1h\].')),

      T('MinBad', '5m', None, None,
        min_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid min endpoint \[abc\] for \[--delay\]. "
                         r"Failed to parse duration \[abc\]: Duration unit "
                         r"'abc' must be preceded by a number.")),
      T('MaxBad', '0s', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r"Invalid max endpoint \[xyz\] for \[--delay\]. "
                         r"Failed to parse duration \[xyz\]: Duration unit "
                         r"'xyz' must be preceded by a number.")),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r"Failed to parse \[--delay\]. Failed to parse "
                         r"duration \[xyz\]: Duration unit 'xyz' must be "
                         r"preceded by a number.")),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r"Failed to parse \[--delay\]. Failed to parse "
                         r"duration \[xyz\]: Duration unit 'xyz' must be "
                         r"preceded by a number.")),
  )
  def testDurationParse(self, arg_fallthrough_value, fallthrough_value,
                        expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'delay': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--delay'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'delay', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.Duration, expected_result, dependency_view,
                   attr, kwargs)

  def testDurationBuildHelpText(self):
    concept = concepts.Duration('delay', help_text='Provide a delay.')
    self.assertEqual('Provide a delay. Must be a string representing an ISO '
                     '8601 duration. Syntax is relaxed to ignore case, the '
                     'leading P and date/time separator T if there is no '
                     'ambiguity. The default suffix is `s`. For example, '
                     '`PT1H` and `1h` are equivalent representations of one '
                     'hour. See $ gcloud topic datetimes for more information.',
                     concept.BuildHelpText())


class TimeStampTest(ConceptParseViewBase):

  def SetUp(self):
    self.StartObjectPatch(times, 'Now', return_value=times.ParseDateTime(
        '2016-05-26T00:05:00.000Z'))

  @parameterized.named_parameters(
      T('FromArgs', '2014-01-06T09:00:00-0400', None,
        '2014-01-06T13:00:00.000Z'),
      T('FromFallthrough', None, '+2m5s', '2016-05-26T00:07:05.000Z'),
      T('FromArgsFirst', '8h', '3m20s', '2016-05-26T08:00:00.000Z'),
      T('ConvertFromFallthrough', None, '1d', '2016-05-27T00:05:00.000Z'),
      T('ZeroNoUnit', '0', None, 0,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--timestamp\]. Failed to parse '
                         r'duration \[0\]: Day is out of range for month.')),

      T('MinClosedLT', '20m', None, None,
        min_endpoint=concepts.Endpoint('1h'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T00:20:00.000Z\] must be greater than '
                         r'or equal to \[2016-05-26T01:00:00.000Z\].')),
      T('MinClosedEQ', '1h', None, '2016-05-26T01:00:00.000Z',
        min_endpoint=concepts.Endpoint('1h')),
      T('MinClosedGT', '3h', None, '2016-05-26T03:00:00.000Z',
        min_endpoint=concepts.Endpoint('1h')),

      T('MinOpenLT', '2017-01-01', None, None,
        min_endpoint=concepts.Endpoint('2018-01-01', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2017-01-01T00:00:00.000Z\] must be greater than '
                         r'\[2018-01-01T00:00:00.000Z\].')),
      T('MinOpenEQ', '1h', None, None,
        min_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T01:00:00.000Z\] must be greater than '
                         r'\[2016-05-26T01:00:00.000Z\].')),
      T('MinOpenGT', '2016-05-26T03:00', None, '2016-05-26T03:00:00.000Z',
        min_endpoint=concepts.Endpoint('2016-05-26T01:00', closed=False)),
      T('MaxClosedLT', '59m59s', None, '2016-05-26T00:59:59.000Z',
        max_endpoint=concepts.Endpoint('1h')),
      T('MaxClosedEQ', '1h', None, '2016-05-26T01:00:00.000Z',
        max_endpoint=concepts.Endpoint('1h')),
      T('MaxClosedGT', '1h1s', None, '2016-05-26 01:00:00-07:00',
        max_endpoint=concepts.Endpoint('1h'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T01:00:01.000Z\] must be less than '
                         r'or equal to \[2016-05-26T01:00:00.000Z\].')),
      T('MaxOpenLT', '45m', None, '2016-05-26T00:45:00.000Z',
        max_endpoint=concepts.Endpoint('1h', closed=False)),
      T('MaxOpenEQ', '1h', None, None,
        max_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T01:00:00.000Z\] must be less than '
                         r'\[2016-05-26T01:00:00.000Z\].')),
      T('MaxOpenGT', '2h', None, None,
        max_endpoint=concepts.Endpoint('1h', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T02:00:00.000Z\] must be less than '
                         r'\[2016-05-26T01:00:00.000Z\].')),

      T('MinBad', '5m', None, None,
        max_endpoint=concepts.Endpoint('1'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--timestamp\]. Value '
                         r'\[2016-05-26T00:05:00.000Z\] must be less than '
                         r'or equal to \[2016-05-01T00:00:00.000Z\].')),
      T('MaxBad', '0s', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[xyz\] for \[--timestamp\]. '
                         r'Failed to parse duration \[xyz\]:.+')),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'xyz', None, None,
        exception=exceptions.ParseError,
        exception_regex=(
            r'Failed to parse \[--timestamp\]. Failed to parse '
            r'duration \[xyz\]:.+')),
      T('InvalidFromFallthrough',
        None,
        'xyz',
        None,
        exception=exceptions.ParseError,
        exception_regex=(
            r'Failed to parse \[--timestamp\]. Failed to parse '
            r'duration \[xyz\]:.+')),
  )
  def testTimeStampParse(self, arg_fallthrough_value, fallthrough_value,
                         expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'timestamp': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--timestamp'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {
        'name': 'timestamp',
        'help_text': 'help',
        'required': True,
        'string': True,
        'fmt': '',
        'tz': times.UTC,
    }
    self.ParseView(concepts.TimeStamp, expected_result, dependency_view,
                   attr, kwargs)

  def testTimeStampBuildHelpText(self):
    concept = concepts.TimeStamp('timestamp', help_text='Provide a timestamp.')
    self.assertEqual('Provide a timestamp. Must be a string representing an '
                     'ISO 8601 date/time. Relative durations (prefixed by - or '
                     '+) may be used to specify offsets from the current time. '
                     'See $ gcloud topic datetimes for more information.',
                     concept.BuildHelpText())

  def testTimeStampBoundariesBuildHelpText(self):
    concept = concepts.TimeStamp(
        'timestamp',
        min_endpoint=concepts.Endpoint('1970-01-01T00:00:00Z'),
        max_endpoint=concepts.Endpoint('2100-01-01T00:00:00Z', closed=False),
        help_text='Provide a timestamp.',
    )
    self.assertEqual('Provide a timestamp. Must be a string representing an '
                     'ISO 8601 date/time. Relative durations (prefixed by - or '
                     '+) may be used to specify offsets from the current time. '
                     'The value must be greater than or equal to '
                     '1970-01-01T00:00:00.000Z and less than '
                     '2100-01-01T00:00:00.000Z. See $ gcloud topic datetimes '
                     'for more information.',
                     concept.BuildHelpText())


class SemVerTest(ConceptParseViewBase):

  @parameterized.named_parameters(
      T('FromArgs', '1.2.3', None, semver.SemVer('1.2.3')),
      T('FromFallthrough', None, '4.5.0', semver.SemVer('4.5.0')),
      T('FromArgsFirst', '1.1.0', '0.9.1', semver.SemVer('1.1.0')),
      T('One', '1', None, semver.SemVer('1.0.0')),
      T('Two', '1.2', None, semver.SemVer('1.2.0')),
      T('Four', '1.2.3.4', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--version\]. The value is not a '
                         r'valid SemVer string: \[1.2.3.4\]')),
      T('Invalid', 'a.b.c', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--version\]. The value is not a '
                         r'valid SemVer string: \[a.b.c\]')),

      T('MinClosedLT', '1.9.9', None, None,
        min_endpoint=concepts.Endpoint('2.0.0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[1.9.9\] must be greater than or equal to '
                         r'\[2.0.0\].')),
      T('MinClosedEQ', '2.0.0', None, semver.SemVer('2.0.0'),
        min_endpoint=concepts.Endpoint('2.0.0')),
      T('MinClosedGT', '3.1.9', None, semver.SemVer('3.1.9'),
        min_endpoint=concepts.Endpoint('2.0.0')),

      T('MinOpenLT', '1.9.9', None, None,
        min_endpoint=concepts.Endpoint('2.0.0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[1.9.9\] must be greater than '
                         r'\[2.0.0\].')),
      T('MinOpenEQ', '2.0.0', None, semver.SemVer('2.0.0'),
        min_endpoint=concepts.Endpoint('2.0.0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[2.0.0\] must be greater than '
                         r'\[2.0.0\].')),
      T('MinOpenGT', '3.1.9', None, semver.SemVer('3.1.9'),
        min_endpoint=concepts.Endpoint('2.0.0', closed=False)),

      T('MaxClosedLT', '1.9.9', None, semver.SemVer('1.9.9'),
        max_endpoint=concepts.Endpoint('2.0.0')),
      T('MaxClosedEQ', '2.0.0', None, semver.SemVer('2.0.0'),
        max_endpoint=concepts.Endpoint('2.0.0')),
      T('MaxClosedGT', '3.1.9', None, semver.SemVer('3.1.9'),
        max_endpoint=concepts.Endpoint('2.0.0'),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[3.1.9\] must be less than or equal to '
                         r'\[2.0.0\].')),

      T('MaxOpenLT', '1.9.9', None, semver.SemVer('1.9.9'),
        max_endpoint=concepts.Endpoint('2.0.0', closed=False)),
      T('MaxOpenEQ', '2.0.0', None, semver.SemVer('2.0.0'),
        max_endpoint=concepts.Endpoint('2.0.0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[2.0.0\] must be less than '
                         r'\[2.0.0\].')),
      T('MaxOpenGT', '3.1.9', None, semver.SemVer('3.1.9'),
        max_endpoint=concepts.Endpoint('2.0.0', closed=False),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--version\]. Value '
                         r'\[3.1.9] must be less than \[2.0.0\].')),

      T('MinBad', '1.0.0', None, None,
        max_endpoint=concepts.Endpoint('abc'),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[abc\] for \[--version\]. The '
                         r'value is not a valid SemVer string: \[abc.0.0\].')),
      T('MaxBad', '2.0.1', None, None,
        max_endpoint=concepts.Endpoint('xyz', closed=False),
        exception=exceptions.ConstraintError,
        exception_regex=(r'Invalid max endpoint \[xyz\] for \[--version\]. The '
                         r'value is not a valid SemVer string: \[xyz.0.0\].')),
      T('Required', None, None, None,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=r'hinthinthint'),
      T('InvalidFromArg', 'abc', None, None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--version\]. The value is not a '
                         r'valid SemVer string: \[abc.0.0\]')),
      T('InvalidFromFallthrough', None, 'xyz', None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--version\]. The value is not a '
                         r'valid SemVer string: \[xyz.0.0\]')),
  )
  def testSemVerParse(self, arg_fallthrough_value, fallthrough_value,
                      expected_result, kwargs=None):
    parsed_args = core_completer_test_base.MockNamespace(
        args={'version': arg_fallthrough_value})
    fallthroughs = [
        deps.ArgFallthrough('--version'),
        deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint')]
    dependency_view = dependency_managers.DependencyViewFromValue(
        functools.partial(deps.GetFromFallthroughs, fallthroughs, parsed_args))
    attr = {'name': 'version', 'help_text': 'help', 'required': True}
    self.ParseView(concepts.SemVer, expected_result, dependency_view,
                   attr, kwargs)

  def testSemVerBuildHelpText(self):
    concept = concepts.SemVer('version', help_text='Provide a version.')
    self.assertEqual('Provide a version. Must be a string representing a '
                     'SemVer number of the form _MAJOR_._MINOR_._PATCH_, where '
                     'omitted trailing parts default to 0. See '
                     'https://semver.org/ for more information.',
                     concept.BuildHelpText())


class ParseTest(ConceptParseArgsBase):

  def testArgConceptDup(self):
    attr = {
        'name': 'string',
        'fallthroughs': [
            deps.Fallthrough(lambda: None, hint='hinthinthint'),
        ],
        'help_text': 'help',
        'required': False,
    }
    kwargs = {
        'exception': argparse.ArgumentError,
        'exception_regex': (r'argument --string: conflicting option '
                            r'string.*: --string'),
    }
    self.parser.add_argument('--string', help='help')
    self.ParseArgs(concepts.String, 'str', ['--string', 'str'], attr, kwargs)


class ListTest(ConceptParseArgsBase):

  @parameterized.named_parameters(
      T('FromArgs', ['--list=e1,e2'], None, ['e1', 'e2']),
      T('FromFallthrough', [], '^;^e,3;e,4', ['e,3', 'e,4']),
      T('FromArgsFirst', ['--list=^;^e,3;e,4'], 'e5,e6', ['e,3', 'e,4']),

      T('Empty', [], None, None),
      T('One', ['--list=one'], None, ['one']),
      T('Two', ['--list=one,two'], None, ['one', 'two']),

      T('ZeroRequired', [], None, [],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        required=True,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=('No value was provided for \\[--list\\]: Failed to '
                         'find attribute. The attribute can be set in the '
                         'following ways:')),
      T('ConstraintsZero', [], None, None,
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1)),
      T('ConstraintsOne', ['--list=one'], None, ['one'],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1)),
      T('ConstraintsTwo', ['--list=one,two'], None, ['one', 'two'],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--list\]. List length \[2\] '
                         r'must be less than or equal to \[1\].')),
  )
  def testStringListParse(self, args, fallthrough_value,
                          expected_result, kwargs=None):
    attr = {
        'name': 'list',
        'element': concepts.String('item'),
        'fallthroughs': [
            deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint'),
        ],
        'help_text': 'help',
        'required': False,
    }
    self.ParseArgs(concepts.List, expected_result, args, attr, kwargs)

  def testStringListHelp(self):
    concept = concepts.List(
        'list',
        element=concepts.String('item', help_text='Items are special strings.'),
        help_text='Provide an item.')
    self.assertEqual('Provide an item. Must be a string representing a list '
                     'of `,` separated item values. Items are special '
                     'strings. See '
                     '$ gcloud topic escaping for details on using alternate '
                     'delimiters.',
                     concept.BuildHelpText())

  def testStringListSizeHelp(self):
    concept = concepts.List(
        'list',
        element=concepts.String('item', help_text='Items are special strings.'),
        help_text='Provide an item.',
        min_endpoint=concepts.Endpoint('1'),
        max_endpoint=concepts.Endpoint('8'))
    self.assertEqual('Provide an item. Must be a string representing a list '
                     'of `,` separated item values. The list length must be '
                     'greater than or equal to 1 and less than or equal to 8. '
                     'Items are special strings. See $ gcloud topic escaping '
                     'for details on using alternate delimiters.',
                     concept.BuildHelpText())

  @parameterized.named_parameters(
      T('FromArgs', ['--sizes=1k,2Gi'], None, [1000, 2147483648]),
      T('FromFallthrough', [], '^;^3MiB;2GB', [3145728, 2000000000]),
      T('FromArgsFirst', ['--sizes=^;^3MiB;2GB'], '4,8', [3145728, 2000000000]),

      T('ZeroRequired', [], None, [],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        required=True,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=('No value was provided for \\[--sizes\\]: Failed to '
                         'find attribute. The attribute can be set in the '
                         'following ways:')),
      T('Zero', [], None, None,
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1)),
      T('One', ['--sizes=one'], None, ['one'],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--size\]. Failed to parse '
                         r'binary/decimal scaled integer \[one\]: \[one\] must '
                         r'the form INTEGER\[UNIT\]\[B\] where units may be '
                         r'one of \[kB,kiB,MB,MiB,GB,GiB,TB,TiB,PB,PiB\].')),
  )
  def testScaledIntegerListParse(self, args, fallthrough_value,
                                 expected_result, kwargs=None):
    attr = {
        'name': 'sizes',
        'element': concepts.ScaledInteger('size'),
        'fallthroughs': [
            deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint'),
        ],
        'help_text': 'help',
        'required': False,
    }
    self.ParseArgs(concepts.List, expected_result, args, attr, kwargs)

  def testScaledIntegerListHelp(self):
    concept = concepts.List(
        'sizes',
        element=concepts.ScaledInteger(
            'capacity', help_text='Specifies the capacity of a bank.'),
        help_text='Provide a capacity.')
    self.assertEqual('Provide a capacity. Must be a string representing a list '
                     'of `,` separated capacity values. Specifies the '
                     'capacity of a bank. Must be a string representing an '
                     'ISO/IEC Decimal/Binary scaled integer. For example, 1k '
                     '== 1000 and 1ki == 1024. The default type abbreviation '
                     'is `B`. See '
                     'https://en.wikipedia.org/wiki/Binary_prefix for details. '
                     'See $ gcloud topic escaping for details on using '
                     'alternate delimiters.',
                     concept.BuildHelpText())

  def testImplicitStringListHelp(self):
    concept = concepts.List(
        'ids',
        help_text='Provide some ids.')
    self.assertEqual('Provide some ids. Must be a string representing a list '
                     'of `,` separated ids values. Each item is a string '
                     'value. See $ gcloud topic escaping for details on using '
                     'alternate delimiters.',
                     concept.BuildHelpText())


class DictTest(ConceptParseArgsBase):

  def SetUp(self):
    self.entries = [
        concepts.BinaryScaledInteger('binary_scaled_integer'),
        concepts.Boolean('boolean'),
        concepts.DayOfWeek('day'),
        concepts.Duration('duration'),
        concepts.Float('float'),
        concepts.Integer('integer'),
        concepts.ScaledInteger('scaled_integer'),
        concepts.String('string'),
        concepts.TimeStamp('timestamp'),
    ]

  @parameterized.named_parameters(
      T('SomeValues',
        ['--dict=string=STRING,integer=123'],
        None,
        {
            'integer': 123,
            'string': 'STRING',
        },
       ),
      T('AllValues',
        ['--dict=binary_scaled_integer=1KiB,boolean=true,day=monday,'
         'duration=1h20s,float=3.1415,integer=99,scaled_integer=1MB,'
         'string=abc.xyz,timestamp=2018-08-11T01:02:03.04Z'],
        None,
        {
            'binary_scaled_integer': 1024,
            'boolean': True,
            'day': 'MON',
            'duration': 3620.0,
            'float': 3.1415,
            'integer': 99,
            'scaled_integer': 1000000,
            'string': 'abc.xyz',
            'timestamp': datetime.datetime(2018, 8, 11, 1, 2, 3, 40000,
                                           tzinfo=times.UTC),
        },
       ),
      T('ZeroRequired', [], None, [],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        required=True,
        exception=exceptions.MissingRequiredArgumentError,
        exception_regex=('No value was provided for \\[--dict\\]: Failed to '
                         'find attribute. The attribute can be set in the '
                         'following ways:')),
      T('ConstraintsZero', [], None, None,
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1)),
      T('ConstraintsOne', ['--dict=integer=123'], None, {'integer': 123},
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1)),
      T('ConstraintsTwo', ['--dict=integer=1,string=two'], None, [1, 'two'],
        min_endpoint=concepts.Endpoint(1),
        max_endpoint=concepts.Endpoint(1),
        exception=exceptions.ValidationError,
        exception_regex=(r'Failed to validate \[--dict\]. Number of entries '
                         r'\[2\] must be less than or equal to \[1\].')),
      T('BadKey',
        ['--dict=foo=bar'],
        None,
        None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--dict\]. Unknown dictionary key '
                         r'\[foo\].'),
       ),
      T('BadValue',
        ['--dict=integer=bogus'],
        None,
        None,
        exception=exceptions.ParseError,
        exception_regex=(r'Failed to parse \[--integer\]. Invalid literal for '
                         r"int\(\) with base 10: 'bogus'."),
       ),
      T('AdditionalStringKey',
        ['--dict=foo=123'],
        None,
        {'foo': '123'},
        additional=concepts.String,
       ),
      T('AdditionalIntegerKey',
        ['--dict=foo=123'],
        None,
        {'foo': 123},
        additional=concepts.Integer,
       ),
  )
  def testStringDictParse(self, args, fallthrough_value,
                          expected_result, kwargs=None):
    attr = {
        'name': 'dict',
        'entries': self.entries,
        'fallthroughs': [
            deps.Fallthrough(lambda: fallthrough_value, hint='hinthinthint'),
        ],
        'help_text': 'help',
        'required': False,
    }
    self.ParseArgs(concepts.Dict, expected_result, args, attr, kwargs)

  def testStringDictHelp(self):
    concept = concepts.Dict(
        'dict',
        entries=self.entries,
        help_text='Provide an entry.')
    self.assertEqual("""\
Provide an entry. Must be a string representing a list of `,` separated _key_=_value_ pairs. _key_ must be one of:
+
*binary_scaled_integer*::: Must be a string representing binary scaled integer where all ISO/IEC prefixes are powers of 2. For example, 1k == 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*boolean*::: A Boolean value.
*day*::: Must be a string representing a day of the week in English, such as 'MON' or 'FRI'. Case is ignored, and any characters after the first three are ignored.
*duration*::: Must be a string representing an ISO 8601 duration. Syntax is relaxed to ignore case, the leading P and date/time separator T if there is no ambiguity. The default suffix is `s`. For example, `PT1H` and `1h` are equivalent representations of one hour. See $ gcloud topic datetimes for more information.
*float*::: Must be a string representing a floating point number.
*integer*::: Must be a string representing an integer.
*scaled_integer*::: Must be a string representing an ISO/IEC Decimal/Binary scaled integer. For example, 1k == 1000 and 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*string*::: A string value.
*timestamp*::: Must be a string representing an ISO 8601 date/time. Relative durations (prefixed by - or +) may be used to specify offsets from the current time. See $ gcloud topic datetimes for more information.
""",
                     concept.BuildHelpText())

  def testStringAdditionalIntegerDictHelp(self):
    concept = concepts.Dict(
        'dict',
        entries=self.entries,
        additional=concepts.Integer,
        help_text='Provide an entry.')
    self.assertEqual("""\
Provide an entry. Must be a string representing a list of `,` separated _key_=_value_ pairs. _key_ may be one of:
+
*binary_scaled_integer*::: Must be a string representing binary scaled integer where all ISO/IEC prefixes are powers of 2. For example, 1k == 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*boolean*::: A Boolean value.
*day*::: Must be a string representing a day of the week in English, such as 'MON' or 'FRI'. Case is ignored, and any characters after the first three are ignored.
*duration*::: Must be a string representing an ISO 8601 duration. Syntax is relaxed to ignore case, the leading P and date/time separator T if there is no ambiguity. The default suffix is `s`. For example, `PT1H` and `1h` are equivalent representations of one hour. See $ gcloud topic datetimes for more information.
*float*::: Must be a string representing a floating point number.
*integer*::: Must be a string representing an integer.
*scaled_integer*::: Must be a string representing an ISO/IEC Decimal/Binary scaled integer. For example, 1k == 1000 and 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*string*::: A string value.
*timestamp*::: Must be a string representing an ISO 8601 date/time. Relative durations (prefixed by - or +) may be used to specify offsets from the current time. See $ gcloud topic datetimes for more information.
```*```::: Additional _key_ names are allowed. Each _value_ must be a string representing an integer.
""",
                     concept.BuildHelpText())

  def testAdditionalIntegerDictHelp(self):
    concept = concepts.Dict(
        'dict',
        additional=concepts.Integer,
        help_text='Provide an entry.')
    self.assertEqual("""\
Provide an entry. Must be a string representing a list of `,` separated _key_=_value_ pairs. _key_ may be one of:
+
```*```::: Any _key_ name is accepted. Each _value_ must be a string representing an integer.
""",
                     concept.BuildHelpText())

  def testImplicitAdditionalStringDictHelp(self):
    concept = concepts.Dict(
        'dict',
        help_text='Provide an entry.')
    self.assertEqual("""\
Provide an entry. Must be a string representing a list of `,` separated _key_=_value_ pairs. _key_ may be one of:
+
```*```::: Any _key_ name is accepted. Each _value_ is a string value.
""",
                     concept.BuildHelpText())

  def testStringDictSizeHelp(self):
    concept = concepts.Dict(
        'dict',
        entries=self.entries,
        help_text='Provide an entry.',
        min_endpoint=concepts.Endpoint('1'),
        max_endpoint=concepts.Endpoint('8'))
    self.assertEqual("""\
Provide an entry. Must be a string representing a list of `,` separated _key_=_value_ pairs. The number of entries must be greater than or equal to 1 and less than or equal to 8. _key_ must be one of:
+
*binary_scaled_integer*::: Must be a string representing binary scaled integer where all ISO/IEC prefixes are powers of 2. For example, 1k == 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*boolean*::: A Boolean value.
*day*::: Must be a string representing a day of the week in English, such as 'MON' or 'FRI'. Case is ignored, and any characters after the first three are ignored.
*duration*::: Must be a string representing an ISO 8601 duration. Syntax is relaxed to ignore case, the leading P and date/time separator T if there is no ambiguity. The default suffix is `s`. For example, `PT1H` and `1h` are equivalent representations of one hour. See $ gcloud topic datetimes for more information.
*float*::: Must be a string representing a floating point number.
*integer*::: Must be a string representing an integer.
*scaled_integer*::: Must be a string representing an ISO/IEC Decimal/Binary scaled integer. For example, 1k == 1000 and 1ki == 1024. The default type abbreviation is `B`. See https://en.wikipedia.org/wiki/Binary_prefix for details.
*string*::: A string value.
*timestamp*::: Must be a string representing an ISO 8601 date/time. Relative durations (prefixed by - or +) may be used to specify offsets from the current time. See $ gcloud topic datetimes for more information.
""",
                     concept.BuildHelpText())


if __name__ == '__main__':
  test_case.main()
