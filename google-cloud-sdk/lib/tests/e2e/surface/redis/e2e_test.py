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

from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface import redis_test_base


class E2eTest(redis_test_base.E2eTestBase):

  def testInstanceCreate(self):
    region_id = redis_test_base.TEST_REGION
    instance_id = next(e2e_utils.GetResourceNameGenerator('redis-instance'))
    expected_instance_name = (
        'projects/{project}/locations/{regionId}/instances/{instanceId}'
        .format(project=self.Project(), regionId=region_id,
                instanceId=instance_id))

    with self.CreateInstance(instance_id, region_id) as actual_instance:
      self.assertEqual(actual_instance.name, expected_instance_name)


if __name__ == '__main__':
  test_case.main()
