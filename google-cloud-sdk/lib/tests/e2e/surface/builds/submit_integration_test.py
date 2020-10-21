# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
import sys

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.sdk_test_base import WithTempCWD

# python-3.7.3-beta-2
PY_VERSION = 'python-{}.{}.{}-{}.{}'.format(sys.version_info.major,
                                            sys.version_info.minor,
                                            sys.version_info.micro,
                                            sys.version_info.releaselevel,
                                            sys.version_info.serial)
# Build tag identifiers:
# "[submit_integration_test.py, python-3.7.3-beta-2, darwin]"
TAGS = "['{}', '{}', '{}']".format(
    os.path.basename(__file__), PY_VERSION, sys.platform)
RESOURCE_PREFIX = 'cloud-sdk-integration-testing_cloudbuild'
CLOUDBUILD_YAML = """
tags: {}
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
""".format(TAGS)


class SubmitIntegrationTest(e2e_base.WithServiceAuth, WithTempCWD):

  def CreateTempBucket(self):
    name = next(e2e_utils.GetResourceNameGenerator(prefix=RESOURCE_PREFIX))
    storage_api.StorageClient().CreateBucketIfNotExists(name, self.Project())
    return name

  def DeleteTempBucket(self, bucket_name):
    bucket_ref = storage_util.BucketReference.FromArgument(
        bucket_name, require_prefix=False)
    for obj_message in storage_api.StorageClient().ListBucket(bucket_ref):
      obj_ref = storage_util.ObjectReference.FromMessage(obj_message)
      storage_api.StorageClient().DeleteObject(obj_ref)
    storage_api.StorageClient().DeleteBucket(bucket_ref)

  def SetUp(self):
    self.build_workspace = os.path.join(self.root_path, 'workspace')
    self.temp_bucket_name = self.CreateTempBucket()
    self.cloudbuild_yaml = self.Touch(self.build_workspace, 'cloudbuild.yaml',
                                      CLOUDBUILD_YAML)

  def TearDown(self):
    self.DeleteTempBucket(self.temp_bucket_name)

  def RunBuildsSubmit(self):
    self.Run(
        'builds submit --gcs-log-dir=gs://{0}/'
        '--gcs-source-staging-dir=gs://{0}/source/ --config={1} {2}'.format(
            self.temp_bucket_name, self.cloudbuild_yaml, self.build_workspace))

  def testSuccess(self):
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testRespectingGcloudIgnore(self):
    self.Touch(
        self.build_workspace, 'trash',
        'This file in a subdirectory should not be uploaded with'
        ' my build.')
    self.Touch(self.build_workspace, '.gcloudignore', 'trash')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testDeployRespectingGitIgnore(self):
    self.Touch(
        os.path.join(self.build_workspace, 'subdir'),
        'trash',
        'This file should not be uploaded with my build.',
        makedirs=True)
    self.Touch(self.build_workspace, '.gcloudignore', 'subdir')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testDeployTopBotDirRespectingGitIgnore(self):
    """Catch os.walk() usage bug caused by keepdir/ignoredir in .gitignore."""
    self.Touch(
        os.path.join(self.build_workspace, 'topdir', 'botdir'),
        'trash', 'This file in a sub-sub-directory should not be uploaded with'
        ' my build.',
        makedirs=True)
    self.Touch(self.build_workspace, '.gcloudignore', 'topdir/botdir')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  @test_case.Filters.DoNotRunIf(sys.version_info.major == 2 and os.name == 'nt',
                                'Py2 on Windows does not have os.symlink')
  def testSymlink(self):
    self.Touch(
        os.path.join(self.build_workspace, 'real'),
        'foo',
        'This is a real file.',
        makedirs=True)
    os.symlink('real', os.path.join(self.build_workspace, 'link'))
    # Replace the default cloudbuild.yaml with our symlink test.
    self.cloudbuild_yaml = self.Touch(
        self.build_workspace, 'cloudbuild.yaml', """
tags: {}
steps:
# For ease of debugging, log what files are present.
- name: 'ubuntu'
  args: ['find', '.', '-print']
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ -L link ]]']
# If we handled the symlink directory, the foo file appears in it.
- name: 'ubuntu'
  args: ['/bin/bash', '-c', '[[ -f link/foo ]]']
""".format(TAGS))
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')


if __name__ == '__main__':
  test_case.main()
