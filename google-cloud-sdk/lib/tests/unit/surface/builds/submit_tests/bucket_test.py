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
from googlecloudsdk.calliope import exceptions as c_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute.builds import submit_test_base as test_base


class BucketTest(test_base.SubmitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateExistingOwnedBucket(self):
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

    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            id='123-456-789',
            images=[
                'gcr.io/my-project/image',
            ],
            projectId='my-project',
            status=self._statuses.QUEUED,
            logsBucket='gs://my-project_cloudbuild/logs',
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='my-project_cloudbuild',
                    object=self.frozen_zip_filename,
                    generation=123,
                )),
            steps=test_base.DOCKER_BUILD_STEPS,
            timeout='600.000s'))

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

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image', '--async'
    ])
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789 2016-03-31T19:12:32+00:00 - gs://my-project_cloudbuild/{frozen_zip_filename} - QUEUED
""".format(frozen_zip_filename=self.frozen_zip_filename),
        normalize_space=True)

  def testGetExistingBucketNotOwned(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='my-project_cloudbuild'),
        response=self.storage_v1_messages.Bucket(id='my-project_cloudbuild'))
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_v1_messages.StorageBucketsListRequest(
            project='my-project',
            prefix='my-project_cloudbuild',
        ),
        response=self.storage_v1_messages.Buckets(items=[]))

    with self.assertRaisesRegex(
        c_exceptions.RequiredArgumentException,
        'Specify a bucket using --gcs-source-staging-dir'):
      self._Run([
          'builds', 'submit', 'gs://bucket/object.zip',
          '--tag=gcr.io/my-project/image', '--async'
      ])

  def testGetExistingBucketSpecifiedBucketAndLog(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='my-project_cloudbuild'),
        response=self.storage_v1_messages.Bucket(id='my-project_cloudbuild'))
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

    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=self.cloudbuild_v1_messages.Build(
            createTime='2016-03-31T19:12:32.838111Z',
            id='123-456-789',
            images=[
                'gcr.io/my-project/image',
            ],
            projectId='my-project',
            status=self._statuses.QUEUED,
            source=self.cloudbuild_v1_messages.Source(
                storageSource=self.cloudbuild_v1_messages.StorageSource(
                    bucket='my-project_cloudbuild',
                    object=self.frozen_zip_filename,
                    generation=123,
                )),
            steps=test_base.DOCKER_BUILD_STEPS,
            timeout='600.000s'))

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=self.cloudbuild_v1_messages.Build(
                images=[
                    'gcr.io/my-project/image',
                ],
                logsBucket='gs://my-project_cloudbuild/logs',
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

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--gcs-source-staging-dir=gs://my-project_cloudbuild/source',
        '--gcs-log-dir=gs://my-project_cloudbuild/logs',
        '--tag=gcr.io/my-project/image', '--async'
    ])
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789 2016-03-31T19:12:32+00:00 - gs://my-project_cloudbuild/{frozen_zip_filename} - QUEUED
""".format(frozen_zip_filename=self.frozen_zip_filename),
        normalize_space=True)

  def testCreateDeniedBucket(self):
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket='my-project_cloudbuild'),
        exception=http_error.MakeHttpError(
            409,
            url=('https://www.googleapis.com/storage/v1/buckets/'
                 'my-project_cloudbuild?alt=json')))

    with self.AssertRaisesHttpExceptionMatches(
        'Buckets instance [my-project_cloudbuild] is the subject of a conflict: '
        'Resource already exists.'):
      self._Run([
          'builds', 'submit', '/bucket/object.zip',
          '--tag=gcr.io/my-project/image', '--async'
      ])


class BucketTestBeta(BucketTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class BucketTestAlpha(BucketTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
