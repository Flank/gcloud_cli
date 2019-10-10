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

"""Test concepts to be used in test commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.command_lib.concepts.all_concepts import concepts
from googlecloudsdk.core import properties


def MakeFooBar(name, help_text, prefixes=False):
  """A group arg with two attributes."""
  foo = concepts.SimpleArg(
      name='foo', key='foo', help_text='A foo',
      fallthroughs=[
          deps_lib.PropertyFallthrough(properties.VALUES.core.project)
      ])
  bar = concepts.SimpleArg(name='bar', key='bar', help_text='A bar')

  foobar = concepts.GroupArg(name, prefixes=prefixes, help_text=help_text)
  foobar.AddConcept(foo)
  foobar.AddConcept(bar)
  return foobar


def MakeDoubleFooBar(name, help_text):
  """A concept with two nested group concepts."""
  first = MakeFooBar('first', 'The first foobar.', prefixes=True)
  second = MakeFooBar('second', 'The second foobar.', prefixes=True)

  group = concepts.GroupArg(name, help_text=help_text)
  group.AddConcept(first)
  group.AddConcept(second)
  return group
