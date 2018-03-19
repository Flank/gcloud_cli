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

"""Tests for the instance-groups managed create subcommand."""

from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


def SetUpZonal(test_obj, api_version):
  test_obj.SelectApi(api_version)
  test_obj.make_requests.side_effect = iter([
      [test_obj.messages.Zone(name='central2-a'),],
      [test_resources.MakeInstanceGroupManagers(API_VERSION)[0],],
      [test_resources.MakeInstanceGroups(test_obj.messages, API_VERSION)[0],],
      [test_resources.MakeAutoscalers(API_VERSION)[0],],
  ])
  test_obj.zone_1_get_request = [(
      test_obj.compute.zones,
      'Get',
      test_obj.messages.ComputeZonesGetRequest(
          project='my-project',
          zone='central2-a'))]
  test_obj.zone_ig_list_request = [(
      test_obj.compute.instanceGroups,
      'List',
      test_obj.messages.ComputeInstanceGroupsListRequest(
          maxResults=500,
          project='my-project',
          zone='zone-1',
      ))]
  test_obj.zone_as_list_request = [(
      test_obj.compute.autoscalers,
      'List',
      test_obj.messages.ComputeAutoscalersListRequest(
          maxResults=500,
          project='my-project',
          zone='zone-1'))]
  test_obj.template_1_uri = (
      '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
          test_obj.compute_uri))
  test_obj.http_health_check_uri = (
      '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
          test_obj.compute_uri))
  test_obj.https_health_check_uri = (
      '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'.format(
          test_obj.compute_uri))


def SetUpRegional(test_obj, api_version):
  test_obj.SelectApi(api_version)
  test_obj.make_requests.side_effect = iter([
      [
          test_resources.MakeInstanceGroupManagers(
              API_VERSION, scope_name='us-central2', scope_type='region')[0],
      ],
      [
          test_resources.MakeInstanceGroups(
              test_obj.messages, API_VERSION, scope_name='us-central2',
              scope_type='region')[0],
      ],
      [
          test_resources.MakeAutoscalers(
              API_VERSION, scope_name='us-central2', scope_type='region')[0],
      ],
  ])
  test_obj.region_ig_list_request = [(
      test_obj.compute.regionInstanceGroups,
      'List',
      test_obj.messages.ComputeRegionInstanceGroupsListRequest(
          maxResults=500,
          project='my-project',
          region='us-central2',
      ))]
  test_obj.region_as_list_request = [(
      test_obj.compute.regionAutoscalers,
      'List',
      test_obj.messages.ComputeRegionAutoscalersListRequest(
          maxResults=500,
          project='my-project',
          region='us-central2'))]
  test_obj.template_1_uri = (
      '{0}/projects/my-project/global/instanceTemplates/template-1'.format(
          test_obj.compute_uri))
  test_obj.http_health_check_uri = (
      '{0}/projects/my-project/global/httpHealthChecks/health-check-1'.format(
          test_obj.compute_uri))
  test_obj.https_health_check_uri = (
      '{0}/projects/my-project/global/httpsHealthChecks/health-check-2'.format(
          test_obj.compute_uri))
  test_obj.region_uri = (
      '{0}/projects/my-project/regions/us-central2'.format(
          test_obj.compute_uri))


class InstanceGroupManagersCreateZonalTest(test_base.BaseTest):

  def SetUp(self):
    SetUpZonal(self, API_VERSION)

  def testWithRequiredOptions(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone central2-a
          --template template-1
          --size 1
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='central2-a',
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[],
                  targetSize=1,
              ),
              project='my-project',
              zone='central2-a')),],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

    # Check default output formatting
    self.AssertOutputEquals("""\
    NAME     LOCATION  SCOPE  BASE_INSTANCE_NAME    SIZE  TARGET_SIZE  INSTANCE_TEMPLATE  AUTOSCALED
    group-1  zone-1    zone   test-instance-name-1  0     1            template-1         yes
    """, normalize_space=True)

  def testWithDescription(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone central2-a
          --template template-1
          --base-instance-name instance-1
          --size 1
          --description "Some description"
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[],
                  targetSize=1,
                  description='Some description',
              ),
              project='my-project',
              zone='central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testWithTargetPools(self):
    self.Run("""
        compute instance-groups managed create group-1
          --zone central2-a
          --template template-1
          --base-instance-name instance-1
          --size 1
          --target-pool target-pool-1,target-pool-2
        """)

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[self.compute_uri + '/projects/my-project/regions'
                               '/central2/targetPools/target-pool-1',
                               self.compute_uri + '/projects/my-project/'
                               'regions/central2/targetPools/target-pool-2'],
                  targetSize=1,
              ),
              project='my-project',
              zone='central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testUrisupport(self):
    self.Run("""
        compute instance-groups managed create
        {0}/projects/my-project/zones/central2-a/instanceGroupManagers/group-1
          --template {0}/projects/my-project/global/instanceTemplates/template-1
          --base-instance-name instance-1
          --size 1
          --target-pool {0}/projects/cloud-autopilot-test/regions/central2/targetPools/target-pool-1
        """.format(self.compute_uri))

    self.CheckRequests(
        self.zone_1_get_request,
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  zone='central2-a',
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  targetPools=[self.compute_uri + '/projects/'
                               'cloud-autopilot-test/regions/central2/'
                               'targetPools/target-pool-1'],
              ),
              project='my-project',
              zone='central2-a'))],
        self.zone_ig_list_request,
        self.zone_as_list_request,
    )

  def testRequiredSize(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --size: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --zone central2-a
            --template template-1
            --base-instance-name instance-1
          """)

  def testRequiredTemplate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --zone central2-a
            --base-instance-name instance-1
            --size 1
          """)

  def testPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central1-a'),
            self.messages.Zone(name='us-central1-b'),
            self.messages.Zone(name='us-central2-a'),
        ],
        [],
        [],
    ])
    self.WriteInput('2\n')

    self.Run("""
        compute instance-groups managed create group-1
          --template template-1
          --base-instance-name instance-1
          --size 1
    """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.zones,
          'Get',
          self.messages.ComputeZonesGetRequest(
              project='my-project',
              zone='us-central1-a'))],
        [(self.compute.instanceGroupManagers,
          'Insert',
          self.messages.ComputeInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  baseInstanceName='instance-1',
                  instanceTemplate=(
                      'https://www.googleapis.com/compute/v1/projects/'
                      'my-project/global/instanceTemplates/template-1'),
                  name='group-1',
                  namedPorts=[],
                  targetPools=[],
                  targetSize=1,
                  zone='us-central1-a'),
              project='my-project',
              zone='us-central1-a'))],
        [],
    )


