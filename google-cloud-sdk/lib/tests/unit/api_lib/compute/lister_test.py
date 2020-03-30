# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Unit tests for the lister module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import utils
import mock
import six


COMPUTE_V1_MESSAGES = apis.GetMessagesModule('compute', 'v1')
_ZONES = [
    COMPUTE_V1_MESSAGES.Zone(name='central1-a'),
    COMPUTE_V1_MESSAGES.Zone(name='central1-b'),
    COMPUTE_V1_MESSAGES.Zone(name='central2-a'),
    COMPUTE_V1_MESSAGES.Zone(name='central2-b'),
    COMPUTE_V1_MESSAGES.Zone(name='central2-c'),
    COMPUTE_V1_MESSAGES.Zone(name='central3-a'),
    COMPUTE_V1_MESSAGES.Zone(name='central3-b'),
]

_REGIONS = [
    COMPUTE_V1_MESSAGES.Region(
        name='central1',
        zones=[
            'http://example.com/compute/v1/my-project/zones/central1-a',
            'http://example.com/compute/v1/my-project/zones/central1-b',
        ]),
    COMPUTE_V1_MESSAGES.Region(
        name='central2',
        zones=[
            'http://example.com/compute/v1/my-project/zones/central2-a',
            'http://example.com/compute/v1/my-project/zones/central2-b',
            'http://example.com/compute/v1/my-project/zones/central2-c',
        ]),
    COMPUTE_V1_MESSAGES.Region(
        name='central3',
        zones=[
            'http://example.com/compute/v1/my-project/zones/central3-a',
            'http://example.com/compute/v1/my-project/zones/central3-b',
        ]),
]


class MockDisplayInfo(object):

  def __init__(self, transforms=None, aliases=None):
    self.transforms = transforms
    self.aliases = aliases


class MockArgs(object):

  def __init__(self, **kwargs):
    for name, value in six.iteritems(kwargs):
      setattr(self, name, value)

  def __contains__(self, item):
    return item in self.__dict__

  def GetDisplayInfo(self):  # pylint: disable=invalid-name, huh?
    return MockDisplayInfo(transforms={})


class GetGlobalResourcesTest(test_case.TestCase):
  """Ensures that filtering for GetGlobalResources() works."""

  def SetUp(self):
    self.compute = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    self.mock_http = mock.MagicMock()

    self.networks_response = [
        self.messages.Network(name='network-1'),
        self.messages.Network(name='network-2'),
        self.messages.Network(name='network-3'),
    ]

    self.batch_url = 'https://www.googleapis.com/batch/compute'

  def RegisterExpectedRequests(self, expected_network_requests=None):

    def make_requests(requests, batch_url, *unused_args, **unused_kwargs):
      self.assertEqual(batch_url, self.batch_url)
      if requests[0][0] == self.compute.networks:
        self.assertEqual(requests, expected_network_requests)
        return self.networks_response

      else:
        self.fail('expected service to be networks')

    self.make_requests.side_effect = make_requests

  def GetGlobalResources(self, **kwargs):
    args = dict(
        service=self.compute.networks,
        project='my-project',
        filter_expr=None,
        http=self.mock_http,
        batch_url=self.batch_url,
        errors=[])
    args.update(kwargs)
    return lister.GetGlobalResources(**args)

  def testFilteringWithNameRegex(self):
    self.RegisterExpectedRequests(
        expected_network_requests=[
            (self.compute.networks,
             'List',
             self.messages.ComputeNetworksListRequest(
                 filter=r'name eq name-1',
                 maxResults=500, project='my-project')),
        ])
    self.GetGlobalResources(filter_expr='name eq name-1')

  def testWithNoFiltering(self):
    self.RegisterExpectedRequests(
        expected_network_requests=[
            (self.compute.networks,
             'List',
             self.messages.ComputeNetworksListRequest(
                 maxResults=500, project='my-project')),
        ])
    self.GetGlobalResources()


