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


@test_case.Filters.SkipOnPy3('They are broken', 'b/114743556')
class SubmitIntegrationTest(e2e_base.WithServiceAuth, WithTempCWD):

  def SetUp(self):
    self.cloudbuild_yaml = self.Touch(
        self.root_path, 'cloudbuild.yaml', CLOUDBUILD_YAML)

  def testSuccess(self):
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.root_path))
    self.AssertOutputContains('SUCCESS')

  def testRespectingGcloudIgnore(self):
    self.Touch(self.root_path, 'trash',
               'This file in a subdirectory should not be uploaded with'
               ' my build.')
    self.Touch(self.root_path, '.gcloudignore', 'trash')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.root_path))
    self.AssertOutputContains('SUCCESS')

  def testDeployRespectingGitIgnore(self):
    self.Touch(os.path.join(self.root_path, 'subdir'), 'trash',
               'This file should not be uploaded with my build.', makedirs=True)
    self.Touch(self.root_path, '.gcloudignore', 'subdir')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.root_path))
    self.AssertOutputContains('SUCCESS')

  def testDeployTopBotDirRespectingGitIgnore(self):
    """Catch os.walk() usage bug caused by keepdir/ignoredir in .gitignore."""
    self.Touch(os.path.join(self.root_path, 'topdir', 'botdir'), 'trash',
               'This file in a sub-sub-directory should not be uploaded with'
               ' my build.',
               makedirs=True)
    self.Touch(self.root_path, '.gcloudignore', 'topdir/botdir')
    self.Run('builds submit --config={0} {1}'.format(
        self.cloudbuild_yaml, self.root_path))
    self.AssertOutputContains('SUCCESS')


if __name__ == '__main__':
  test_case.main()
