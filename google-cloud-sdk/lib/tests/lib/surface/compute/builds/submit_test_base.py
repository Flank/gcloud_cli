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

import os.path
import uuid

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from tests.lib import e2e_base
from tests.lib import sdk_test_base

_CONFIG_STEPS = """\
steps:
 - name: gcr.io/cloud-builders/docker
   args:
   - build
   - --network
   - cloudbuild
   - --no-cache
   - -t
   - gcr.io/my-project/image
   - .
"""

DOCKER_BUILD_STEPS = [
    core_apis.GetMessagesModule('cloudbuild', 'v1').BuildStep(
        name='gcr.io/cloud-builders/docker',
        args=[
            'build', '--network', 'cloudbuild', '--no-cache', '-t',
            'gcr.io/my-project/image', '.'
        ])
]

DEFAULT_BUILDPACK_BUILDER = 'gcr.io/buildpacks/builder'

DOCKER_BUILD_STEPS_WITH_AR = [
    core_apis.GetMessagesModule('cloudbuild', 'v1').BuildStep(
        name='gcr.io/cloud-builders/docker',
        args=[
            'build', '--network', 'cloudbuild', '--no-cache', '-t',
            'us-east1-docker.pkg.dev/my-project/image', '.'
        ])
]


def MakeConfig(images=None, timeout=None):
  config_contents = _CONFIG_STEPS
  if images:
    config_contents += 'images:\n{}\n'.format('\n'.join(
        ['- {}'.format(i) for i in images]))
  if timeout:
    config_contents += 'timeout: {}s\n'.format(timeout)
  return config_contents


class SubmitTestBase(e2e_base.WithMockHttp, sdk_test_base.WithFakeAuth,
                     sdk_test_base.WithTempCWD):
  """Base test class for the builds submit subcommand."""

  def SetUp(self):
    self.StartPatch('time.sleep')  # To speed up tests with polling

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
    self.storage_v1_messages = core_apis.GetMessagesModule('storage', 'v1')

    properties.VALUES.core.project.Set('my-project')

    messages = self.cloudbuild_v1_messages
    self._statuses = messages.Build.StatusValueValuesEnum
    self._vmtypes = messages.BuildOptions.MachineTypeValueValuesEnum

    frozen_time = times.ParseDateTime('2016-05-26T00:05:00.000000Z')
    frozen_uuid = uuid.uuid4()
    self.frozen_zip_filename = 'source/{frozen_time}-{frozen_uuid}.zip'.format(
        frozen_time=times.GetTimeStampFromDateTime(frozen_time),
        frozen_uuid=frozen_uuid.hex)
    self.frozen_tgz_filename = 'source/{frozen_time}-{frozen_uuid}.tgz'.format(
        frozen_time=times.GetTimeStampFromDateTime(frozen_time),
        frozen_uuid=frozen_uuid.hex)
    self.StartObjectPatch(times, 'Now', return_value=frozen_time)
    self.StartObjectPatch(uuid, 'uuid4', return_value=frozen_uuid)
    self.StartObjectPatch(os.path, 'getsize', return_value=100)

  def _Run(self, args):
    self.Run(args)

  def ExpectMessagesForSimpleBuild(self,
                                   b_in,
                                   b_out,
                                   build_project='my-project',
                                   gcs=True):
    storage_project = build_project.replace('google', 'elgoog')
    storage_project = storage_project.replace(':', '_')
    storage_project = storage_project.replace('.', '_')
    if gcs:
      b = self.storage_v1_messages.Bucket(id=storage_project + '_cloudbuild')
      self.mocked_storage_v1.buckets.Get.Expect(
          self.storage_v1_messages.StorageBucketsGetRequest(bucket=b.id),
          response=b)
      self.mocked_storage_v1.buckets.List.Expect(
          self.storage_v1_messages.StorageBucketsListRequest(
              project=build_project,
              prefix=b.id,
          ),
          response=self.storage_v1_messages.Buckets(items=[b]))
      self.mocked_storage_v1.objects.Rewrite.Expect(
          self.storage_v1_messages.StorageObjectsRewriteRequest(
              destinationBucket=storage_project + '_cloudbuild',
              destinationObject=self.frozen_zip_filename,
              sourceBucket='bucket',
              sourceObject='object.zip',
          ),
          response=self.storage_v1_messages.RewriteResponse(
              resource=self.storage_v1_messages.Object(
                  bucket=storage_project + '_cloudbuild',
                  name=self.frozen_zip_filename,
                  generation=123,
              ),
              done=True,
          ),
      )

    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=b_out)

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=b_in,
            projectId=build_project,
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata))))