class GetRegionalResourcesTest(test_case.TestCase):
  """Ensures that region filtering for GetRegionalResources() works."""

  def SetUp(self):
    self.compute = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    self.mock_http = mock.MagicMock()

    self.target_pools_response = [
        self.messages.TargetPool(name='pool-1'),
        self.messages.TargetPool(name='pool-2'),
        self.messages.TargetPool(name='pool-3'),
    ]

    self.batch_url = 'https://www.googleapis.com/batch/compute'

  def RegisterExpectedRequests(self, expected_target_pool_requests=None):

    def make_requests(requests, batch_url, *unused_args, **unused_kwargs):
      self.assertEqual(batch_url, self.batch_url)
      if requests[0][0] == self.compute.regions:
        self.assertEqual(
            requests,
            [(self.compute.regions,
              self.messages.ComputeRegionsListRequest(project='my-project'))])
        return _REGIONS

      elif requests[0][0] == self.compute.targetPools:
        self.assertEqual(requests, expected_target_pool_requests)
        return self.target_pools_response

      else:
        self.fail('expected service to be either regions or targetPools')

    self.make_requests.side_effect = make_requests

  def GetRegionalResources(self, **kwargs):
    args = dict(
        service=self.compute.targetPools,
        project='my-project',
        requested_regions=[],
        filter_expr=None,
        http=self.mock_http,
        batch_url=self.batch_url,
        errors=[])
    args.update(kwargs)
    return lister.GetRegionalResources(**args)

  def testFilteringWithNameRegex(self):
    self.RegisterExpectedRequests(
        expected_target_pool_requests=[
            (self.compute.targetPools,
             'AggregatedList',
             self.messages.ComputeTargetPoolsAggregatedListRequest(
                 filter=r'name eq name-1',
                 maxResults=500,
                 project='my-project')),
        ])
    self.GetRegionalResources(filter_expr='name eq name-1')

  def testWithNoFiltering(self):
    self.RegisterExpectedRequests(
        expected_target_pool_requests=[
            (self.compute.targetPools,
             'AggregatedList',
             self.messages.ComputeTargetPoolsAggregatedListRequest(
                 maxResults=500,
                 project='my-project')),
        ])
    self.GetRegionalResources()

  def testRegionFilteringWithTwoRegions(self):
    self.RegisterExpectedRequests(
        expected_target_pool_requests=[
            (self.compute.targetPools,
             'List',
             self.messages.ComputeTargetPoolsListRequest(
                 maxResults=500, project='my-project', region='central1')),
            (self.compute.targetPools,
             'List',
             self.messages.ComputeTargetPoolsListRequest(
                 maxResults=500, project='my-project', region='central2')),
        ])
    self.GetRegionalResources(requested_regions=['central1', 'central2'])


