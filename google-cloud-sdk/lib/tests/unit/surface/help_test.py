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

from tests.lib import cli_test_base


class HelpTest(cli_test_base.CliTestBase):

  def testHelpGroupHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('-h')
    self.AssertOutputContains('Usage: gcloud [optional flags]')

  def testHelpCommandHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info -h')
    self.AssertOutputContains('Usage: gcloud info [optional flags]')

  def testHelpGroupHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('--help')
    self.AssertOutputContains('gcloud - manage Google Cloud Platform resources '
                              'and developer workflow')

  def testHelpCommandHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info --help')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')

  def testHelpGroupHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help')
    self.AssertOutputContains('gcloud - manage Google Cloud Platform resources '
                              'and developer workflow')

  def testHelpCommandHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help info')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')

  def testHelpBadCommandUnknownHFlag(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r"Invalid choice: 'junk'."):
      self.Run('junk -h')

  def testHelpBadSecondCommandUnknownHFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info junk -h')
    self.AssertOutputContains('Usage: gcloud info [optional flags]')

  def testHelpBadCommandUnknownHelpFlag(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r"Invalid choice: 'junk'."):
      self.Run('junk --help')

  def testHelpBadSecondCommandUnknownHelpFlag(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('info junk --help')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')

  def testHelpBadCommandUnknownHelp(self):
    with self.AssertRaisesArgumentErrorRegexp(
        r"Invalid choice: 'junk'."):
      self.Run('help junk')

  def testHelpBadSecondCommandUnknownHelp(self):
    with self.assertRaisesRegex(SystemExit, '0'):
      self.Run('help info junk')
    self.AssertOutputContains('gcloud info - display information about the '
                              'current gcloud environment')


if __name__ == '__main__':
  cli_test_base.main()
