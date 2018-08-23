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
"""Test of the 'source clone' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import stat
import subprocess
import sys

import gcloud
from googlecloudsdk.api_lib.auth import service_account
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case

# Contents of ~/.gitconfig. Set credential helper to empty, this overrides
# any system installed credentials helpers as otherwise they are additive.
GIT_CONFIG = """\
[credential]
  helper =
"""


class CloneTest(cli_test_base.CliTestBase):

  def SetUp(self):
    git_path = files.FindExecutableOnPath('git')
    if not git_path:
      self.skipTest('Git is not available')

    # The system under which we are testing could have credential manager
    # installed at system or global level. It could interfere with gcloud
    # credential manager. Overriding global to be empty will override system and
    # global setting.
    home_dir = os.path.join(self.temp_path, 'home')
    self.prev_home_dir = os.environ.get('HOME')
    os.environ['HOME'] = home_dir
    self.Touch(home_dir, '.gitconfig', contents=GIT_CONFIG, makedirs=True)

    # Synthesize gcloud wrapper script and add it to the path so that git can
    # invoke it. This way we guarantee that gcloud under test will be invoked.
    if (platforms.OperatingSystem.Current() ==
        platforms.OperatingSystem.WINDOWS):
      gcloud_ext = '.cmd'
      script_template = """\
  @echo off
  "%COMSPEC%" /C "{} {} %*"

  "%COMSPEC%" /C exit %ERRORLEVEL%
  """
    else:
      gcloud_ext = ''
      script_template = """\
    #!/bin/bash

    {} {} $@
    """

    local_bin_dir = os.path.join(self.temp_path, 'bin')
    gcloud_script = self.Touch(
        local_bin_dir,
        'gcloud' + gcloud_ext,
        contents=script_template.format(sys.executable, gcloud.__file__),
        makedirs=True)
    st = os.stat(gcloud_script)
    os.chmod(gcloud_script, st.st_mode | stat.S_IEXEC)
    self.old_bin_path = os.environ['PATH']
    os.environ['PATH'] = os.pathsep.join([local_bin_dir, self.old_bin_path])

    # Make sure there is plenty of diagnosing data in case of test failure.
    os.environ['GIT_CURL_VERBOSE'] = '1'
    os.environ['GIT_TRACE'] = '1'
    properties.VALUES.core.print_unhandled_tracebacks.Set(True)
    properties.VALUES.core.print_handled_tracebacks.Set(True)

  def TearDown(self):
    if self.prev_home_dir is None:
      os.environ.pop('HOME', None)
    else:
      os.environ['HOME'] = self.prev_home_dir
    os.environ['PATH'] = self.old_bin_path
    os.environ.pop('GIT_CURL_VERBOSE', None)
    os.environ.pop('GIT_TRACE', None)

  def _RunCloneAndAssert(self, name, project):
    target_dir = os.path.join(self.temp_path, 'tmp-' + name)
    self.Run([
        'source', 'repos', 'clone', 'do-not-delete-gcloud-tests-repo',
        target_dir, '--project', project
    ])
    self.AssertOutputEquals('', normalize_space=True)

    with files.ChDir(target_dir):
      proc = subprocess.Popen(['git', 'status'])
      proc.communicate()
      self.assertEqual(0, proc.returncode)

      properties.VALUES.core.account.Set('some-other-nonexistant account')
      # Make sure git can now authenticate on its own.
      proc = subprocess.Popen(['git', 'pull'])
      proc.communicate()
      self.assertEqual(0, proc.returncode)

  def testClone_RefreshToken(self):
    with e2e_base.RefreshTokenAuth() as auth:
      self._RunCloneAndAssert(auth.__class__.__name__, auth.Project())

  def testClone_ServiceAccount(self):
    with e2e_base.ServiceAccountAuth() as auth:
      self._RunCloneAndAssert(auth.__class__.__name__, auth.Project())

  def testClone_P12ServiceAccountAuth(self):
    try:
      with e2e_base.P12ServiceAccountAuth() as auth:
        self._RunCloneAndAssert(auth.__class__.__name__, auth.Project())
    except service_account.UnsupportedCredentialsType:
      self.skipTest('P12 keys are not supported')

  def testClone_GceServiceAccount(self):
    try:
      with e2e_base.GceServiceAccount() as auth:
        self._RunCloneAndAssert(auth.__class__.__name__, auth.Project())
    except e2e_base.GceNotConnectedError:
      self.skipTest('Not on GCE')


if __name__ == '__main__':
  test_case.main()
