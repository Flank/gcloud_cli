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

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.updater import update_manager
from tests.lib import cli_test_base


class RepositoriesTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.StartPropertyPatch(config.Paths, 'sdk_root',
                            return_value=self.temp_path)
    self.from_url_mock = self.StartObjectPatch(snapshots.ComponentSnapshot,
                                               'FromURLs')
    self.from_url_mock.return_value = None
    properties.VALUES.component_manager.snapshot_url.Set('notused')

  def CheckRepos(self, repos):
    self.assertEqual(
        ','.join(repos) if repos else None,
        properties.VALUES.component_manager.additional_repositories.Get())

  def testEverything(self):
    self.Run('components repositories list')
    self.CheckRepos(None)
    self.AssertErrContains('You have no registered component repositories')
    self.ClearErr()

    result = self.Run('components repositories add FOO')
    self.assertEqual(['FOO'], result)
    self.CheckRepos(['FOO'])
    self.AssertErrContains('Added repository: [FOO]')
    self.ClearErr()

    self.Run('components repositories list')
    self.AssertOutputContains("""\
REPOSITORY  LAST_UPDATE
FOO         Unknown
""", normalize_space=True)
    self.ClearOutput()

    result = self.Run('components repositories add BAR')
    self.assertEqual(['BAR'], result)
    self.CheckRepos(['FOO', 'BAR'])
    self.AssertErrContains('Added repository: [BAR]')
    self.ClearErr()

    self.Run('components repositories list')
    self.AssertOutputContains('FOO')
    self.AssertOutputContains('BAR')
    self.ClearOutput()

    self.WriteInput('1')
    result = self.Run('components repositories remove')
    self.assertEqual(['FOO'], result)
    self.CheckRepos(['BAR'])
    self.AssertErrContains('Removed repository: [FOO]')
    self.ClearErr()

    self.Run('components repositories list')
    self.AssertOutputContains("""\
REPOSITORY  LAST_UPDATE
BAR         Unknown
""", normalize_space=True)
    self.ClearOutput()

    self.WriteInput('1')
    result = self.Run('components repositories remove')
    self.assertEqual(['BAR'], result)
    self.CheckRepos(None)
    self.AssertErrContains('Removed repository: [BAR]')
    self.ClearErr()

    self.Run('components repositories list')
    self.AssertErrContains('You have no registered component repositories')
    self.ClearErr()

  def testEverythingByResult(self):
    result = self.Run('components repositories list')
    self.assertEqual([], list(result))
    self.CheckRepos(None)
    self.AssertErrContains('You have no registered component repositories')
    self.ClearErr()

    result = self.Run('components repositories add FOO')
    self.assertEqual(['FOO'], list(result))
    self.CheckRepos(['FOO'])
    self.AssertErrContains('Added repository: [FOO]')
    self.ClearErr()

    result = self.Run('components repositories list --format=disable')
    self.assertEqual(['FOO'], list(result))

    result = self.Run('components repositories add BAR')
    self.assertEqual(['BAR'], list(result))
    self.CheckRepos(['FOO', 'BAR'])
    self.AssertErrContains('Added repository: [BAR]')
    self.ClearErr()

    result = self.Run('components repositories list --format=disable')
    self.assertEqual(['FOO', 'BAR'], list(result))

    self.WriteInput('1')
    result = self.Run('components repositories remove')
    self.assertEqual(['FOO'], list(result))
    self.CheckRepos(['BAR'])
    self.AssertErrContains('Removed repository: [FOO]')
    self.ClearErr()

    result = self.Run('components repositories list --format=disable')
    self.assertEqual(['BAR'], list(result))

    self.WriteInput('1')
    result = self.Run('components repositories remove')
    self.assertEqual(['BAR'], list(result))
    self.CheckRepos(None)
    self.AssertErrContains('Removed repository: [BAR]')
    self.ClearErr()

    result = self.Run('components repositories list --format=disable')
    self.assertEqual([], list(result))

  def testAddDuplicate(self):
    self.Run('components repositories list')
    self.CheckRepos(None)
    self.AssertErrContains('You have no registered component repositories')
    self.ClearErr()

    result = self.Run('components repositories add FOO')
    self.assertEqual(['FOO'], result)
    self.CheckRepos(['FOO'])
    self.AssertErrContains(
        'Added repository: [FOO]\n')
    self.ClearErr()

    result = self.Run('components repositories add FOO BAR')
    self.assertEqual(['BAR'], result)
    self.CheckRepos(['FOO', 'BAR'])
    self.AssertErrContains(
        'Added repository: [BAR]\nRepository already added, skipping: [FOO]\n')
    self.ClearErr()

  def testAddRemoveMultiple(self):
    self.Run('components repositories list')
    self.CheckRepos(None)
    self.AssertErrContains('You have no registered component repositories')
    self.ClearErr()

    result = self.Run('components repositories add FOO BAR')
    self.assertEqual(['FOO', 'BAR'], result)
    self.CheckRepos(['FOO', 'BAR'])
    self.AssertErrContains(
        'Added repository: [FOO]\nAdded repository: [BAR]')
    self.ClearErr()

    result = self.Run('components repositories remove FOO BAR')
    self.assertEqual(['FOO', 'BAR'], result)
    self.CheckRepos([])
    self.AssertErrContains(
        'Removed repository: [FOO]\nRemoved repository: [BAR]')
    self.ClearErr()

  def testRemoveAll(self):
    self.Run('components repositories list')
    self.CheckRepos(None)
    self.Run('components repositories add FOO BAR')
    self.CheckRepos(['FOO', 'BAR'])

    self.ClearOutput()
    self.Run('components repositories list')
    self.AssertOutputContains("""\
REPOSITORY  LAST_UPDATE
FOO         Unknown
BAR         Unknown
""", normalize_space=True)
    self.ClearOutput()

    result = self.Run('components repositories remove --all')
    self.assertEqual(['FOO', 'BAR'], result)
    self.CheckRepos(None)

    result = self.Run('components repositories remove --all')
    self.assertEqual([], result)
    self.CheckRepos(None)

  def testAddRemoveErrors(self):
    with self.assertRaisesRegex(
        update_manager.NoRegisteredRepositoriesError,
        'You have no registered repositories.'):
      self.Run('components repositories remove')
    self.CheckRepos([])

    with self.assertRaisesRegex(
        update_manager.NoRegisteredRepositoriesError,
        'You have no registered repositories.'):
      self.Run('components repositories remove FOO')
    self.CheckRepos([])

    self.Run('components repositories add FOO')
    result = self.Run('components repositories remove')
    self.assertEqual([], result)
    self.CheckRepos(['FOO'])
    self.AssertErrContains('No repository was removed.')
    self.ClearErr()

    with self.AssertRaisesToolExceptionRegexp(
        'was not a known registered repository'):
      result = self.Run('components repositories remove ASDF')

    self.from_url_mock.side_effect = snapshots.URLFetchError()
    with self.AssertRaisesToolExceptionRegexp(
        r'The given repository \[FOO\] could not be fetched.'):
      self.Run('components repositories add FOO')

  def testRemoveCompletion(self):
    self.Run('components repositories add FOO')
    self.Run('components repositories add BAR')
    self.RunCompletion('components repositories remove ', ['FOO', 'BAR'])


if __name__ == '__main__':
  cli_test_base.main()
