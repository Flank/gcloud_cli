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

"""Test concepts to be used in test commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.concepts import base
from googlecloudsdk.command_lib.concepts import names
from googlecloudsdk.command_lib.concepts.all_concepts import concepts
from googlecloudsdk.core import properties


class FooBar(object):
  """Result of FooBarArg.Parse()."""

  def __init__(self, foo, bar):
    self.foo = foo
    self.bar = bar


class FooBarArg(base.Concept):
  """A group arg with two attributes."""

  def __init__(self, name='foo-bar', prefixes=False, **kwargs):
    self.prefixes = prefixes
    super(FooBarArg, self).__init__(name, **kwargs)

  def Attribute(self):
    return base.AttributeGroup(
        concept=self,
        attributes=[
            concepts.SimpleArg(
                name=self._GetSubConceptName('foo'),
                key='foo', help_text='A foo',
                fallthroughs=[
                    deps_lib.PropertyFallthrough(
                        properties.VALUES.core.project)]
                ).Attribute(),
            concepts.SimpleArg(
                name=self._GetSubConceptName('bar'),
                key='bar', help_text='A bar').Attribute()],
        help=self.BuildHelpText())

  def Parse(self, dependencies):
    return FooBar(dependencies.foo, dependencies.bar)

  def _GetSubConceptName(self, attribute_name):
    if self.prefixes:
      return names.ConvertToNamespaceName(self.name + '_' + attribute_name)
    return attribute_name

  def BuildHelpText(self):
    return '{} This is a foobar concept.'.format(self.help_text)

  def GetPresentationName(self):
    return names.ConvertToNamespaceName(self.name)


class Baz(object):
  """Result of DoubleFooBar.Parse()."""

  def __init__(self, first_foobar, second_foobar):
    self.first = first_foobar
    self.second = second_foobar


class DoubleFooBar(base.Concept):
  """A concept with two nested group concepts."""

  def __init__(self, name='baz', **kwargs):  # pylint: disable=useless-super-delegation
    super(DoubleFooBar, self).__init__(name, **kwargs)

  def Attribute(self):
    return base.AttributeGroup(
        concept=self,
        attributes=[
            FooBarArg(name='first', help_text='the first foobar',
                      prefixes=True).Attribute(),
            FooBarArg(name='second', help_text='the second foobar',
                      prefixes=True).Attribute()],
        help=self.BuildHelpText())

  def BuildHelpText(self):
    return '{} This is a concept with two group concepts inside it!'.format(
        self.help_text)

  def Parse(self, dependencies):
    return Baz(dependencies.first, dependencies.second)

  def GetPresentationName(self):
    return names.ConvertToNamespaceName(self.name)
