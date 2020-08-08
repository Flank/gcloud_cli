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

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute.builds import submit_test_base as test_base


class KanikoTest(test_base.SubmitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testSubmitUseKaniko(self):
    properties.VALUES.builds.use_kaniko.Set(True)

    b_in = self.cloudbuild_v1_messages.Build(
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '6h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        projectId='my-project',
        status=self._statuses.QUEUED,
        logsBucket='gs://my-project_cloudbuild/logs',
        logUrl='mockLogURL',
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '6h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
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

  def testSubmitUseKanikoCacheTTL(self):
    properties.VALUES.builds.use_kaniko.Set(True)
    properties.VALUES.builds.kaniko_cache_ttl.Set(1)

    b_in = self.cloudbuild_v1_messages.Build(
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '1h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        projectId='my-project',
        status=self._statuses.QUEUED,
        logsBucket='gs://my-project_cloudbuild/logs',
        logUrl='mockLogURL',
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '1h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
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

  def testSubmitUseKanikoOverrideImage(self):
    properties.VALUES.builds.use_kaniko.Set(True)
    properties.VALUES.builds.kaniko_image.Set('gcr.io/some-other/kaniko-image')

    b_in = self.cloudbuild_v1_messages.Build(
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/some-other/kaniko-image',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '6h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        projectId='my-project',
        status=self._statuses.QUEUED,
        logsBucket='gs://my-project_cloudbuild/logs',
        logUrl='mockLogURL',
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/some-other/kaniko-image',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '6h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
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

  def testSubmitNoCacheWithConfig(self):
    properties.VALUES.builds.use_kaniko.Set(True)
    config_path = self.Touch('.', 'config.yaml')
    with self.assertRaises(c_exceptions.ConflictingArgumentsException):
      self._Run([
          'builds', 'submit', 'gs://bucket/object.zip', '--config', config_path,
          '--no-cache'
      ])

  def testSubmitNoCacheWithoutKaniko(self):
    properties.VALUES.builds.use_kaniko.Set(False)
    with self.assertRaises(c_exceptions.InvalidArgumentException):
      self._Run([
          'builds', 'submit', 'gs://bucket/object.zip',
          '--tag=gcr.io/my-project/image', '--no-cache'
      ])

  def testSubmitNoCache(self):
    properties.VALUES.builds.use_kaniko.Set(True)

    b_in = self.cloudbuild_v1_messages.Build(
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '0h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
    b_out = self.cloudbuild_v1_messages.Build(
        createTime='2016-03-31T19:12:32.838111Z',
        id='123-456-789',
        projectId='my-project',
        status=self._statuses.QUEUED,
        logsBucket='gs://my-project_cloudbuild/logs',
        logUrl='mockLogURL',
        source=self.cloudbuild_v1_messages.Source(
            storageSource=self.cloudbuild_v1_messages.StorageSource(
                bucket='my-project_cloudbuild',
                object=self.frozen_zip_filename,
                generation=123,
            )),
        steps=[
            self.cloudbuild_v1_messages.BuildStep(
                name='gcr.io/kaniko-project/executor:latest',
                args=[
                    '--destination',
                    'gcr.io/my-project/image',
                    '--cache',
                    '--cache-ttl',
                    '0h',
                    '--cache-dir',
                    '',
                ],
            ),
        ])
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip', '--async',
        '--tag=gcr.io/my-project/image', '--no-cache'
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


class KanikoTestBeta(KanikoTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class KanikoTestAlpha(KanikoTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
