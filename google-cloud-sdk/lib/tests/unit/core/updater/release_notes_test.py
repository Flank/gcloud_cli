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
"""Tests for googlecloudsdk.core.updater.tests.release_notes."""

from googlecloudsdk.core import config
from googlecloudsdk.core.updater import release_notes
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.core.updater import util


class ReleaseNotesErrorTest(util.Base):

  def testBadFile(self):
    notes = release_notes.ReleaseNotes.FromURL(
        self.URLFromFile(self.Resource('Junk')))
    self.assertEqual(None, notes)


class ReleaseNotesDiffTest(util.Base):

  def SetUp(self):
    self.release_notes = release_notes.ReleaseNotes.FromURL(
        self.URLFromFile(self.Resource('RELEASE_NOTES')))

  def testGetIndex(self):
    self.assertEqual(0, self.release_notes._GetVersionIndex('0.9.78'))
    self.assertEqual(1, self.release_notes._GetVersionIndex('0.9.77'))
    self.assertEqual(4, self.release_notes._GetVersionIndex('0.9.74'))
    self.assertEqual(None, self.release_notes._GetVersionIndex('asdf'))
    self.assertEqual(None, self.release_notes._GetVersionIndex(None))

  def testGetText(self):
    text = self.release_notes.GetVersionText('0.9.77')
    self.assertIn('gcloud preview logging is now gcloud beta logging', text)
    self.assertEqual(None, self.release_notes.GetVersionText('asdf'))

    expected = """\
## 0.9.78 (2015/09/16)

### Breaking changes

*   Something here

### Other changes

*   GAE components updated to 1.9.26. Please visit
    <https://code.google.com/p/googleappengine/wiki/SdkReleaseNotes> for details.
*   Increase the default boot disk size for remote build VMs in
    `gcloud preview app deploy`.
*   The `--instance` flag to the `gcloud preview app modules set-managed-by`
    command now takes an instance name instead of an index.
*   The V1Beta4 API for sqladmin can now be accessed through the
    `gcloud beta sql` surface.
*   Usability enhancements for `gcloud beta init` and named configurations."""

    actual = self.release_notes.GetVersionText('0.9.78')
    self.assertEqual(expected, actual)

  def testDiff(self):
    items = self.release_notes.Diff(None, None)
    self.assertEqual(5, len(items))

    items = self.release_notes.Diff(None, '0.9.76')
    self.assertEqual(2, len(items))
    self.assertEqual('0.9.78', items[0][0])
    self.assertEqual('0.9.77', items[1][0])

    items = self.release_notes.Diff('0.9.76', None)
    self.assertEqual(3, len(items))
    self.assertEqual('0.9.76', items[0][0])
    self.assertEqual('0.9.75', items[1][0])
    self.assertEqual('0.9.74', items[2][0])

    items = self.release_notes.Diff('0.9.77', '0.9.75')
    self.assertEqual(2, len(items))
    self.assertEqual('0.9.77', items[0][0])
    self.assertEqual('0.9.76', items[1][0])

    items = self.release_notes.Diff('0.9.77', 'junk')
    self.assertEqual(None, items)

    items = self.release_notes.Diff('junk', '0.9.77')
    self.assertEqual(None, items)

    items = self.release_notes.Diff('0.9.77', '0.9.77')
    self.assertEqual([], items)

    items = self.release_notes.Diff('0.9.76', '0.9.77')
    self.assertEqual([], items)


class ReleaseNotesParseTest(util.Base):

  def testEmpty(self):
    notes = release_notes.ReleaseNotes('')
    self.assertEqual(0, len(notes._versions))

  def testBad(self):
    notes = release_notes.ReleaseNotes('trash')
    self.assertEqual(0, len(notes._versions))

    notes = release_notes.ReleaseNotes("""
some title here

some stuff

# thisisnotaversionline

### thisisnotaversionline

something else
    """)
    self.assertEqual(0, len(notes._versions))

  def testVersionsWithWindowsLineEndings(self):
    notes = release_notes.ReleaseNotes("""
some title here

some stuff

## 1 (date goes here)

asdf

## 0.0.0 (date goes here)

asdf

## abcdef (date goes here)

asdf

## 1.2.3-patch (date goes here)

asdf

## 1.2a_345.6.7 (date goes here)

asdf

    """.replace('\n', '\r\n'))
    expected_versions = ['1', '0.0.0', 'abcdef', '1.2.3-patch', '1.2a_345.6.7']
    versions = [version for (version, _) in notes._versions]
    self.assertEqual(expected_versions, versions)


class ReleaseNotesPrintTest(util.Base, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.release_notes_url = self.URLFromFile(self.Resource('RELEASE_NOTES'))

  def AssertGenericMessage(self, url, over_max=False):
    if over_max:
      self.AssertErrContains(
          'A lot has changed since your last upgrade.  For the latest full '
          'release notes,\nplease visit:')
    else:
      self.AssertErrContains('For the latest full release notes, please visit')
    self.AssertErrContains(url)

  def testNoPrint(self):
    release_notes.PrintReleaseNotesDiff(None, '1', '1')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff(self.release_notes_url, None, '1')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff(self.release_notes_url, '1', None)
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff('junk', '1', '1')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff(self.release_notes_url, '1', '1')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff(self.release_notes_url,
                                        '0.9.77', '0.9.77')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

    release_notes.PrintReleaseNotesDiff(self.release_notes_url,
                                        '0.9.78', '0.9.77')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url)
    self.ClearErr()

  def testPrint(self):
    release_notes.PrintReleaseNotesDiff(self.release_notes_url,
                                        '0.9.76', '0.9.78')
    self.AssertErrContains('0.9.78')
    self.AssertErrContains('0.9.77')

  def testOverMax(self):
    release_notes_url = self.URLFromFile(
        self.Resource('RELEASE_NOTES_OVER_MAX'))
    release_notes.PrintReleaseNotesDiff(release_notes_url, '1', '17')
    self.AssertGenericMessage(config.INSTALLATION_CONFIG.release_notes_url,
                              over_max=True)


if __name__ == '__main__':
  test_case.main()
