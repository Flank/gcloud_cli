# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Integration tests for creating/deleting sole tenant hosts."""

import re

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base
from tests.lib.surface.compute import resource_managers

_HOST_TYPE = 'n1-host-64-416'
_ZONES_WITH_N1_HOST_64_416 = [
    'europe-west1-d',
    'us-central1-b',
    'us-central1-c',
    'us-east1-b',
    'us-east1-c',
    'us-east1-d',
]


class SoleTenantHostTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='sole-tenancy-host', sequence_start=1)

  @test_case.Filters.skip('Failing', 'b/77953407')
  def testDescribeHost(self):
    # Sometimes it's impossible to create a sole tenancy host in a zone because
    # of temporary conditions in the zone. Such situation shouldn't be
    # considered a failure of this test.
    # Because of that this test tries to run in different zones as long as the
    # failure was caused by an exception suggesting to try later or in a
    # different zone.
    for zone in _ZONES_WITH_N1_HOST_64_416:
      try:
        with resource_managers.SoleTenancyHost(
            zone, _HOST_TYPE, self._name_generator, self.Run) as host:
          description = self.Run(
              """compute sole-tenancy hosts describe {0} --zone {1} --quiet
                 --format=disable""".format(host.name, host.zone))
          self.assertEqual('compute#host', description.kind)
          self.assertEqual(host.name, description.name)
          return  # Test succeeded, no need to keep trying.
      except exceptions.ToolException as e:
        if re.search(r'Try a different zone, or try again later.', e.message,
                     flags=re.IGNORECASE):
          log.Print('Got transient error {!r} in {!r}.'.format(e.message, zone))
        else:
          raise  # Non-retriable error, fail the test.
    self.fail('Got transient failure in each and every allowed zone.')


class SoleTenantHostTypesTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='sole-tenancy-host', sequence_start=1)
    self.zone = 'us-central1-b'
    self.scope_flag[e2e_test_base.ZONAL] = '--zone ' + self.zone
    self._created_resources = []

  def testListHostTypes(self):
    self.Run('compute sole-tenancy host-types list')
    self.AssertNewOutputContains('n1-host-64-416')


if __name__ == '__main__':
  test_case.main()
