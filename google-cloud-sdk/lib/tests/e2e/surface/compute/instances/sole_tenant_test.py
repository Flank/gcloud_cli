# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/using/deleting instances."""

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class SoleTenantTest(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.compute_uri = ('https://www.googleapis.com/compute/{0}'
                        .format(self.track.prefix or 'v1'))
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='sole-tenant-instance', sequence_start=1)
    self.zone = 'us-central1-b'
    self.scope_flag[e2e_test_base.ZONAL] = '--zone ' + self.zone
    self.host_type = 'n1-host-64-416'
    self._created_resources = []

  def _CreateResourceScheduleCleanUp(
      self, name, res_type, scope, creation_args):
    self._created_resources.append((name, res_type, scope,))
    return self.Run('compute {0} create {1} {2}'.format(res_type, name,
                                                        creation_args))

  def _CreateHost(self):
    name = self._name_generator.next()
    self._CreateResourceScheduleCleanUp(
        name, 'sole-tenancy hosts', e2e_test_base.ZONAL,
        '--zone {0} --host-type {1}'.format(self.zone, self.host_type))
    return name

  def TearDown(self):
    for name, res_type, scope in self._created_resources[::-1]:
      self.CleanUpResource(name, res_type, scope=scope)

  @test_case.Filters.skip('Failing', 'b/77953407')
  def testCreateInstanceOnSoleTenancyHost(self):
    host = self._CreateHost()
    name = self._name_generator.next()
    self._CreateResourceScheduleCleanUp(
        name, 'instances', e2e_test_base.ZONAL,
        '--zone {0} --sole-tenancy-host {1}'.format(self.zone, host))
    self.Run('compute instances describe {0} --zone {1} --quiet'.format(
        name, self.zone))
    self.AssertNewOutputContains(
        'host: {0}/projects/{1}/zones/{2}/hosts/{3}'.format(
            self.compute_uri, self.Project(), self.zone, host))


if __name__ == '__main__':
  e2e_test_base.main()
