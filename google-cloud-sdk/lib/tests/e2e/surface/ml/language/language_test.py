# Copyright 2017 Google Inc. All Rights Reserved.
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

"""e2e tests for ml language command group."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case


class VisionTests(e2e_base.WithServiceAuth):
  """E2E tests for ml vision command group."""

  def SetUp(self):
    self.track = base.ReleaseTrack.GA

  def _RunTest(self, command, text):
    result = self.Run(
        'ml language {command} --content "{text}"'.format(command=command,
                                                          text=text))
    # Check that there is at least one response and that request didn't raise
    # an error.
    self.assertTrue(result)

  def testAnalyzeEntities(self):
    """Test analyze-entities command."""
    self._RunTest('analyze-entities', 'There are five donuts')

  def testAnalyzeSentiment(self):
    """Test analyze-sentiment command."""
    self._RunTest('analyze-sentiment', 'Donuts are pleasant.')

  def testAnalyzeSyntax_ContentFile(self):
    """Test analyze-syntax command with --content-file flag."""
    test_file = self.Resource('tests', 'e2e', 'surface', 'ml', 'language',
                              'testdata', 'test-text')
    result = self.Run(
        'ml language {} --content-file {}'.format('analyze-syntax', test_file))
    # Check that there is at least one response and that request didn't raise
    # an error.
    self.assertTrue(result)

  def testAnalyzeEntitySentiment(self):
    """Test analyze-entity-sentiment command."""
    self._RunTest('analyze-entity-sentiment', 'This content includes amazing '
                  'entities like New York and SF.')

  def testClassifyText(self):
    """Test classify-text command."""
    self.track = base.ReleaseTrack.BETA
    content = """\
    The time is always right to do what is right.
    Faith is taking the first step even when you don't see the whole staircase.
    The ultimate measure of a man is not where he stands in moments of comfort and
    convenience, but where he stands at times of challenge and controversy.
    In the end, we will remember not the words of our enemies, but the silence of
    our friends.
    """
    self._RunTest('classify-text', content)


if __name__ == '__main__':
  test_case.main()
