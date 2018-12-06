# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for usage_text.TextChoiceSuggester."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import usage_text
from tests.lib import sdk_test_base
from tests.lib import test_case


GCLOUD_COMMANDS = [
    'app', 'auth', 'components', 'config', 'dns', 'preview', 'sql', 'help',
    'init', 'interactive', 'version']


class EditDistanceTest(sdk_test_base.SdkBase):

  def testCommandChoice(self):
    tester = usage_text.TextChoiceSuggester(GCLOUD_COMMANDS)
    self.assertEqual('app', tester.GetSuggestion('apa'))
    self.assertEqual('config', tester.GetSuggestion('confg'))
    self.assertEqual('components', tester.GetSuggestion('componets'))
    self.assertEqual('app', tester.GetSuggestion('ap'))
    self.assertEqual('init', tester.GetSuggestion('int'))

    tester = usage_text.TextChoiceSuggester(['yaml', 'Ybad'])
    self.assertEqual('yaml', tester.GetSuggestion('YAML'))

  def testAliases(self):
    tester = usage_text.TextChoiceSuggester(GCLOUD_COMMANDS)
    tester.AddAliases(['foo', 'bar'], 'components')
    tester.AddAliases(['app'], 'components')
    self.assertEqual('components', tester.GetSuggestion('foo'))
    self.assertEqual('components', tester.GetSuggestion('fooo'))
    # Adding an alias for an existing item should not clobber it.
    self.assertEqual('app', tester.GetSuggestion('app'))

  def testCommandChoice_DistanceTooFar(self):
    tester = usage_text.TextChoiceSuggester(['ssh'])
    self.assertEqual(None, tester.GetSuggestion('help'))


if __name__ == '__main__':
  test_case.main()
