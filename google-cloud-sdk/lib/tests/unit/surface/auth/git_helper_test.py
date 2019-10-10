# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

import subprocess

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GitHelperTest(sdk_test_base.WithFakeAuth,
                    cli_test_base.CliTestBase):

  def SetUp(self):
    def FakeRefresh(cred, http=None):
      del http
      if cred:
        cred.access_token = self.FakeAuthAccessToken()
    self.StartObjectPatch(c_store, 'Refresh', side_effect=FakeRefresh)

  def testGitCredHelper(self):
    self.WriteInput('protocol=https\nhost=source.developers.google.com\n')
    self.Run('auth git-helper get')
    self.AssertOutputContains('username={username}\npassword={pwd}'.format(
        username=self.FakeAuthAccount(), pwd=self.FakeAuthAccessToken()))

  def testGitCredHelperGoogleSource(self):
    self.WriteInput('protocol=https\nhost=googlesource.com\n')
    self.Run('auth git-helper get')
    self.AssertOutputEquals('username={username}\npassword={pwd}\n'.format(
        username='git-account', pwd=self.FakeAuthAccessToken()))

  def testGitCredHelperGoogleSourceSubdomain(self):
    self.WriteInput('protocol=https\nhost=foo.googlesource.com\n')
    self.Run('auth git-helper get')
    self.AssertOutputEquals('username={username}\npassword={pwd}\n'.format(
        username='git-account', pwd=self.FakeAuthAccessToken()))

  def testGitCredHelperEmptyPath(self):
    self.WriteInput(
        'protocol=https\nhost=source.developers.google.com\npath=\n')
    self.Run('auth git-helper get')
    self.AssertOutputContains('username={username}\npassword={pwd}'.format(
        username=self.FakeAuthAccount(), pwd=self.FakeAuthAccessToken()))

  def testGitCredHelperBadProtocol(self):
    self.WriteInput('protocol=junk\nhost=source.developers.google.com\n')
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        r'Invalid protocol \[junk\].  "https" expected.'):
      self.Run('auth git-helper get')
    self.AssertOutputEquals('')

  def testGitCredHelperExtraSpaces(self):
    self.WriteInput(' protocol=https\nhost=source.developers.google.com\n')
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        'Required key "protocol" missing.'):
      self.Run('auth git-helper get')
    self.AssertOutputEquals('')

  def testGitCredHelperBadDomain(self):
    self.WriteInput('protocol=https\nhost=junk.com\n')
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        r'Unknown host \[junk.com\].'):
      self.Run('auth git-helper get')
    self.AssertOutputEquals('')

  def testGitCredHelperBadMethod(self):
    self.FakeAuthSetCredentialsPresent(False)
    self.WriteInput('protocol=https\nhost=source.developers.google.com\n')
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        r'Unexpected method \[junk\]. One of \[get, store\] expected.'):
      self.Run('auth git-helper junk')
    self.AssertOutputEquals('')

  def testIgnoreUnknownMethod(self):
    self.Run('auth git-helper junk --ignore-unknown')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testIgnoreUnknownHost(self):
    self.WriteInput('protocol=https\nhost=slashdot.org\n')
    self.Run('auth git-helper get --ignore-unknown')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testNoIgnoreUnknownMethod(self):
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        r'Unexpected method \[junk]\. One of \[get, store] expected\.'):
      self.Run('auth git-helper junk')
    self.AssertOutputEquals('')
    self.AssertErrContains('ERROR')

  def testNoIgnoreUnknownHost(self):
    self.WriteInput('protocol=https\nhost=slashdot.org\n')
    with self.assertRaisesRegex(
        auth_exceptions.GitCredentialHelperError,
        r'Unknown host \[slashdot.org]\.'):
      self.Run('auth git-helper get')
    self.AssertOutputEquals('')
    self.AssertErrContains('ERROR')

  def testGitCredHelperNoCreds(self):
    self.FakeAuthSetCredentialsPresent(False)
    self.WriteInput('protocol=https\nhost=source.developers.google.com\n')
    self.Run('auth git-helper get')
    self.AssertErrContains('ERROR: ')

  def testGitCredHelperExtraDomains(self):
    properties.VALUES.core.credentialed_hosted_repo_domains.Set(
        'foo.com,junk.com')
    self.WriteInput('protocol=https\nhost=junk.com\n')
    self.Run('auth git-helper get')
    self.AssertOutputContains('username={username}\npassword={pwd}'.format(
        username=self.FakeAuthAccount(), pwd=self.FakeAuthAccessToken()))

    self.WriteInput('protocol=https\nhost=foo.com\n')
    self.Run('auth git-helper get')
    self.AssertOutputContains('username={username}\npassword={pwd}'.format(
        username=self.FakeAuthAccount(), pwd=self.FakeAuthAccessToken()))

  def testStore(self):
    self.WriteInput('protocol=https\nhost=source.developers.google.com\n')
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.return_value.communicate.return_value = ('', '')
    popen_mock.return_value.returncode = 0

    self.Run('auth git-helper store --verbosity=debug')
    self.assertFalse(popen_mock.called)

    self.WriteInput('protocol=https\nhost=source.developers.google.com\n')
    os_mock.return_value = platforms.OperatingSystem.MACOSX
    self.Run('auth git-helper store --verbosity=debug')
    popen_mock.assert_called_once_with(
        ['git-credential-osxkeychain', 'erase'], stdout=subprocess.PIPE,
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    popen_mock.return_value.communicate.assert_called_once_with(
        'protocol=https\nhost=source.developers.google.com\n\n')
    self.AssertErrNotContains('Failed to clear OSX')


if __name__ == '__main__':
  test_case.main()
