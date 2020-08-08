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
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute.builds import submit_test_base as test_base


class CreateTest(test_base.SubmitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateSuccess(self):
    b_out = self.cloudbuild_v1_messages.Build(
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
        logUrl='mockLogURL',
        timeout='600.000s',
    )
    b_in = self.cloudbuild_v1_messages.Build(
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
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

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
    self.AssertErrContains('Logs are available at')
    self.AssertErrContains('mockLogURL')
    self.AssertErrNotContains('Logs can be found in the Cloud Console')

  def testCreateSuccessWithArtifactRegistry(self):
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        images=[
            'us-east1-docker.pkg.dev/my-project/image',
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
        steps=test_base.DOCKER_BUILD_STEPS_WITH_AR,
        logUrl='mockLogURL',
        timeout='600.000s',
    )
    b_in = self.cloudbuild_v1_messages.Build(
        images=[
            'us-east1-docker.pkg.dev/my-project/image',
        ],
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=test_base.DOCKER_BUILD_STEPS_WITH_AR,
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=us-east1-docker.pkg.dev/my-project/image', '--async'
    ])
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
123-456-789 2016-03-31T19:12:32+00:00 - gs://my-project_cloudbuild/{frozen_zip_filename} - QUEUED
""".format(frozen_zip_filename=self.frozen_zip_filename),
        normalize_space=True)
    self.AssertErrContains('Logs are available at')
    self.AssertErrContains('mockLogURL')
    self.AssertErrNotContains('Logs can be found in the Cloud Console')

  def testCreateSuccessSubstitutions(self):
    substitutions_type = self.cloudbuild_v1_messages.Build.SubstitutionsValue
    substitutions = self.cloudbuild_v1_messages.Build.SubstitutionsValue(
        additionalProperties=[
            substitutions_type.AdditionalProperty(
                key='_DAY_OF_WEEK', value='tuesday'),
            substitutions_type.AdditionalProperty(
                key='_FAVORITE_COLOR', value='blue')
        ])
    b_out = self.cloudbuild_v1_messages.Build(
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
        substitutions=substitutions,
        logUrl='mockLogURL',
        timeout='600.000s',
    )
    b_in = self.cloudbuild_v1_messages.Build(
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
        substitutions=substitutions)
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image', '--async', '--substitutions',
        '_DAY_OF_WEEK=tuesday,_FAVORITE_COLOR=blue'
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
    self.AssertErrContains('Logs are available at')
    self.AssertErrContains('mockLogURL')
    self.AssertErrNotContains('Logs can be found in the Cloud Console')

  def testCreateSuccessNoLogUrl(self):
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
        ),
    )

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

    self.AssertErrNotContains('To see logs in the Cloud Console')
    self.AssertErrContains('Logs are available in the Cloud Console')

  def testCreateWithTimeout(self):
    properties.VALUES.builds.timeout.Set('200')

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
            done=True))

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
            timeout='200s'))

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
                timeout='200s',
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


class CreateTestBeta(CreateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateTestAlpha(CreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
