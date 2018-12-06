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

"""Integration test for the 'debug source gen-repo-info-file' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import subprocess

from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.debug import base


FAKE_URL = 'https://github.com/NoSuchProject__/dummy.git'


# Do not inherit from any base class that provides auth - we want to verify
# that this command can run without auth.
class GenRepoInfoFileTest(base.DebugTest):

  def SetUp(self):
    # Identifier for this test, used for service names etc.
    self.test_dir = self.CreateTempDir()

  def testNoAuth(self):
    # Verifies that this test suite does not have auth. The testRepoInfo test
    # needs to run without auth in order to ensure that it works properly in
    # that case.
    with self.assertRaises(properties.RequiredPropertyError):
      self.RunDebug(['snapshots', 'create', 'foo.bar:123'])

  @sdk_test_base.Filters.RunOnlyIfExecutablePresent('git')
  def testRepoInfo(self):
    git_dir = os.path.join(self.test_dir, 'git_dir')

    try:
      subprocess.check_call(['git', 'init', git_dir])
      subprocess.check_call(['git', '-C', git_dir, 'config',
                             'user.email', 'nobody@google.com'])
      subprocess.check_call(['git', '-C', git_dir, 'config',
                             'user.name', 'Dummy Name'])
      subprocess.check_call(['git', '-C', git_dir, 'remote', 'add', 'origin',
                             FAKE_URL])
      with open(os.path.join(git_dir, 'dummy.txt'), 'w') as f:
        f.write('hello world')
      subprocess.check_call(['git', '-C', git_dir, 'add', '-A'])
      subprocess.check_call(['git', '-C', git_dir, 'commit',
                             '-m', 'Dummy commit'])
      self.RunDebug(
          ['source', 'gen-repo-info-file', '--source-directory', git_dir,
           '--output-directory', git_dir])
      with open(os.path.join(git_dir, 'source-context.json'), 'r') as f:
        context = json.load(f)
        self.assertEqual(context.get('git', {}).get('url'), FAKE_URL)
    finally:
      # Removal of the git in the TearDown method is flaky. Unclear
      # why. It seems to work consistently here though.
      if os.path.exists(git_dir):
        files.RmTree(git_dir)


if __name__ == '__main__':
  test_case.main()
