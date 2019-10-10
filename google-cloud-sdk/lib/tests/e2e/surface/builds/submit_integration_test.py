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

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.sdk_test_base import WithTempCWD

# LINT.IfChange
RESOURCE_PREFIX = 'cloud-sdk-integration-testing_cloudbuild'
# LINT.ThenChange(//depot/google3/cloud/sdk/component_build/scripts/resources.yaml)
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
    self.temp_bucket_name = self.CreateTempBucket()
    self.cloudbuild_yaml = self.Touch(
        self.root_path, 'cloudbuild.yaml', CLOUDBUILD_YAML)

  def TearDown(self):
    self.DeleteTempBucket(self.temp_bucket_name)

  def RunBuildsSubmit(self):
    self.Run(
        'builds submit --gcs-log-dir=gs://{0}/'
        '--gcs-source-staging-dir=gs://{0}/source/ --config={1} {2}'.format(
            self.temp_bucket_name, self.cloudbuild_yaml, self.root_path))

  def testSuccess(self):
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testRespectingGcloudIgnore(self):
    self.Touch(self.root_path, 'trash',
               'This file in a subdirectory should not be uploaded with'
               ' my build.')
    self.Touch(self.root_path, '.gcloudignore', 'trash')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testDeployRespectingGitIgnore(self):
    self.Touch(os.path.join(self.root_path, 'subdir'), 'trash',
               'This file should not be uploaded with my build.', makedirs=True)
    self.Touch(self.root_path, '.gcloudignore', 'subdir')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')

  def testDeployTopBotDirRespectingGitIgnore(self):
    """Catch os.walk() usage bug caused by keepdir/ignoredir in .gitignore."""
    self.Touch(os.path.join(self.root_path, 'topdir', 'botdir'), 'trash',
               'This file in a sub-sub-directory should not be uploaded with'
               ' my build.',
               makedirs=True)
    self.Touch(self.root_path, '.gcloudignore', 'topdir/botdir')
    self.RunBuildsSubmit()
    self.AssertOutputContains('SUCCESS')


if __name__ == '__main__':
  test_case.main()