class GetZonalResourcesTest(test_case.TestCase):
  """Ensures that zone and region filtering for GetZonalResources() work."""

  def SetUp(self):
    self.compute = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests',
        autospec=True)
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()

    self.mock_http = mock.MagicMock()

    self.instances_response = [
        self.messages.Instance(name='instance-1'),
        self.messages.Instance(name='instance-2'),
        self.messages.Instance(name='instance-3'),
    ]

    self.batch_url = 'https://www.googleapis.com/batch/compute'

  def GetZonalResources(self, **kwargs):
    args = dict(
        service=self.compute.instances,
        project='my-project',
        requested_zones=[],
        filter_expr=None,
        http=self.mock_http,
        batch_url=self.batch_url,
        errors=[])
    args.update(kwargs)
    return lister.GetZonalResources(**args)

  def RegisterExpectedRequests(self, expected_instance_requests=None):

    def make_requests(requests, batch_url, *unused_args, **unused_kwargs):
      self.assertEqual(batch_url, self.batch_url)
      if requests[0][0] == self.compute.regions:
        self.assertEqual(
            requests,
            [(self.compute.regions,
              self.messages.ComputeRegionsListRequest(project='my-project'))])
        return _REGIONS

      elif requests[0][0] == self.compute.zones:
        self.assertEqual(
            requests,
            [(self.compute.zones,
              self.messages.ComputeZonesListRequest(project='my-project'))])
        return _ZONES

      elif requests[0][0] == self.compute.instances:
        self.assertEqual(requests, expected_instance_requests)
        return self.instances_response

      else:
        self.fail('expected service to be one of regions, zones, or instances')

    self.make_requests.side_effect = make_requests

  def testWithNoFiltering(self):
    self.RegisterExpectedRequests(
        expected_instance_requests=[
            (self.compute.instances,
             'AggregatedList',
             self.messages.ComputeInstancesAggregatedListRequest(
                 maxResults=500,
                 project='my-project')),
        ])
    self.GetZonalResources()

  def testFilteringWithNameRegex(self):
    self.RegisterExpectedRequests(
        expected_instance_requests=[
            (self.compute.instances,
             'AggregatedList',
             self.messages.ComputeInstancesAggregatedListRequest(
                 filter=r'name eq name-1',
                 maxResults=500,
                 project='my-project')),
        ])
    self.GetZonalResources(filter_expr='name eq name-1')

  def testZoneFilteringWithOneZone(self):
    self.RegisterExpectedRequests(
        expected_instance_requests=[
            (self.compute.instances,
             'List',
             self.messages.ComputeInstancesListRequest(
                 maxResults=500, project='my-project', zone='central1-a')),
        ])
    self.GetZonalResources(requested_zones=['central1-a'])

  def testZoneFilteringWithTwoZones(self):
    self.RegisterExpectedRequests(
        expected_instance_requests=[
            (self.compute.instances,
             'List',
             self.messages.ComputeInstancesListRequest(
                 maxResults=500, project='my-project', zone='central1-a')),
            (self.compute.instances,
             'List',
             self.messages.ComputeInstancesListRequest(
                 maxResults=500, project='my-project', zone='central2-b')),
        ])
    self.GetZonalResources(requested_zones=['central1-a', 'central2-b'])


class GetResourcesDictsTests(test_case.TestCase):

  def SetUp(self):
    self.compute = apis.GetClientInstance('compute', 'v1', no_http=True)
    self.messages = apis.GetMessagesModule('compute', 'v1')

    self.result = []
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        return_value=self.result)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testGetZonalResourcesDicts(self):
    service = self.compute.instances
    project = 'my-project'
    requested_zones = ['my-zone']
    filter_expr = ''
    http = object()
    batch_url = object()
    errors = []

    self.assertIs(self.result,
                  lister.GetZonalResourcesDicts(
                      service=service,
                      project=project,
                      requested_zones=requested_zones,
                      filter_expr=filter_expr,
                      http=http,
                      batch_url=batch_url,
                      errors=errors))

    self.assertListEqual(errors, [])
    self.list_json.assert_called_once_with(
        requests=[(service, 'List', self.messages.ComputeInstancesListRequest(
            filter=filter_expr,
            maxResults=500,
            project=project,
            zone='my-zone'))],
        http=http,
        batch_url=batch_url,
        errors=errors)

  def testGetRegionalResourcesDicts(self):
    service = self.compute.targetPools
    project = 'my-project'
    requested_regions = ['my-region']
    filter_expr = ''
    http = object()
    batch_url = object()
    errors = []

    self.assertIs(self.result,
                  lister.GetRegionalResourcesDicts(
                      service=service,
                      project=project,
                      requested_regions=requested_regions,
                      filter_expr=filter_expr,
                      http=http,
                      batch_url=batch_url,
                      errors=errors))

    self.assertListEqual(errors, [])
    self.list_json.assert_called_once_with(
        requests=[(service, 'List', self.messages.ComputeTargetPoolsListRequest(
            filter=filter_expr,
            maxResults=500,
            project=project,
            region='my-region'))],
        http=http,
        batch_url=batch_url,
        errors=errors)

  def testGetGlobalResourcesDicts(self):
    service = self.compute.zones
    project = 'my-project'
    filter_expr = ''
    http = object()
    batch_url = object()
    errors = []

    self.assertIs(self.result,
                  lister.GetGlobalResourcesDicts(
                      service=service,
                      project=project,
                      filter_expr=filter_expr,
                      http=http,
                      batch_url=batch_url,
                      errors=errors))

    self.assertListEqual(errors, [])
    self.list_json.assert_called_once_with(
        requests=[(service, 'List', self.messages.ComputeZonesListRequest(
            filter=filter_expr,
            maxResults=500,
            project=project))],
        http=http,
        batch_url=batch_url,
        errors=errors)


