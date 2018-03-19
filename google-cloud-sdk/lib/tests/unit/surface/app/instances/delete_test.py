# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests for gcloud app instances delete."""

from tests.lib.surface.app import instances_base


class InstancesDeleteTest(instances_base.InstancesTestBase):

  def testDelete(self):
    self._ExpectDeleteInstanceCall('default', 'v1', 'i2')
    self.Run('app instances delete -s default -v v1 i2')
    self.AssertErrContains('Deleted [https://appengine.googleapis.com/v1/apps/'
                           'fakeproject/services/default/versions/v1/'
                           'instances/i2].')
