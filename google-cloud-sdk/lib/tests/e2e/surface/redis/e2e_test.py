# Copyright 2018 Google Inc. All Rights Reserved.
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

"""E2E test for `gcloud redis` surface."""

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib import test_case


TEST_REGION = 'us-central1'
# The default network in the cloud-sdk-integration-testing project is LEGACY
# and will not work with the Redis API.
TEST_NETWORK = 'do-not-delete-redis-test'


class E2eTest(e2e_base.WithServiceAuth, cli_test_base.CliTestBase,
              parameterized.TestCase):

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                             calliope_base.ReleaseTrack.BETA])
  def testInstanceCreate(self, track):
    self.track = track
    region_id = TEST_REGION
    instance_id = next(e2e_utils.GetResourceNameGenerator('redis-instance'))
    expected_instance_name = (
        'projects/{project}/locations/{regionId}/instances/{instanceId}'
        .format(project=self.Project(), regionId=region_id,
                instanceId=instance_id))

    with self.CreateInstance(instance_id, region_id) as actual_instance:
      self.assertEqual(actual_instance.name, expected_instance_name)

  @contextlib.contextmanager
  def CreateInstance(self, instance_id, region):
    try:
      yield self.Run(
          'redis instances create --region {region} {instance_id}'
          ' --network {network}'
          .format(region=region, instance_id=instance_id,
                  network=TEST_NETWORK))
    finally:
      self.Run('redis instances delete --region {region} {instance_id} --quiet'
               .format(region=region, instance_id=instance_id))


if __name__ == '__main__':
  test_case.main()
