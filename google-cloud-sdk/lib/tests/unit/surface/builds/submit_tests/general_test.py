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
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute.builds import submit_test_base as test_base
from six.moves import range  # pylint: disable=redefined-builtin


class GeneralSubmitTest(test_base.SubmitTestBase):

  def testManyImages(self):
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
            steps=[
                self.cloudbuild_v1_messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', 'gcr.io/my-project/image', '.'],
                ),
            ],
            timeout='200.000s'))

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=self.cloudbuild_v1_messages.Build(
                images=[
                    'gcr.io/my-project/image1',
                    'gcr.io/my-project/image2',
                    'gcr.io/my-project/image3',
                    'gcr.io/my-project/image4',
                    'gcr.io/my-project/image5',
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

    config_path = self.Touch(
        '.',
        'config.yaml',
        contents=test_base.MakeConfig(
            images=['gcr.io/my-project/image{}'.format(i) for i in range(1, 6)],
            timeout=200))
    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip', '--config', config_path,
        '--async'
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

  def testBadLocalFile(self):
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

    bad_tarball_path = self.Touch(
        '.', 'source.badfile', contents='pretend this is a valid tarball')
    with self.assertRaisesRegex(c_exceptions.BadFileException, 'Local file'):
      self._Run([
          'builds', 'submit', bad_tarball_path, '--tag=gcr.io/my-project/image',
          '--async'
      ])

  def testNotGCRTag(self):
    img = 'gcr-staging.sandbox.googleapis.com/my-registry/my-image'
    with self.assertRaisesRegex(c_exceptions.InvalidArgumentException,
                                'Tag value must be in the gcr.io'):
      self._Run(['builds', 'submit', '.', '--tag=' + img])

    # Confirm that hidden property disables Exception for non-gcr.io registry
    properties.VALUES.builds.check_tag.Set(False)
    b_in = self.cloudbuild_v1_messages.Build(
        images=[img],
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                args=[
                    'build', '--network', 'cloudbuild', '--no-cache', '-t', img,
                    '.'
                ],
                name='gcr.io/cloud-builders/docker',
            ),
        ],
    )
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        images=[img],
        projectId='my-project',
        status=self._statuses.QUEUED,
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
                    'build', '--network', 'cloudbuild', '--no-cache', '-t', img,
                    '.'
                ],
            ),
        ],
        timeout='600.000s')
    self.ExpectMessagesForSimpleBuild(b_in, b_out)
    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip', '--tag=' + img, '--async'
    ])

  def testNoImage(self):
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
            images=[],
            projectId='my-project',
            status=self._statuses.QUEUED,
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
                    args=['build', '-t', 'gcr.io/my-project/image', '.'],
                ),
            ],
            timeout='200.000s'))

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=self.cloudbuild_v1_messages.Build(
                images=[],
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

    config_path = self.Touch(
        '.', 'config.yaml', contents=test_base.MakeConfig(timeout=200))
    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip', '--config', config_path,
        '--async'
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

  def testTimeout(self):
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
        timeout='62.000s',
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
        timeout='62s',
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image', '--async', '--timeout=1m2s'
    ])

  def testTimeoutBareSeconds(self):
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
        timeout='62.000s',
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
        timeout='62s',
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image', '--async', '--timeout=62'
    ])

  def testDomainScopedProject(self):
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        images=[
            'gcr.io/google.com/foobar/image',
        ],
        projectId='google.com:foobar',
        status=self._statuses.QUEUED,
        logsBucket='gs://elgoog_com_foobar_cloudbuild/logs',
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='elgoog_com_foobar_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/cloud-builders/docker',
                args=[
                    'build', '--network', 'cloudbuild', '--no-cache', '-t',
                    'gcr.io/google.com/foobar/image', '.'
                ],
            ),
        ],
        logUrl='mockLogURL',
        timeout='600.000s',
    )
    b_in = self.cloudbuild_v1_messages.Build(
        images=[
            'gcr.io/google.com/foobar/image',
        ],
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='elgoog_com_foobar_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                args=[
                    'build', '--network', 'cloudbuild', '--no-cache', '-t',
                    'gcr.io/google.com/foobar/image', '.'
                ],
                name='gcr.io/cloud-builders/docker',
            ),
        ],
    )
    self.ExpectMessagesForSimpleBuild(
        b_in, b_out, build_project='google.com:foobar')

    self._Run([
        'builds', 'submit', '--project=google.com:foobar',
        'gs://bucket/object.zip', '--tag=gcr.io/google.com/foobar/image',
        '--async'
    ])
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/google.com%3Afoobar/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789 2016-03-31T19:12:32+00:00 - gs://elgoog_com_foobar_cloudbuild/{frozen_zip_filename} - QUEUED
""".format(frozen_zip_filename=self.frozen_zip_filename),
        normalize_space=True)
    self.AssertErrContains('Logs are available at')
    self.AssertErrContains('mockLogURL')
    self.AssertErrNotContains('Logs can be found in the Cloud Console')

  def testDefaultSourceSuccess(self):
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
    self.mocked_storage_v1.objects.Insert.Expect(
        self.storage_v1_messages.StorageObjectsInsertRequest(
            bucket='my-project_cloudbuild',
            name=self.frozen_tgz_filename,
            object=self.storage_v1_messages.Object(size=100),
        ),
        response=self.storage_v1_messages.Object(
            bucket='my-project_cloudbuild',
            name=self.frozen_tgz_filename,
            generation=123,
            size=100,
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
                    object=self.frozen_tgz_filename,
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
                        object=self.frozen_tgz_filename,
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

    self.Touch('.', 'Dockerfile', contents='FROM busybox\n')
    self._Run(['builds', 'submit', '--tag=gcr.io/my-project/image', '--async'])
    self.AssertErrContains('Uploading tarball of ')
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789 2016-03-31T19:12:32+00:00 - gs://my-project_cloudbuild/{frozen_tgz_filename} - QUEUED
""".format(frozen_tgz_filename=self.frozen_tgz_filename),
        normalize_space=True)

  def testNoSourceSuccess(self):
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        images=[
            'gcr.io/my-project/image',
        ],
        projectId='my-project',
        status=self._statuses.QUEUED,
        logsBucket='gs://my-project_cloudbuild/logs',
        source=None,
        steps=test_base.DOCKER_BUILD_STEPS,
        logUrl='mockLogURL',
        timeout='600.000s',
    )
    b_in = self.cloudbuild_v1_messages.Build(
        images=[
            'gcr.io/my-project/image',
        ],
        source=None,
        steps=test_base.DOCKER_BUILD_STEPS,
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out, gcs=False)

    self._Run([
        'builds', 'submit', '--no-source', '--tag=gcr.io/my-project/image',
        '--async'
    ])
    self.AssertErrContains(
        """\
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/builds/123-456-789].
""",
        normalize_space=True)
    self.AssertOutputContains(
        """\
ID CREATE_TIME DURATION SOURCE IMAGES STATUS
123-456-789 2016-03-31T19:12:32+00:00 - - - QUEUED
""",
        normalize_space=True)
    self.AssertErrContains('Logs are available at')
    self.AssertErrContains('mockLogURL')
    self.AssertErrNotContains('Logs can be found in the Cloud Console')

  def testNoEmptyTag(self):
    with self.assertRaises(c_exceptions.InvalidArgumentException):
      self._Run(['builds', 'submit', 'gs://bucket/object.zip', '--tag='])


class GeneralSubmitTestBeta(GeneralSubmitTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class GeneralSubmitTestAlpha(GeneralSubmitTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