class InvokeTests(test_case.TestCase):

  def SetUp(self):
    self.called = False

  def testInvoke(self):
    frontend = object()
    result = object()

    def implementation(f):
      self.assertFalse(self.called)
      self.called = True
      self.assertIs(f, frontend)
      return result

    self.assertIs(result, lister.Invoke(frontend, implementation))
    self.assertTrue(self.called)


class ComposeSyncImplementationTest(test_case.TestCase):

  def SetUp(self):
    self.generator_result = None

  def testComposeSyncImplementation(self):
    frontend = object()
    generator_result = object()
    executor_result = object()
    def generator(f):
      self.assertIsNone(self.generator_result)
      self.assertIs(f, frontend)
      self.generator_result = generator_result
      return generator_result

    def executor(r, f):
      self.assertIs(r, self.generator_result)
      self.assertIs(f, frontend)
      return executor_result

    implementation = lister.ComposeSyncImplementation(generator, executor)

    self.assertIs(executor_result, implementation(frontend))


class AllScopesTests(test_case.TestCase):

  def testAllScopes(self):
    projects = object()
    zonal = object()
    regional = object()

    all_scopes = lister.AllScopes(projects, zonal, regional)

    self.assertIs(all_scopes.projects, projects)
    self.assertIs(all_scopes.zonal, zonal)
    self.assertIs(all_scopes.regional, regional)


class AddListerArgsTestBase(test_case.TestCase):

  class Parser(object):

    def __init__(self):
      self.arguments = []

    def add_argument(self, name, *args, **kwargs):
      _ = args
      _ = kwargs
      self.arguments.append(name)

    def add_mutually_exclusive_group(self):
      return self


class AddBaseListerArgsTests(AddListerArgsTestBase):

  def testAddBaseListerArgs(self):
    parser = self.Parser()

    lister.AddBaseListerArgs(parser)

    self.assertListEqual(['names', '--regexp'], parser.arguments)


class AddZonalListerArgsTests(AddListerArgsTestBase):

  def testAddZonalListerArgs(self):
    parser = self.Parser()

    lister.AddZonalListerArgs(parser)

    self.assertListEqual(['names', '--regexp', '--zones'], parser.arguments)


class AddRegionalListerArgsTests(AddListerArgsTestBase):

  def testAddZonalListerArgs(self):
    parser = self.Parser()

    lister.AddRegionsArg(parser)

    self.assertListEqual(['names', '--regexp', '--regions'], parser.arguments)


class AddMultiScopeListerArgsTests(AddListerArgsTestBase):

  def testAddNoScopeArgs(self):
    parser = self.Parser()

    lister.AddMultiScopeListerFlags(parser)

    self.assertListEqual(['names', '--regexp'], parser.arguments)

  def testAddAllScopeArgs(self):
    parser = self.Parser()

    lister.AddMultiScopeListerFlags(
        parser, zonal=True, regional=True, global_=True)

    self.assertListEqual(
        ['names', '--regexp', '--zones', '--regions',
         '--global'], parser.arguments)


class GetListCommandFrontendPrototypeTests(test_case.TestCase):

  def testSimple(self):
    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
    )

    frontend = lister._GetListCommandFrontendPrototype(args)

    self.assertEqual(frontend.filter, (None, None))
    self.assertIsNone(frontend.max_results)
    self.assertIsNone(frontend.scope_set)

  def testComplex(self):
    args = MockArgs(
        filter='name=asdf',
        page_size=999,
        limit=123,
    )

    frontend = lister._GetListCommandFrontendPrototype(args)

    self.assertEqual(frontend.filter, (None, r'name eq ".*\basdf\b.*"'))
    self.assertEqual(frontend.max_results, None)
    self.assertIsNone(frontend.scope_set)


