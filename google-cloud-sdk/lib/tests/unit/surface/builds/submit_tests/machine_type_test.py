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
from tests.lib import test_case
from tests.lib.surface.compute.builds import submit_test_base as test_base


class MachineTypeTest(test_base.SubmitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testCreateMachineTypeSuccess(self):
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
        options=self.cloudbuild_v1_messages.BuildOptions(
            machineType=self._vmtypes.N1_HIGHCPU_8),
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
        options=self.cloudbuild_v1_messages.BuildOptions(
            machineType=self._vmtypes.N1_HIGHCPU_8),
    )
    self.ExpectMessagesForSimpleBuild(b_in, b_out)

    self._Run([
        'builds', 'submit', 'gs://bucket/object.zip',
        '--tag=gcr.io/my-project/image', '--machine-type=n1-highcpu-8',
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

  def testCreateWrongMachineType(self):
    with self.assertRaises(Exception):
      self._Run([
          'builds', 'submit', '--tag=gcr.io/my-project/image',
          '--machine-type=n1-wrong-1', '--no-source'
      ])

  def testCreateUnspecifiedMachineType(self):
    with self.assertRaises(Exception):
      self._Run([
          'builds', 'submit', '--tag=gcr.io/my-project/image',
          '--machine-type=unspecified', '--no-source'
      ])


class MachineTypeTestBeta(MachineTypeTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class MachineTypeTestAlpha(MachineTypeTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
