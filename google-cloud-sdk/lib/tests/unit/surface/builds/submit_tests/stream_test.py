# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests that exercise build creation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions as core_exceptions
from tests.lib import test_case
from tests.lib.surface.compute.builds import submit_test_base as test_base


class StreamTest(test_base.SubmitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateAndStream(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='my-project_cloudbuild'),
        response=self.storage_v1_messages.Bucket(id='my-project_cloudbuild'))
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix='my-project_cloudbuild',
        ),
        response=self.storage_v1_messages.Buckets(
            items=[self.storage_v1_messages.Bucket(
                id='my-project_cloudbuild')]))
    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project_cloudbuild',
            destinationObject=self.frozen_zip_filename,
            sourceBucket='bucket',
            sourceObject='object.zip',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project_cloudbuild',
                name=self.frozen_zip_filename,
                generation=123,
            ),
            done=True,
        ))

    def _MakeBuild(status):
      return self.cloudbuild_v1_messages.Build(
          createTime='2016-03-31T19:12:32.838111Z',
          id='123-456-789',
          images=[
              'gcr.io/my-project/image',
          ],
          projectId='my-project',
          status=status,
          logsBucket='gs://my-project_cloudbuild/logs',
          source=self.cloudbuild_v1_messages.Source(
              storageSource=self.cloudbuild_v1_messages.StorageSource(
                  bucket='my-project_cloudbuild',
                  object=self.frozen_zip_filename,
                  generation=123,
              )),
          steps=[
              self.cloudbuild_v1_messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=[
                      'build', '--no-cache', '-t', 'gcr.io/my-project/image',
                      '.'
                  ],
              ),
          ],
          timeout='600.000s')

    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=self.cloudbuild_v1_messages.Build(
                images=[
                    'gcr.io/my-project/image',
                ],
                source=self.cloudbuild_v1_messages.Source(
                    storageSource=self.cloudbuild_v1_messages.StorageSource(
                        bucket='my-project_cloudbuild',
                        object=self.frozen_zip_filename,
                        generation=123,
                    )),
                steps=test_base.DOCKER_BUILD_STEPS,
            ),
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.WORKING))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.SUCCESS))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image'
    ])

    self.AssertOutputContains(
        """\
Here is some streamed
data for you to print
Here the last line
""",
        normalize_space=True)

  def testCreateAndStreamButFAILURE(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='my-project_cloudbuild'),
        response=self.storage_v1_messages.Bucket(id='my-project_cloudbuild'))
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix='my-project_cloudbuild',
        ),
        response=self.storage_v1_messages.Buckets(
            items=[self.storage_v1_messages.Bucket(
                id='my-project_cloudbuild')]))
    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project_cloudbuild',
            destinationObject=self.frozen_zip_filename,
            sourceBucket='bucket',
            sourceObject='object.zip',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project_cloudbuild',
                name=self.frozen_zip_filename,
                generation=123,
            ),
            done=True,
        ))

    def _MakeBuild(status):
      return self.cloudbuild_v1_messages.Build(
          createTime='2016-03-31T19:12:32.838111Z',
          id='123-456-789',
          images=[
              'gcr.io/my-project/image',
          ],
          projectId='my-project',
          status=status,
          logsBucket='gs://my-project_cloudbuild/logs',
          source=self.cloudbuild_v1_messages.Source(
              storageSource=self.cloudbuild_v1_messages.StorageSource(
                  bucket='my-project_cloudbuild',
                  object=self.frozen_zip_filename,
                  generation=123,
              )),
          steps=[
              self.cloudbuild_v1_messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=[
                      'build', '--no-cache', '-t', 'gcr.io/my-project/image',
                      '.'
                  ],
              ),
          ],
          timeout='600.000s')

    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=self.cloudbuild_v1_messages.Build(
                images=[
                    'gcr.io/my-project/image',
                ],
                source=self.cloudbuild_v1_messages.Source(
                    storageSource=self.cloudbuild_v1_messages.StorageSource(
                        bucket='my-project_cloudbuild',
                        object=self.frozen_zip_filename,
                        generation=123,
                    )),
                steps=test_base.DOCKER_BUILD_STEPS,
            ),
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.QUEUED))

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.WORKING))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=0-'},
        status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='123-456-789',
            projectId='my-project',
        ),
        response=_MakeBuild(self._statuses.FAILURE))

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=44-'},
        status=200,
        body='Here the last line\n')

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-123-456-789.txt',
        request_headers={'Range': 'bytes=63-'},
        status=200,
        body='')
    with self.assertRaisesRegex(core_exceptions.Error, 'FAILURE'):
      self._Run([
          'builds', 'submit', 'gs://bucket/object.zip',
          '--tag=gcr.io/my-project/image'
      ])

    self.AssertOutputContains(
        """\
Here is some streamed
data for you to print
Here the last line
""",
        normalize_space=True)


class StreamTestBeta(StreamTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class StreamTestAlpha(StreamTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