class GetBaseListerFrontendPrototypeTests(test_case.TestCase):

  def testSimpleDefaultFilter(self):
    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
    )

    frontend = lister._GetBaseListerFrontendPrototype(args)

    self.assertEqual(args.filter, None)
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertIsNone(frontend.scope_set)

  def testSimpleEmptyFilter(self):
    args = MockArgs(
        filter='',
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
    )

    frontend = lister._GetBaseListerFrontendPrototype(args)

    self.assertEqual(args.filter, '')
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertIsNone(frontend.scope_set)

  def testComplex(self):
    args = MockArgs(
        filter='name=asdf',
        page_size=None,
        limit=None,
        names=[
            'name1',
            'https://compute.googleapis.com/compute/v1/projects/'
            'my-project/zones/zone-1/disks/disk-1',
        ],
        regexp='my.*regexp',
    )

    frontend = lister._GetBaseListerFrontendPrototype(args)

    self.assertEqual(
        args.filter,
        '(name=asdf) AND (name ~ "^my.*regexp$") AND ((name =(name1)) OR '
        '(selfLink =(https://compute.googleapis.com/compute/v1/projects/'
        'my-project/zones/zone-1/disks/disk-1)))')
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertIsNone(frontend.scope_set)


class ParseZonalFlagsTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testSimple(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
        zones=[],
    )

    frontend = lister.ParseZonalFlags(args, resource_registry)

    self.assertEqual(args.filter, None)
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set,
                     lister.AllScopes(
                         projects=[project], zonal=True, regional=False))

  def testComplex(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
        zones=['my-zone-1', 'my-zone-2'],
    )

    zone1 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/zones/my-zone-1')

    zone2 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/zones/my-zone-2')

    frontend = lister.ParseZonalFlags(args, resource_registry)

    self.assertEqual(args.filter, '(zone :(my-zone-1 my-zone-2))')
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set, lister.ZoneSet([zone1, zone2]))


class ParseRegionalFlagsTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testSimple(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
        regions=[],
    )

    frontend = lister.ParseRegionalFlags(args, resource_registry)

    self.assertEqual(args.filter, None)
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set,
                     lister.AllScopes(
                         projects=[project], zonal=False, regional=True))

  def testComplex(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
        regions=['my-region-1', 'my-region-2'],
    )

    region1 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/regions/my-region-1')

    region2 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/regions/my-region-2')

    frontend = lister.ParseRegionalFlags(args, resource_registry)

    self.assertEqual(args.filter, '(region :(my-region-1 my-region-2))')
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set, lister.RegionSet([region1, region2]))


class ParseGlobalFlagsTests(cli_test_base.CliTestBase):

  def Project(self):
    """See base class."""
    return 'lister-project'

  def testSimple(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        self.Project(), collection='compute.projects')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
    )

    frontend = lister.ParseNamesAndRegexpFlags(args, resource_registry)

    self.assertEqual(args.filter, None)
    self.assertEqual(frontend.filter, None)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set, lister.GlobalScope([project]))


class ParseMultiScopeFlagsTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testAllScopes(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
        zones=[],
        regions=[],
    )

    frontend = lister.ParseMultiScopeFlags(args, resource_registry)

    self.assertEqual(args.filter, None)
    self.assertIsNone(frontend.filter)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set,
                     lister.AllScopes(
                         projects=[project], zonal=True, regional=True))

  def testGlobal(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    args = MockArgs(
        filter=None,
        page_size=None,
        limit=None,
        names=None,
        regexp=None,
    )
    setattr(args, 'global', True)  # global is a keyword

    frontend = lister.ParseMultiScopeFlags(args, resource_registry)

    self.assertIsNone(args.filter)
    self.assertIsNone(frontend.filter)
    self.assertIsNone(frontend.max_results)
    self.assertEqual(frontend.scope_set, lister.GlobalScope([project]))


class ZonalListerTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testAggregatedList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.AllScopes([project], True, False))

    zonal_lister = lister.ZonalLister(self.api_mock.adapter, 'service')

    result = list(zonal_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.mock_get_zonal_resources.assert_called_once_with(
        service='service',
        project=self.Project(),
        requested_zones=[],
        filter_expr='filter',
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])

  def testBatchList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    zone1 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/zones/my-zone-1')

    zone2 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/zones/my-zone-2')

    frontend = lister._Frontend('filter', 123, lister.ZoneSet([zone1, zone2]))

    zonal_lister = lister.ZonalLister(self.api_mock.adapter, 'service')

    result = list(zonal_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.mock_get_zonal_resources.assert_called_once_with(
        service='service',
        project=self.Project(),
        requested_zones=['my-zone-1', 'my-zone-2'],
        filter_expr='filter',
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])


class RegionalListerTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testRepr(self):
    regional_lister = lister.RegionalLister('client', 'service')
    # Python 2: u"RegionalLister(u'client', u'service')"
    # Python 3: "RegionalLister('client', 'service')"
    expected = 'RegionalLister({}, {})'.format(repr('client'), repr('service'))
    self.assertEqual(repr(regional_lister), expected)

  def testEq(self):
    client = object()
    service = object()
    regional_lister1 = lister.RegionalLister(client, service)
    regional_lister2 = lister.RegionalLister(client, service)

    self.assertEqual(regional_lister1, regional_lister2)
    self.assertEqual(hash(regional_lister1), hash(regional_lister2))

  def testNeq(self):
    client1 = object()
    client2 = object()
    service = object()
    regional_lister1 = lister.RegionalLister(client1, service)
    regional_lister2 = lister.RegionalLister(client2, service)

    self.assertNotEqual(regional_lister1, regional_lister2)

  def testDeepcopy(self):
    regional_lister = lister.RegionalLister('client', 'service')

    self.assertEqual(regional_lister, copy.deepcopy(regional_lister))

  def testAggregatedList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.AllScopes([project], False, True))

    regional_lister = lister.RegionalLister(self.api_mock.adapter, 'service')

    result = list(regional_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.mock_get_regional_resources.assert_called_once_with(
        service='service',
        project=self.Project(),
        requested_regions=[],
        filter_expr='filter',
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])

  def testBatchList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    region1 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/regions/my-region-1')

    region2 = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/'
        'lister-project/regions/my-region-2')

    frontend = lister._Frontend('filter', 123,
                                lister.RegionSet([region1, region2]))

    regional_lister = lister.RegionalLister(self.api_mock.adapter, 'service')

    result = list(regional_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.mock_get_regional_resources.assert_called_once_with(
        service='service',
        project=self.Project(),
        requested_regions=['my-region-1', 'my-region-2'],
        filter_expr='filter',
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])


class GlobalListerTests(cli_test_base.CliTestBase):

  def Project(self):
    """See base class."""
    return 'lister-project'

  def testRepr(self):
    global_lister = lister.GlobalLister('client', 'service')
    # Python 2: u"GlobalLister(u'client', u'service')"
    # Python 3: "GlobalLister('client', 'service')"
    expected = 'GlobalLister({}, {})'.format(repr('client'), repr('service'))
    self.assertEqual(repr(global_lister), expected)

  def testEq(self):
    client = object()
    service = object()
    global_lister1 = lister.GlobalLister(client, service)
    global_lister2 = lister.GlobalLister(client, service)

    self.assertEqual(global_lister1, global_lister2)
    self.assertEqual(hash(global_lister1), hash(global_lister2))

  def testNeq(self):
    client1 = object()
    client2 = object()
    service = object()
    global_lister1 = lister.GlobalLister(client1, service)
    global_lister2 = lister.GlobalLister(client2, service)

    self.assertNotEqual(global_lister1, global_lister2)

  def testDeepcopy(self):
    global_lister = lister.GlobalLister('client', 'service')

    self.assertEqual(global_lister, copy.deepcopy(global_lister))

  def testBatchList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        self.Project(), collection='compute.projects')

    frontend = lister._Frontend('filter', 123, lister.GlobalScope([project]))

    global_lister = lister.GlobalLister(self.api_mock.adapter, 'service')

    result = list(global_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.mock_get_global_resources.assert_called_once_with(
        service='service',
        project=self.Project(),
        filter_expr='filter',
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])


