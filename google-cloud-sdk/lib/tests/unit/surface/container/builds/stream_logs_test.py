# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Streaming logs tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class StreamLogsTest(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

    self.mocked_storage_v1 = mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

    properties.VALUES.core.project.Set('my-project')

    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

  def _Run(self, args):
    self.Run(['alpha']+args)

  def testInProgress(self):
    def mk_build(status):
      return self.cloudbuild_v1_messages.Build(
          createTime='2016-03-31T19:12:32.838111Z',
          id='123-456-789',
          images=[
              'gcr.io/project/image',
          ],
          projectId='my-project',
          status=status,
          logsBucket='gs://my-project_cloudbuild/logs',
          source=self.cloudbuild_v1_messages.Source(
              storageSource=self.cloudbuild_v1_messages.StorageSource(
                  bucket='my-project_cloudbuild',
                  object='source/1464221100.0_gcr.io_project_image.tgz',
                  generation=123,
              ),
          ),
          steps=[
              self.cloudbuild_v1_messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=['build', '-t', 'gcr.io/project/image'],
              ),
          ],
          timeout='600.000s')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=mk_build(self._statuses.WORKING))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=mk_build(self._statuses.SUCCESS))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'}, status=200,
        body='Here the last line\n')

    self._Run(['container', 'builds', 'stream-logs', '123-456-789'])

    self.AssertOutputContains("""\
Here is some streamed
data for you to print
Here the last line
""", normalize_space=True)

  def testAlreadyFinished(self):
    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            id='123-456-789',
            images=[
                'gcr.io/project/image',
            ],
            projectId='my-project',
            status=self._statuses.SUCCESS,
            logsBucket='gs://my-project_cloudbuild/logs',
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='my-project_cloudbuild',
                    object='source/1464221100.0_gcr.io_project_image.tgz',
                    generation=123,
                ),
            ),
            steps=[
                self.cloudbuild_v1_messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', 'gcr.io/project/image'],
                ),
            ],
            timeout='600.000s'))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self._Run(['container', 'builds', 'stream-logs', '123-456-789'])

    self.AssertOutputContains("""\
Here is some streamed
data for you to print
""", normalize_space=True)

  def testNoLogsBucket(self):
    build = self.cloudbuild_v1_messages.Build(
        id='123-456-789',
        logsBucket=None)  # No logsBucket specified
    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=build)
    with self.assertRaises(cb_logs.NoLogsBucketException):
      self._Run(['container', 'builds', 'stream-logs', '123-456-789'])


if __name__ == '__main__':
  test_case.main()