class InstanceGroupManagersCreateRegionalTest(test_base.BaseTest):

  def SetUp(self):
    SetUpRegional(self, API_VERSION)

  def testWithRequiredOptions(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --size 1
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='group-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2')),],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithDescription(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --description "Some description"
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[],
                  targetSize=1,
                  description='Some description',
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testWithTargetPools(self):
    self.Run("""
        compute instance-groups managed create group-1
          --region us-central2
          --template template-1
          --base-instance-name instance-1
          --size 1
          --target-pool target-pool-1,target-pool-2
        """)

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetPools=[self.compute_uri + '/projects/my-project/regions'
                               '/us-central2/targetPools/target-pool-1',
                               self.compute_uri + '/projects/my-project/'
                               'regions/us-central2/targetPools/target-pool-2'],
                  targetSize=1,
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testUrisupport(self):
    self.Run("""
        compute instance-groups managed create
        {0}/projects/my-project/regions/us-central2/instanceGroupManagers/group-1
          --template {0}/projects/my-project/global/instanceTemplates/template-1
          --base-instance-name instance-1
          --size 1
          --target-pool {0}/projects/cloud-autopilot-test/regions/us-central2/targetPools/target-pool-1
        """.format(self.compute_uri))

    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  name='group-1',
                  region=self.region_uri,
                  baseInstanceName='instance-1',
                  instanceTemplate=self.template_1_uri,
                  targetSize=1,
                  targetPools=[self.compute_uri + '/projects/'
                               'cloud-autopilot-test/regions/us-central2/'
                               'targetPools/target-pool-1'],
              ),
              project='my-project',
              region='us-central2'))],
        self.region_ig_list_request,
        self.region_as_list_request,
    )

  def testRequiredSize(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --size: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --region us-central2
            --template template-1
            --base-instance-name instance-1
          """)

  def testRequiredTemplate(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --template: Must be specified.'
        ):
      self.Run("""
          compute instance-groups managed create group-1
            --region us-central2
            --base-instance-name instance-1
            --size 1
          """)

  def testPrompt(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central2'),
        ],
        [
            self.messages.Zone(name='us-central1-a'),
            self.messages.Zone(name='us-central1-b'),
            self.messages.Zone(name='us-central2-a'),
        ],
        [],
        [],
    ])
    self.WriteInput('1\n')

    self.Run("""
        compute instance-groups managed create group-1
          --template template-1
          --base-instance-name instance-1
          --size 1
    """)

    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
        [(self.compute.regionInstanceGroupManagers,
          'Insert',
          self.messages.ComputeRegionInstanceGroupManagersInsertRequest(
              instanceGroupManager=self.messages.InstanceGroupManager(
                  baseInstanceName='instance-1',
                  instanceTemplate=(
                      'https://www.googleapis.com/compute/v1/projects/'
                      'my-project/global/instanceTemplates/template-1'),
                  name='group-1',
                  namedPorts=[],
                  targetPools=[],
                  targetSize=1,
                  region=self.region_uri,),
              project='my-project',
              region='us-central2'))],
        [],
    )

  def testNegativeSize(self):
    with self.assertRaisesRegexp(
        cli_test_base.MockArgumentError,
        'argument --size: Value must be greater than or equal to 0; '
        'received: -1'):
      self.Run("""
          compute instance-groups managed create group-1
            --zone central2-a
            --template template-1
            --size -1
          """)

if __name__ == '__main__':
  test_case.main()