class MultiScopeListerTests(cli_test_base.CliTestBase):

  def Project(self):
    return 'lister-project'

  def testRepr(self):
    multi_scope_lister = lister.MultiScopeLister(
        'client', 'zonal_service', 'regional_service', 'global_service',
        'aggregation_service')
    # Python 2: u"MultiScopeLister(u'client', u'zonal_service',
    #   u'regional_service', u'global_service', u'aggregation_service')"
    # Python 3: "MultiScopeLister('client', 'zonal_service','regional_service',
    #  'global_service', 'aggregation_service')"
    expected = 'MultiScopeLister({}, {}, {}, {}, {}, {})'.format(
        repr('client'), repr('zonal_service'), repr('regional_service'),
        repr('global_service'), repr('aggregation_service'), repr(True))
    self.assertEqual(repr(multi_scope_lister), expected)

  def testEq(self):
    client = object()
    service = object()
    regional_lister1 = lister.MultiScopeLister(client, regional_service=service)
    regional_lister2 = lister.MultiScopeLister(client, regional_service=service)

    self.assertEqual(regional_lister1, regional_lister2)
    self.assertEqual(hash(regional_lister1), hash(regional_lister2))

  def testNeq(self):
    client1 = object()
    client2 = object()
    service = object()
    regional_lister1 = lister.MultiScopeLister(
        client1, regional_service=service)
    regional_lister2 = lister.MultiScopeLister(
        client2, regional_service=service)

    self.assertNotEqual(regional_lister1, regional_lister2)

  def testDeepcopy(self):
    global_lister = lister.MultiScopeLister(
        'client', global_service='global_service')

    self.assertEqual(global_lister, copy.deepcopy(global_lister))

  def testAggregatedList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.list_json = lister_patcher.start()
    self.list_json.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.AllScopes([project], True, True))

    instances_lister = lister.MultiScopeLister(
        self.api_mock.adapter,
        aggregation_service=self.api_mock.adapter.apitools_client.instances)

    result = list(instances_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.list_json.assert_called_once_with(
        requests=[
            (self.api_mock.adapter.apitools_client.instances, 'AggregatedList',
             self.api_mock.adapter.messages
             .ComputeInstancesAggregatedListRequest(
                 filter='filter',
                 maxResults=123,
                 project='lister-project',
                 includeAllScopes=True))
        ],
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])

  def testGlobalList(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.list_json = lister_patcher.start()
    self.list_json.return_value = [1, 2, 3]

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.GlobalScope([project]))

    zones_lister = lister.MultiScopeLister(
        self.api_mock.adapter,
        global_service=self.api_mock.adapter.apitools_client.zones)

    result = list(zones_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

    self.list_json.assert_called_once_with(
        requests=[(self.api_mock.adapter.apitools_client.zones, 'List',
                   self.api_mock.adapter.messages.ComputeZonesListRequest(
                       filter='filter',
                       maxResults=123,
                       project='lister-project'))],
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])

  def testWithPartialError(self):

    def make_server_responses(*_, **kwargs):
      for num in range(5):
        if num == 2:
          kwargs['errors'].append((400, 'Invalid field name'))
        else:
          yield num

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.list_json = lister_patcher.start()
    self.list_json.side_effect = make_server_responses

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://www.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.GlobalScope([project]))

    zones_lister = lister.MultiScopeLister(
        self.api_mock.adapter,
        global_service=self.api_mock.adapter.apitools_client.zones)

    result = list(zones_lister(frontend))

    self.assertListEqual(result, [0, 1, 3, 4])

    errors = [(400, u'Invalid field name')]
    self.list_json.assert_called_once_with(
        requests=[(self.api_mock.adapter.apitools_client.zones, 'List',
                   self.api_mock.adapter.messages.ComputeZonesListRequest(
                       filter='filter',
                       maxResults=123,
                       project='lister-project')),
                 ],
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=errors)

  def testWithError(self):
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.list_json = lister_patcher.start()
    self.list_json.side_effect = Exception('my-exception')

    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    project = resource_registry.Parse(
        'https://compute.googleapis.com/compute/v1/projects/lister-project')

    frontend = lister._Frontend('filter', 123,
                                lister.GlobalScope([project]))

    zones_lister = lister.MultiScopeLister(
        self.api_mock.adapter,
        global_service=self.api_mock.adapter.apitools_client.zones)

    with self.AssertRaisesExceptionMatches(Exception, 'my-exception'):
      list(zones_lister(frontend))

    self.list_json.assert_called_once_with(
        requests=[(self.api_mock.adapter.apitools_client.zones, 'List',
                   self.api_mock.adapter.messages.ComputeZonesListRequest(
                       filter='filter',
                       maxResults=123,
                       project='lister-project'))],
        http=self.api_mock.adapter.apitools_client.http,
        batch_url=self.api_mock.adapter.batch_url,
        errors=[])


