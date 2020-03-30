# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for artifacts print-settings npm."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from tests.lib import test_case
from tests.lib.surface.artifacts import base


class NpmTests(base.ARTestBase):

  def testNpm(self):
    cmd = ' '.join([
        'beta', 'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=us'
    ])
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
Please insert following snippet into your .npmrc

======================================================
registry=https://us-npm.pkg.dev/fake-project/my-repo/
//us-npm.pkg.dev/fake-project/my-repo/:_password=""
//us-npm.pkg.dev/fake-project/my-repo/:username=oauth2accesstoken
//us-npm.pkg.dev/fake-project/my-repo/:email=not.valid@email.com
//us-npm.pkg.dev/fake-project/my-repo/:always-auth=true
======================================================

""",
        normalize_space=True)

  def testNpmWithScope(self):
    cmd = ' '.join([
        'beta', 'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--scope=@my-scope', '--location=asia'
    ])
    self.SetListLocationsExpect('asia')
    self.SetGetRepositoryExpect(
        'asia', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
Please insert following snippet into your .npmrc

======================================================
@my-scope:registry=https://asia-npm.pkg.dev/fake-project/my-repo/
//asia-npm.pkg.dev/fake-project/my-repo/:_password=""
//asia-npm.pkg.dev/fake-project/my-repo/:username=oauth2accesstoken
//asia-npm.pkg.dev/fake-project/my-repo/:email=not.valid@email.com
//asia-npm.pkg.dev/fake-project/my-repo/:always-auth=true
======================================================

""",
        normalize_space=True)

  def testMissingRepo(self):
    cmd = ' '.join(['beta', 'artifacts', 'print-settings', 'npm'])
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Failed to find attribute [repository]')

  def testInvalidLocation(self):
    cmd = ' '.join([
        'beta', 'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=invalid'
    ])
    self.SetListLocationsExpect('us')
    with self.assertRaises(ar_exceptions.UnsupportedLocationError):
      self.Run(cmd)
    self.AssertErrContains(
        'invalid is not a valid location. Valid locations are')

  def testInvalidRepoType(self):
    cmd = ' '.join([
        'beta', 'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=us'
    ])
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.DOCKER)
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Invalid repository type DOCKER. Valid type is NPM')


if __name__ == '__main__':
  test_case.main()
