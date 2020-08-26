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

import os

from googlecloudsdk.api_lib.artifacts import exceptions as ar_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.artifacts import base


class NpmTestsBeta(base.ARTestBase):

  def PreSetUp(self):
    super(NpmTestsBeta, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.BETA

  def testNpm(self):
    cmd = [
        'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=us'
    ]
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
# Insert following snippet into your .npmrc

registry=https://us-npm.pkg.dev/fake-project/my-repo/
//us-npm.pkg.dev/fake-project/my-repo/:_authToken=""
//us-npm.pkg.dev/fake-project/my-repo/:always-auth=true

""",
        normalize_space=True)

  def testNpmWithScope(self):
    cmd = [
        'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--scope=@my-scope', '--location=asia'
    ]
    self.SetListLocationsExpect('asia')
    self.SetGetRepositoryExpect(
        'asia', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)
    self.Run(cmd)
    self.AssertOutputEquals(
        """\
# Insert following snippet into your .npmrc

@my-scope:registry=https://asia-npm.pkg.dev/fake-project/my-repo/
//asia-npm.pkg.dev/fake-project/my-repo/:_authToken=""
//asia-npm.pkg.dev/fake-project/my-repo/:always-auth=true

""",
        normalize_space=True)

  def testNpmJsonKeyConfig(self):
    cmd = [
        'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=us'
    ]
    self.SetUpCreds()
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)

    self.Run(cmd)
    self.AssertOutputEquals(
        """\
# Insert following snippet into your .npmrc

registry=https://us-npm.pkg.dev/fake-project/my-repo/
//us-npm.pkg.dev/fake-project/my-repo/:_password="ZXdvZ0lDSmpiR2xsYm5SZlpXMWhhV3dpT2lBaVltRnlRR1JsZG1Wc2IzQmxjaTVuYzJWeWRtbGpaV0ZqWTI5MWJuUXVZMjl0SWl3S0lDQWlZMnhwWlc1MFgybGtJam9nSW1KaGNpNWhjSEJ6TG1kdmIyZHNaWFZ6WlhKamIyNTBaVzUwTG1OdmJTSXNDaUFnSW5CeWFYWmhkR1ZmYTJWNUlqb2dJaTB0TFMwdFFrVkhTVTRnVUZKSlZrRlVSU0JMUlZrdExTMHRMVnh1WVhOa1pseHVMUzB0TFMxRlRrUWdVRkpKVmtGVVJTQkxSVmt0TFMwdExWeHVJaXdLSUNBaWNISnBkbUYwWlY5clpYbGZhV1FpT2lBaWEyVjVMV2xrSWl3S0lDQWlkSGx3WlNJNklDSnpaWEoyYVdObFgyRmpZMjkxYm5RaUNuMD0="
//us-npm.pkg.dev/fake-project/my-repo/:username=_json_key_base64
//us-npm.pkg.dev/fake-project/my-repo/:email=not.valid@email.com
//us-npm.pkg.dev/fake-project/my-repo/:always-auth=true

""",
        normalize_space=True)

  def testNpmJsonKeyInput(self):
    with files.TemporaryDirectory() as tmp_dir:
      key_file = os.path.join(tmp_dir, 'path/to/key.json')
      self.WriteKeyFile(key_file)
      cmd = [
          'artifacts', 'print-settings', 'npm', '--repository=my-repo',
          '--location=us',
          '--json-key=%s' % key_file
      ]
      self.SetListLocationsExpect('us')
      self.SetGetRepositoryExpect(
          'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)

      self.Run(cmd)
      self.AssertOutputEquals(
          """\
# Insert following snippet into your .npmrc

registry=https://us-npm.pkg.dev/fake-project/my-repo/
//us-npm.pkg.dev/fake-project/my-repo/:_password="ZXlKaElqb2lZaUo5"
//us-npm.pkg.dev/fake-project/my-repo/:username=_json_key_base64
//us-npm.pkg.dev/fake-project/my-repo/:email=not.valid@email.com
//us-npm.pkg.dev/fake-project/my-repo/:always-auth=true

""",
          normalize_space=True)

  def testNpmJsonKeyWithScope(self):
    with files.TemporaryDirectory() as tmp_dir:
      key_file = os.path.join(tmp_dir, 'path/to/key.json')
      cmd = [
          'artifacts', 'print-settings', 'npm', '--repository=my-repo',
          '--scope=@my-scope', '--location=asia',
          '--json-key=%s' % key_file
      ]
      self.WriteKeyFile(key_file)
      self.SetListLocationsExpect('asia')
      self.SetGetRepositoryExpect(
          'asia', 'my-repo', self.messages.Repository.FormatValueValuesEnum.NPM)

      self.Run(cmd)
      self.AssertOutputEquals(
          """\
# Insert following snippet into your .npmrc

@my-scope:registry=https://asia-npm.pkg.dev/fake-project/my-repo/
//asia-npm.pkg.dev/fake-project/my-repo/:_password="ZXlKaElqb2lZaUo5"
//asia-npm.pkg.dev/fake-project/my-repo/:username=_json_key_base64
//asia-npm.pkg.dev/fake-project/my-repo/:email=not.valid@email.com
//asia-npm.pkg.dev/fake-project/my-repo/:always-auth=true

""",
          normalize_space=True)

  def testMissingRepo(self):
    cmd = ['artifacts', 'print-settings', 'npm']
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Failed to find attribute [repository]')

  def testInvalidLocation(self):
    cmd = [
        'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=invalid'
    ]
    self.SetListLocationsExpect('us')
    with self.assertRaises(ar_exceptions.UnsupportedLocationError):
      self.Run(cmd)
    self.AssertErrContains(
        'invalid is not a valid location. Valid locations are')

  def testInvalidRepoType(self):
    cmd = [
        'artifacts', 'print-settings', 'npm', '--repository=my-repo',
        '--location=us'
    ]
    self.SetListLocationsExpect('us')
    self.SetGetRepositoryExpect(
        'us', 'my-repo', self.messages.Repository.FormatValueValuesEnum.DOCKER)
    with self.assertRaises(ar_exceptions.InvalidInputValueError):
      self.Run(cmd)
    self.AssertErrContains('Invalid repository type DOCKER. Valid type is NPM')


class NpmTestsAlpha(NpmTestsBeta):

  def PreSetUp(self):
    super(NpmTestsAlpha, self).PreSetUp()
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