class ZonalParallelListerTests(test_base.BaseTest):

  def Project(self):
    """See base class."""
    return 'lister-project'

  def testRepr(self):
    zonal_lister = lister.ZonalParallelLister('client', 'service', 'resources')
    # Python 2: u"ZonalParallelLister(u'client', u'service', u'resources')"
    # Python 3: "ZonalParallelLister('client', 'service', 'resources')"
    expected = 'ZonalParallelLister({}, {}, {})'.format(
        repr('client'), repr('service'), repr('resources'))
    self.assertEqual(repr(zonal_lister), expected)

  def testEq(self):
    client = object()
    service = object()
    resource_registry = object()
    zonal_lister1 = lister.ZonalParallelLister(client, service,
                                               resource_registry)
    zonal_lister2 = lister.ZonalParallelLister(client, service,
                                               resource_registry)

    self.assertEqual(zonal_lister1, zonal_lister2)
    self.assertEqual(hash(zonal_lister1), hash(zonal_lister2))
    self.assertNotEqual(zonal_lister1, object())

  def testNeq(self):
    client1 = object()
    client2 = object()
    service = object()
    resource_registry = object()
    zonal_lister1 = lister.ZonalParallelLister(client1, service,
                                               resource_registry)
    zonal_lister2 = lister.ZonalParallelLister(client2, service,
                                               resource_registry)

    self.assertNotEqual(zonal_lister1, zonal_lister2)

  def testDeepcopy(self):
    zonal_lister = lister.ZonalParallelLister('client', 'service', 'resources')

    self.assertEqual(zonal_lister, copy.deepcopy(zonal_lister))

  def testExplicitZoneList(self):
    # In this test fronted is provided with precise set of zones
    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    frontend = lister._Frontend('filter', 123,
                                self.MakeZoneSet(['zone-1', 'zone-2']))

    zonal_lister = lister.ZonalParallelLister(
        self.api_mock.adapter, self.api_mock.adapter.apitools_client.instances,
        'registry')

    self.ExpectListerInvoke(
        scope_set=frontend.scope_set,
        filter_expr=frontend.filter,
        max_results=frontend.max_results,
        result=[1, 2, 3])
    result = list(zonal_lister(frontend))

    self.assertListEqual(result, [1, 2, 3])

  def testNoExplicitZoneList(self):
    # In this tests zonal wildcard is used, zones have to be fetched by
    # implementation
    self.api_mock = utils.ComputeApiMock('v1').Start()
    self.addCleanup(self.api_mock.Stop)

    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')

    frontend = lister._Frontend('filter', 123, self.MakeAllScopes(zonal=True))

    zonal_lister = lister.ZonalParallelLister(
        self.api_mock.adapter, self.api_mock.adapter.apitools_client.instances,
        resource_registry)

    zone_set = self.MakeZoneSet(['zone-1', 'zone-2'])

    # This is for zones listing
    self.ExpectListerInvoke(
        scope_set=self.MakeGlobalScope(),
        result=[{
            'selfLink': z.SelfLink()
        } for z in zone_set])

    # This is for "instances" listing
    self.ExpectListerInvoke(
        scope_set=zone_set,
        filter_expr=frontend.filter,
        max_results=frontend.max_results,
        result=[1, 2, 3])

    result = list(zonal_lister(frontend))
    self.assertListEqual(result, [1, 2, 3])

if __name__ == '__main__':
  test_case.main()
