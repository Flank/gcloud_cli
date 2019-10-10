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
"""Tests for the concepts v2 base.py module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.concepts import base
from tests.lib import parameterized
from tests.lib import test_case


class TestConcept(base.Concept):
  """Test concept."""

  def GetPresentationName(self):
    pass

  def Parse(self, _):
    pass

  def Attribute(self):
    pass

  def BuildHelpText(self):
    pass

  def IsArgRequired(self):
    pass


class BaseTest(test_case.TestCase,
               parameterized.TestCase):

  @parameterized.named_parameters(
      ('Defaults',
       {'name': 'name', 'help_text': 'help'},
       'name', 'name', 'help', False),
      ('NonDefaults',
       {'name': 'name', 'help_text': 'help', 'key': 'k', 'required': True},
       'name', 'k', 'help', True))
  def testBaseConcept(self, kwargs, expected_name, expected_key, expected_help,
                      expected_required):
    concept = TestConcept(**kwargs)
    self.assertEqual(expected_name, concept.name)
    self.assertEqual(expected_key, concept.key)
    self.assertEqual(expected_help, concept.help_text)
    self.assertEqual(expected_required, concept.required)

  @parameterized.named_parameters(
      ('Defaults', {}, [], {}),
      ('Fallthroughs',
       {'fallthroughs': [deps.Fallthrough(lambda: '!', hint='h')]},
       [deps.Fallthrough(lambda: '!', hint='h')],
       {}),
      ('OtherKwargs',
       {'fallthroughs': [deps.Fallthrough(lambda: '!', hint='h')],
        'required': True},
       [deps.Fallthrough(lambda: '!', hint='h')],
       {'required': True}))
  def testAttribute(self, kwargs, expected_fallthroughs, expected_kwargs):
    concept = TestConcept(name='foo', key='k', help_text='help')
    self.StartObjectPatch(concept, 'GetPresentationName', return_value='--foo')

    result = base.Attribute(concept=concept, **kwargs)

    self.assertEqual(concept, result.concept)
    self.assertEqual('--foo', result.arg_name)
    self.assertEqual(
        [(f.GetValue(None), f.hint)for f in expected_fallthroughs],
        [(f.GetValue(None), f.hint) for f in result.fallthroughs])
    self.assertEqual(expected_kwargs, result.kwargs)

  @parameterized.named_parameters(
      ('NoKwargs',
       {'attributes': [
           base.Attribute(concept=TestConcept(name='a', key='k1'))]},
       {}),
      ('Kwargs',
       {'attributes': [
           base.Attribute(concept=TestConcept(name='a', key='k1'))],
        'mutex': True},
       {'mutex': True}))
  def testAttributeGroup(self, kwargs, expected_kwargs):
    concept = TestConcept(name='c', key='k')

    result = base.AttributeGroup(concept=concept, **kwargs)

    self.assertEqual(concept, result.concept)
    self.assertEqual(kwargs.get('attributes'), result.attributes)
    self.assertEqual(expected_kwargs, result.kwargs)


if __name__ == '__main__':
  test_case.main()
