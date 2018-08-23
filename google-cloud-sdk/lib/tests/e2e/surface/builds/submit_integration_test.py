# -*- coding: utf-8 -*- #
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

"""Integration test for the 'functions deploy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.sdk_test_base import WithTempCWD

CLOUDBUILD_YAML = """
steps:
# For ease of debugging, log what files are present.
- name: 'ubuntu'
  args: ['/bin/ls', '-l']
# Files "trash" and "subdir/trash" should not be uploaded.
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ ! -f trash ]]']
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ ! -f subdir/trash ]]']
# File "topdir/botdir/trash" should not be uploaded.
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ ! -f topdir/botdir/trash ]]']
# File "cloudbuild.yaml" ought to have been uploaded.
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ -f cloudbuild.yaml ]]']
"""


class SubmitIntegrationTest(e2e_base.WithServiceAuth, WithTempCWD):

  def _PrepareBuildFiles(self):
    path = self.CreateTempDir()
    self.cloudbuild_yaml = os.path.join(path, 'cloudbuild.yaml')
    with open(self.cloudbuild_yaml, 'w') as f:
      f.write(CLOUDBUILD_YAML)
    return path

  def SetUp(self):
    self.source_path = self._PrepareBuildFiles()

  def testSuccess(self):
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.source_path))
    self.AssertOutputContains('SUCCESS')

  def testRespectingGcloudIgnore(self):
    trash = os.path.join(self.source_path, 'trash')
    with open(trash, 'w') as f:
      f.write('This file should not be uploaded with my build.')
    with open(os.path.join(self.source_path, '.gcloudignore'), 'w') as f:
      f.write('trash')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.source_path))
    self.AssertOutputContains('SUCCESS')
    os.remove(trash)

  def testDeployRespectingGitIgnore(self):
    subdir = os.path.join(self.source_path, 'subdir')
    trash = os.path.join(subdir, 'trash')
    os.mkdir(subdir)
    with open(trash, 'w') as f:
      f.write('This file in a subdirectory should not be uploaded with'
              ' my build.')
    with open(os.path.join(self.source_path, '.gitignore'), 'w') as f:
      f.write('subdir')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.source_path))
    self.AssertOutputContains('SUCCESS')
    os.remove(trash)
    os.rmdir(subdir)

  def testDeployTopBotDirRespectingGitIgnore(self):
    """Catch os.walk() usage bug caused by keepdir/ignoredir in .gitignore."""
    topdir = os.path.join(self.source_path, 'topdir')
    botdir = os.path.join(topdir, 'botdir')
    trash = os.path.join(botdir, 'trash')
    os.mkdir(topdir)
    os.mkdir(botdir)
    with open(trash, 'w') as f:
      f.write('This file in a sub-sub-directory should not be uploaded with'
              ' my build.')
    with open(os.path.join(self.source_path, '.gitignore'), 'w') as f:
      f.write('topdir/botdir')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.source_path))
    self.AssertOutputContains('SUCCESS')
    os.remove(trash)
    os.rmdir(botdir)
    os.rmdir(topdir)

  def TearDown(self):
    pass

if __name__ == '__main__':
  test_case.main()
