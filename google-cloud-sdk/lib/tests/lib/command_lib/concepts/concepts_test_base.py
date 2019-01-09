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
"""Test mixin for concepts v2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.concepts.all_concepts import concepts
from tests.lib.calliope.concepts import concepts_test_base
from tests.lib.command_lib.concepts import test_concepts


class ConceptArgsTestBase(concepts_test_base.GenericConceptsTestBase):
  """Mixin for testing concepts v2."""

  def SetUp(self):
    self.string_concept = concepts.String(
        name='c', help_text='String concept help.')
    self.fallthrough_concept = concepts.String(
        name='c', help_text='String concept with fallthrough help.',
        fallthroughs=[self.fallthrough])
    self.group_arg_concept = test_concepts.MakeDoubleFooBar(
        'baz', 'Group concept help.')
    self.integer_concept = concepts.Integer(
        name='int', help_text='Integer concept help.')
    self.day_of_week_concept = concepts.DayOfWeek(
        name='foo-day', help_text='Day of Week concept help.')
