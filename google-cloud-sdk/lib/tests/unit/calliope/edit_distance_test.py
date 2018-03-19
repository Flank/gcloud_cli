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

  def testSynonyms(self):
    tester = usage_text.TextChoiceSuggester()
    tester.AddSynonyms()
    self.assertEqual(None, tester.GetSuggestion('add'))

    tester = usage_text.TextChoiceSuggester(['add'])
    self.assertEqual('add', tester.GetSuggestion('add'))
    # Create doesn't have the smart alias.
    self.assertEqual(None, tester.GetSuggestion('create'))
    tester.AddSynonyms()
    # We now get the smart suggestion.
    self.assertEqual('add', tester.GetSuggestion('create'))
    # Add still points to itself.
    self.assertEqual('add', tester.GetSuggestion('add'))

    tester = usage_text.TextChoiceSuggester(['remove', 'delete'])
    self.assertEqual('remove', tester.GetSuggestion('remove'))
    self.assertEqual('delete', tester.GetSuggestion('delete'))
    tester.AddSynonyms()
    # No changes to these since they are both present.
    self.assertEqual('remove', tester.GetSuggestion('remove'))
    self.assertEqual('delete', tester.GetSuggestion('delete'))

    tester = usage_text.TextChoiceSuggester(['get', 'junk'])
    tester.AddAliases(['describe'], 'junk')
    # Describe is an alias match for junk.
    self.assertEqual('junk', tester.GetSuggestion('describe'))
    tester.AddSynonyms()
    # This still maps to junk since it was an explicit alias, even though the
    # synonym would make it point to 'get'.
    self.assertEqual('junk', tester.GetSuggestion('describe'))

  def testCommandChoice_DistanceTooFar(self):
    tester = usage_text.TextChoiceSuggester(['ssh'])
    self.assertEqual(None, tester.GetSuggestion('help'))


if __name__ == '__main__':
  test_case.main()
