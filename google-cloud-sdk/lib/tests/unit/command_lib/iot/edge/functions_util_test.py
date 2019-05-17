# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for tests.unit.command_lib.iot.edge.functions.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis

from googlecloudsdk.command_lib.iot.edge.functions import util

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.edge import base


_FUNCTION_BUILDER_NAME = 'gcr.io/cloud-iot-edge/function-builder'


class BuildTest(base.CloudIotEdgeBase, parameterized.TestCase):
  """Tests Edge function build with cloudbuild."""

  def testParseSourceUri(self):
    source = util._ParseSourceUri('gs://my-bucket/source/archive.tgz')
    self.assertEqual(source.storageSource.bucket, 'my-bucket')
    self.assertEqual(source.storageSource.object, 'source/archive.tgz')

  def testParseSourceUriFail(self):
    with self.assertRaisesRegex(util.FunctionBuilderError,
                                'not a valid GCS URI'):
      util._ParseSourceUri('gs://my-bucket')

  @parameterized.named_parameters(
      {
          'testcase_name': 'case 1',
          'arch': 'x86-64',
          'function_type': 'on-demand',
          'name': 'gcr.io/$PROJECT_ID/edge-functions/ondemand/my-function',
          'build_args': ['ondemand', 'x86_64']
      },
      {
          'testcase_name': 'case 2',
          'arch': 'aarch64',
          'function_type': 'stream-processing',
          'name': ('gcr.io/$PROJECT_ID/edge-functions/'
                   'streamprocessing/my-function'),
          'build_args': ['streamprocessing', 'aarch64']
      },
      {
          'testcase_name': 'case 3',
          'arch': 'armhf',
          'function_type': 'on-demand',
          'name': 'gcr.io/$PROJECT_ID/edge-functions/ondemand/my-function',
          'build_args': ['ondemand', 'armhf']
      },
  )
  def testEdgeFunctionMessage(self, arch, function_type, name, build_args):
    build_config = util._EdgeFunctionBuildMessage(
        'my-function', arch, function_type, 'gs://my-bucket/source/archive.tgz')
    self.assertEqual(len(build_config.steps), 1)
    self.assertEqual(build_config.steps[0].name, _FUNCTION_BUILDER_NAME)
    self.assertEqual(len(build_config.steps[0].args), 4)
    self.assertEqual(build_config.steps[0].args[0], name)
    self.assertEqual(build_config.steps[0].args[1:3], build_args)
    self.assertEqual(build_config.steps[0].args[3], util._EDGE_VERSION)
    self.assertEqual(len(build_config.images), 1)
    self.assertEqual(build_config.images[0], name)

  def testPrepareStagingObject(self):
    source_bucket_id = 'fake-project_edgefunction'
    self.storage_client.buckets.Get.Expect(
        self.storage_messages.StorageBucketsGetRequest(
            bucket=source_bucket_id),
        self.storage_messages.Bucket(id=source_bucket_id))
    staging_object = util._PrepareStagingObject()
    self.assertEqual(staging_object.bucket, source_bucket_id)
    self.assertRegex(staging_object.object, 'source/[0-9a-f]{32}.tgz')

  def SetUp(self):
    self.cloudbuild_client = mock.Client(
        client_class=apis.GetClientClass('cloudbuild', 'v1'))
    self.cloudbuild_messages = apis.GetMessagesModule('cloudbuild', 'v1')
    self.cloudbuild_client.Mock()
    self.addCleanup(self.cloudbuild_client.Unmock)

    self.storage_client = mock.Client(
        client_class=apis.GetClientClass('storage', 'v1'))
    self.storage_messages = apis.GetMessagesModule('storage', 'v1')
    self.storage_client.Mock()
    self.addCleanup(self.storage_client.Unmock)

if __name__ == '__main__':
  test_case.main()
