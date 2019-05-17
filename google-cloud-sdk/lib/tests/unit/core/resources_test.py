# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for the resources module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case
from googlecloudsdk.third_party.apis import apis_map

from six.moves import urllib


compute_v1 = core_apis.GetMessagesModule('compute', 'v1')
compute_beta = core_apis.GetMessagesModule('compute', 'beta')
dataflow_v1b3 = core_apis.GetMessagesModule('dataflow', 'v1b3')
storage_v1 = core_apis.GetMessagesModule('storage', 'v1')


_ALTENATE_COMPUTE_URL = 'http://localhost:3990/compute/beta/'


class AlternateAPIHostTest(sdk_test_base.SdkBase):

  def testParseLocalURL(self):
    registry = resources.Registry()
    registry.RegisterApiByName('compute', 'beta')
    instance_url = _ALTENATE_COMPUTE_URL + 'projects/p/zones/z/instances/i'
    instance_ref = registry.Parse(instance_url, {})
    self.assertEqual(instance_url, instance_ref.SelfLink())
    self.assertEqual('compute.instances', instance_ref.Collection())

  def testParseURLContainingNameWithSlash(self):
    registry = resources.Registry()
    registry.RegisterApiByName('compute', 'beta')

    image_url = _ALTENATE_COMPUTE_URL + 'projects/p/global/images/family/f'
    image_ref = registry.Parse(image_url, {})
    self.assertEqual(image_url, image_ref.SelfLink())
    self.assertEqual('compute.images', image_ref.Collection())
    self.assertEqual('family/f', image_ref.Name())
    self.assertEqual('projects/p/global/images/family/f',
                     image_ref.RelativeName())

  def testParseLocalCollection(self):
    registry = resources.Registry()
    registry.RegisterApiByName('compute', 'beta')

    properties.VALUES.api_endpoint_overrides.compute.Set(_ALTENATE_COMPUTE_URL)

    zone_ref = registry.Parse('z',
                              params={'project': lambda: 'p'},
                              collection='compute.zones')
    self.assertEqual(_ALTENATE_COMPUTE_URL + 'projects/p/zones/z',
                     zone_ref.SelfLink())
    self.assertEqual('compute.zones', zone_ref.Collection())

  def testParseUrl_OverriddenEndpoint_NotPreregistered(self):
    url = 'http://localhost:3990/projects/p/zones/z'
    properties.VALUES.api_endpoint_overrides.compute.Set(
        'http://localhost:3990/')
    registry = resources.Registry()
    registry.RegisterApiByName('compute', 'beta')
    ref = registry.Parse(url)
    self.assertEqual(url, ref.SelfLink())
    self.assertEqual('compute.zones', ref.Collection())
    self.assertEqual('compute', ref.GetCollectionInfo().api_name)
    self.assertEqual('beta', ref.GetCollectionInfo().api_version)

  def testDifferentEndpoint_CanParseExistingApi(self):
    urls = [
        'https://www.googleapis.com/compute/v1/projects/p/zones/z/instances/i',
        _ALTENATE_COMPUTE_URL +'projects/p/zones/z/instances/i',
    ]
    registry = resources.Registry()
    for url in urls:
      ref = registry.Parse(url)
      self.assertEqual(url, ref.SelfLink())

  def testOverrideShouldHaveVersion2(self):
    properties.VALUES.api_endpoint_overrides.container.Set(
        'https://container-test.sandbox.googleapis.com/')

    registry = resources.Registry()
    registry.RegisterApiByName('container', 'v1alpha1')

    ref = registry.Parse('zone1', params={'projectId': 'xyz'},
                         collection='container.projects.zones')
    self.assertEqual(
        'https://container-test.sandbox.googleapis.com/v1alpha1/projects/xyz'
        '/zones/zone1', ref.SelfLink())

  def testCloneAndSwitchWithEndpointOverrride(self):
    urls = [
        # staging endpoint
        'https://www-googleapis-staging.sandbox.google.com/compute/v1/',
        # test endpoint
        'https://www-googleapis-test.sandbox.google.com/compute/v1/',
        # local endpoint. Url contains name and version in url path.
        'http://localhost:8787/compute/v1/',
        # local esf endpoint. Url contains neither version nor api_name.
        'http://localhost:8787/',
    ]
    registry = resources.Registry()
    # For added risk use different version than endpoint.
    registry.RegisterApiByName('compute', 'beta')
    for url in urls:
      properties.VALUES.api_endpoint_overrides.compute.Set(url)
      ref = registry.Parse(
          'dt1',
          collection='compute.diskTypes',
          params={'project': 'p', 'zone': 'z'})
      self.assertEqual(ref.SelfLink(), url + 'projects/p/zones/z/diskTypes/dt1')


class ResourcePathingTest(sdk_test_base.SdkBase):

  TC1_URL = ('https://www.googleapis.com/compute/v1/'
             'projects/fake-project%3Afake/'
             'zones/us-central1-a/'
             'instances/tc1')
  TC1_URL_CLEAN = ('https://www.googleapis.com/compute/v1/'
                   'projects/fake-project:fake/'
                   'zones/us-central1-a/'
                   'instances/tc1')
  TC1_URL_BETA = ('https://www.googleapis.com/compute/beta/'
                  'projects/fake-project%3Afake/'
                  'zones/us-central1-a/'
                  'instances/tc1')
  TC1_URL_BETA_CLEAN = ('https://www.googleapis.com/compute/beta/'
                        'projects/fake-project:fake/'
                        'zones/us-central1-a/'
                        'instances/tc1')

  BAD_URL = ('https://www.googleapis.com/compute/v1/'
             'project/proj/'
             'zone/zone/'
             'instance/inst')
  SHORT_URL = ('https://www.googleapis.com/compute/v1/projects')

  def Project(self):
    return 'fake-project:fake'

  def SetUp(self):
    self.registry = resources.Registry()
    self.StartObjectPatch(apis_map, 'MAP', {})
    core_apis.AddToApisMap('bigtableclusteradmin', 'v1', True)
    core_apis.AddToApisMap('compute', 'v1', True)
    core_apis.AddToApisMap('compute', 'beta', False)
    core_apis.AddToApisMap('compute', 'alpha', False)
    core_apis.AddToApisMap('container', 'v1')
    core_apis.AddToApisMap('dataflow', 'v1b3', True)
    core_apis.AddToApisMap('dataproc', 'v1', True)
    core_apis.AddToApisMap('sqladmin', 'v1beta3', True)
    core_apis.AddToApisMap('sqladmin', 'v1beta4', False)
    core_apis.AddToApisMap('storage', 'v1', True)

  def testStorageGsUri(self):
    ref = self.registry.Parse(
        'gs://my_bucket/my_folder/my_file.txt')
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/'
        'my_bucket/o/my_folder/my_file.txt', ref.SelfLink())
    self.assertEqual('my_bucket', ref.bucket)
    self.assertEqual('my_folder/my_file.txt', ref.object)
    self.assertEqual('my_folder/my_file.txt', ref.Name())
    self.assertEqual('b/my_bucket/o/my_folder/my_file.txt', ref.RelativeName())
    self.assertEqual(
        {'bucket': 'my_bucket', 'object': 'my_folder/my_file.txt'},
        ref.AsDict())
    self.assertEqual(
        ['my_bucket', 'my_folder/my_file.txt'],
        ref.AsList())

  def testStorageOnlyParams(self):
    ref = self.registry.Create(
        'storage.objects',
        bucket='my_bucket',
        object='my_folder/my_file.txt',
    )
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/'
        'my_bucket/o/my_folder/my_file.txt', ref.SelfLink())
    self.assertEqual('my_bucket', ref.bucket)
    self.assertEqual('my_folder/my_file.txt', ref.object)
    self.assertEqual('my_folder/my_file.txt', ref.Name())
    self.assertEqual('b/my_bucket/o/my_folder/my_file.txt', ref.RelativeName())
    self.assertEqual(
        {'bucket': 'my_bucket', 'object': 'my_folder/my_file.txt'},
        ref.AsDict())
    self.assertEqual(
        ['my_bucket', 'my_folder/my_file.txt'],
        ref.AsList())

  def testMultilineName(self):
    ref = self.registry.Parse('First\nSecond', collection='storage.buckets')
    self.assertEqual('First\nSecond', ref.Name())

  def testWithTabName(self):
    ref = self.registry.Parse('First\tSecond', collection='storage.buckets')
    self.assertEqual('First\tSecond', ref.Name())

  def testWithSpaceInName(self):
    ref = self.registry.Parse('First Second', collection='storage.buckets')
    self.assertEqual('First Second', ref.Name())

  def testEmpty(self):
    with self.assertRaisesRegex(resources.InvalidResourceException,
                                r'could not parse resource \[\]'):
      self.registry.Parse('', collection='storage.buckets')

  def testImmutable(self):
    ref = self.registry.Parse('large', collection='storage.buckets')

    with self.assertRaises(NotImplementedError):
      ref.bucket = 'small'

    with self.assertRaises(NotImplementedError):
      del ref.bucket

  def testStorageGsUriWithCollection(self):
    # Collection should make no difference.
    ref = self.registry.Parse(
        'gs://my_bucket/my_folder/my_file.txt',
        collection='storage.objects')
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/'
        'my_bucket/o/my_folder/my_file.txt', ref.SelfLink())

  def testStorageJustBucket(self):
    ref = self.registry.Parse('gs://my_bucket')
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/my_bucket', ref.SelfLink())
    self.assertEqual('my_bucket', ref.bucket)
    self.assertEqual('my_bucket', ref.Name())
    self.assertEqual('b/my_bucket', ref.RelativeName())
    self.assertEqual({'bucket': 'my_bucket'}, ref.AsDict())
    self.assertEqual(['my_bucket'], ref.AsList())

  def testStorageUri(self):
    ref = self.registry.Parse(
        'https://www.googleapis.com/storage/v1'
        '/b/my_bucket/o/my_folder/my_file.txt')
    self.assertEqual('storage.objects', ref.Collection())
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/'
        'my_bucket/o/my_folder/my_file.txt', ref.SelfLink())

  def testStorageAlternativeUri_Fails(self):
    # Note that this url has no api version.
    url = 'https://storage.googleapis.com/my_bucket/my_folder/my_file.txt'
    with self.assertRaisesRegex(
        resources.InvalidResourceException,
        r'could not parse resource \[{0}\]: '
        r'unknown api version None'.format(url)):
      self.registry.ParseURL(url)

  def testStorageAlternativeUri(self):
    ref = self.registry.Parse(
        'https://storage.googleapis.com'
        '/my_bucket/my_folder/my_file.txt')
    self.assertEqual('storage.objects', ref.Collection())
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/'
        'my_bucket/o/my_folder/my_file.txt', ref.SelfLink())

  def testStorageBucketUri(self):
    ref = self.registry.Parse(
        'https://www.googleapis.com/storage/v1/b/my_bucket')
    self.assertEqual('storage.buckets', ref.Collection())
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/my_bucket', ref.SelfLink())

  def testStorageBucketPath(self):
    ref = self.registry.Parse('my_bucket', collection='storage.buckets')
    self.assertEqual('storage.buckets', ref.Collection())
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/my_bucket', ref.SelfLink())

  def testStorageBucketPath_MockedClient(self):
    with api_mock.Client(core_apis.GetClientClass('storage', 'v1')) as client:
      self.assertEqual('https://www.googleapis.com/storage/v1/', client.url)
      self.registry.RegisterApiByName('storage', 'v1')

      ref = self.registry.Parse('my_bucket', collection='storage.buckets')
      self.assertEqual('storage.buckets', ref.Collection())
      self.assertEqual(
          'https://www.googleapis.com/storage/v1/b/my_bucket', ref.SelfLink())

  def testStorageAlternativeBucketUri(self):
    ref = self.registry.Parse(
        'https://storage.googleapis.com/my_bucket')
    self.assertEqual('storage.buckets', ref.Collection())
    self.assertEqual(
        'https://www.googleapis.com/storage/v1/b/my_bucket', ref.SelfLink())

  def testStorageBadUri(self):
    with self.assertRaisesRegex(resources.InvalidResourceException,
                                r'could not parse resource \['
                                r'https://www.googleapis.com/storage/v1/'
                                r'bucket/my_bucket/o/my_folder/my_file.txt\]: '
                                r'Could not parse at \[bucket\]'):
      self.registry.Parse(
          'https://www.googleapis.com/storage/v1'
          '/bucket/my_bucket/o/my_folder/my_file.txt')

  def testStorageBadUriShort(self):
    with self.assertRaisesRegex(resources.InvalidResourceException,
                                r'could not parse resource \['
                                r'https://www.googleapis.com/storage/v1/'
                                r'foo\]: Could not parse at \[foo\]'):
      self.registry.Parse(
          'https://www.googleapis.com/storage/v1'
          '/foo')

  def testUnknownAPI(self):
    # The api is nonsense.
    with self.assertRaises(apis_util.UnknownAPIError):
      self.registry.Parse(
          'project/zone/instance', {}, collection='notquitecompute.instances')

  def assertIsTC1(self, resource):
    self.assertEqual(resource.SelfLink(), ResourcePathingTest.TC1_URL_CLEAN)
    self.assertEqual(resource.project, self.Project())
    self.assertEqual(resource.zone, 'us-central1-a')
    self.assertEqual(resource.instance, 'tc1')
    self.assertEqual(resource.Name(), 'tc1')
    self.assertEqual('projects/fake-project:fake/'
                     'zones/us-central1-a/instances/tc1',
                     resource.RelativeName())
    self.assertEqual(
        {'project': 'fake-project:fake',
         'zone': 'us-central1-a',
         'instance': 'tc1'}, resource.AsDict())
    self.assertEqual(
        ['fake-project:fake',
         'us-central1-a',
         'tc1'], resource.AsList())

  def assertIsTC1Beta(self, resource):
    self.assertEqual(
        resource.SelfLink(), ResourcePathingTest.TC1_URL_BETA_CLEAN)
    self.assertEqual(resource.project, self.Project())
    self.assertEqual(resource.zone, 'us-central1-a')
    self.assertEqual(resource.instance, 'tc1')
    self.assertEqual(resource.Name(), 'tc1')
    self.assertEqual('projects/fake-project:fake/zones/us-central1-a/'
                     'instances/tc1', resource.RelativeName())

  def testParamFuncs(self):
    # pylint: disable=unnecessary-lambda
    self.assertIsTC1(self.registry.Parse(
        'tc1',
        params={'project': (lambda: self.Project()),
                'zone': (lambda: 'us-central1-a')},
        collection='compute.instances'))
    self.assertIsTC1(self.registry.Parse(
        'tc1',
        params={'project': self.Project(),
                'zone': (lambda: 'us-central1-a')},
        collection='compute.instances'))

  def testDefaultResolverNoParams(self):
    defaults = {
        'project': self.Project(),
        'zone': 'us-central1-a',
    }

    def _DefaultResolver(param):
      return defaults.get(param)

    self.assertIsTC1(self.registry.Parse(
        'tc1',
        default_resolver=_DefaultResolver,
        collection='compute.instances'))

  def testDefaultResolverCoveredByParams(self):
    defaults = {
        'project': 'ignored-project',
        'zone': 'ignored-zone',
    }
    params = {
        'project': self.Project(),
        'zone': 'us-central1-a',
    }

    def _DefaultResolver(param):
      return defaults.get(param)

    self.assertIsTC1(self.registry.Parse(
        'tc1',
        default_resolver=_DefaultResolver,
        collection='compute.instances',
        params=params))

  def testDefaultResolverMixedWithParams(self):
    defaults = {
        'project': self.Project(),
    }
    params = {
        'zone': 'us-central1-a',
    }

    def _DefaultResolver(param):
      return defaults.get(param)

    self.assertIsTC1(self.registry.Parse(
        'tc1',
        default_resolver=_DefaultResolver,
        collection='compute.instances',
        params=params))

  def testExtraParam(self):
    with self.assertRaisesRegex(
        ValueError,
        r"Provided params \[u?'project', u?'region', u?'zone'\] is not subset "
        r"of the resource parameters \[u?'instance', u?'project', .?'zone'\]"):
      self.registry.Parse(
          'tc1',
          params={
              'project': self.Project(),
              'zone': 'us-central1-a',
              'region': 'us-central1',
          },
          collection='compute.instances')

  def testMisspelledParam(self):
    with self.assertRaisesRegex(
        ValueError,
        r"Provided params \[u?'projectsId', u?'zone'\] is not subset of the "
        r"resource parameters \[u?'instance', u?'project', u?'zone'\]"):
      self.registry.Parse(
          'tc1',
          params={
              'projectsId': self.Project(),
              'zone': 'us-central1-a',
          },
          collection='compute.instances')

  def testParseURL(self):
    self.assertIsTC1(
        self.registry.Parse(ResourcePathingTest.TC1_URL, {}))
    self.assertIsTC1(
        self.registry.Parse(ResourcePathingTest.TC1_URL_CLEAN, {}))
    self.assertIsTC1Beta(
        self.registry.Parse(ResourcePathingTest.TC1_URL_BETA, {}))

    # The URL has typos that make it not point to a valid resource.
    with self.assertRaisesRegex(
        resources.InvalidResourceException,
        r'could not parse resource \[{}\]: Could not parse at \[project\]'
        .format(ResourcePathingTest.BAD_URL)):
      self.registry.Parse(ResourcePathingTest.BAD_URL, {})

    # The URL is the prefix of a valid resource, but does not indicate
    # a resource on its own.
    with self.assertRaisesRegex(
        resources.InvalidResourceException,
        r'could not parse resource \[{}\]: Url too short.'
        .format(ResourcePathingTest.SHORT_URL)):
      self.registry.Parse(ResourcePathingTest.SHORT_URL, {})

    # The provided URL is for an instance, but the constraint says disks.
    with self.assertRaisesRegex(
        resources.WrongResourceCollectionException,
        urllib.parse.unquote(ResourcePathingTest.TC1_URL)):
      self.registry.Parse(ResourcePathingTest.TC1_URL, {},
                          collection='compute.disks')

    # Only https:// is allowed for URLs.
    with self.assertRaisesRegex(
        resources.InvalidResourceException,
        r'could not parse resource \[http://something\]: unknown API host'):
      self.registry.Parse('http://something', {})

  def testParseURLWithDifferentCollection(self):
    # Confirm this collection gives us global resource.
    ref = self.registry.Parse('bs1', params={'project': self.Project()},
                              collection='compute.backendServices')
    self.assertEqual(
        'https://www.googleapis.com/compute/v1/projects/fake-project:fake/'
        'global/backendServices/bs1', ref.SelfLink())

    # Now parse regional URL even though collections dont match.
    name = ('https://www.googleapis.com/compute/alpha/'
            'projects/fake-project%3Afake/'
            'regions/us-central1/backendServices/bs1')
    ref = self.registry.Parse(name, collection='compute.backendServices',
                              enforce_collection=False)
    self.assertEqual(urllib.parse.unquote(name), ref.SelfLink())

    # Confirm that without enforce_collection set to False we get the error.
    with self.assertRaises(resources.WrongResourceCollectionException):
      self.registry.Parse(name, collection='compute.backendServices')

  def testParseUrl_DifferentResourcePathParamNames(self):
    api_name, api_version = 'dataproc', 'v1'
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    clusters_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.regions.clusters',
        path='projects/{projectId}/regions/{region}/clusters/{clusterName}',
        flat_paths={},
        params=['projectId', 'region', 'clusterName'])
    # This collection uses different param for projects.
    operations_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.regions.operations',
        path=('projects/{projectsId}/regions/{regionsId}/'
              'operations/{operationsId}'),
        flat_paths={},
        params=['projectsId', 'regionsId', 'operationsId'])
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]

    registry._RegisterCollection(operations_collection)
    registry._RegisterCollection(clusters_collection)
    ref = registry.Parse('{0}projects/p/regions/r/clusters/c'.format(base_url))
    self.assertEqual('p', ref.projectId)
    self.assertEqual('r', ref.region)
    self.assertEqual('c', ref.clusterName)
    ref = registry.Parse('{0}projects/p/regions/r/operations/o'
                         .format(base_url))
    self.assertEqual('p', ref.projectsId)
    self.assertEqual('r', ref.regionsId)
    self.assertEqual('o', ref.operationsId)

  def testWrongCollectionMessage(self):
    with self.assertRaisesRegex(
        resources.WrongResourceCollectionException,
        r'wrong collection: expected \[compute.disks\], got '
        r'\[compute.instances\], for path \[https://www.googleapis.com'
        r'/compute/v1/projects/{0}'
        r'/zones/us-central1-a/instances/tc1\]'.format(self.Project())):
      self.registry.Parse(ResourcePathingTest.TC1_URL_CLEAN, {},
                          collection='compute.disks')

  def testAmbiguousResourcePaths(self):
    api_name, api_version = 'bigtableclusteradmin', 'v1'
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    operations_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='operations',
        path='{+name}',
        flat_paths=[],
        params=['name'])
    clusters_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.zones.clusters',
        path='{+name}',
        flat_paths=[],
        params=['name'])
    registry._RegisterCollection(operations_collection)
    with self.assertRaises(resources.AmbiguousResourcePath):
      registry._RegisterCollection(clusters_collection)

  def testAmbiguousResourcePathsNoUriParsing(self):
    api_name, api_version = 'bigtableclusteradmin', 'v1'
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    operations_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='operations',
        path='{+name}',
        flat_paths=[],
        params=['name'])
    clusters_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.zones.clusters',
        path='{+name}',
        flat_paths=[],
        params=['name'],
        enable_uri_parsing=False)
    registry._RegisterCollection(operations_collection)
    # No exception here.
    registry._RegisterCollection(clusters_collection)

  def testCustomResourcePaths(self):
    api_name, api_version = 'bigtableclusteradmin', 'v1'
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    operations_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='operations',
        path='operations/{+name}',
        flat_paths={'': 'operations/{+operationId}'},
        params=['name'])
    clusters_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.zones.clusters',
        path='{+name}',
        flat_paths={
            '': 'projects/{projectId}/zones/{zoneId}/clusters/{clusterId}',
        },
        params=['name'])
    registry._RegisterCollection(operations_collection)
    registry._RegisterCollection(clusters_collection)
    expected_url = ('https://bigtableclusteradmin.googleapis.com/v1/'
                    'operations/opid-123')
    ref = registry.Parse('opid-123',
                         collection='bigtableclusteradmin.operations')
    self.assertEqual(expected_url, ref.SelfLink())
    ref_from_url = registry.Parse(expected_url)
    self.assertEqual(expected_url, ref_from_url.SelfLink())
    self.assertEqual('operations/opid-123', ref.RelativeName())
    self.assertEqual({'operationId': 'opid-123'}, ref.AsDict())
    self.assertEqual(['opid-123'], ref.AsList())

    expected_url = ('https://bigtableclusteradmin.googleapis.com/v1/'
                    'projects/fishing/zones/hudson/clusters/cluster-42')
    ref = registry.Parse(
        'cluster-42',
        params={'projectId': 'fishing', 'zoneId': 'hudson'},
        collection='bigtableclusteradmin.projects.zones.clusters')
    self.assertEqual(expected_url, ref.SelfLink())
    self.assertEqual('projects/fishing/zones/hudson/clusters/cluster-42',
                     ref.RelativeName())
    self.assertEqual(
        {'projectId': 'fishing', 'zoneId': 'hudson', 'clusterId': 'cluster-42'},
        ref.AsDict())
    self.assertEqual(
        ['fishing', 'hudson', 'cluster-42'], ref.AsList())
    ref_from_url = registry.Parse(expected_url)
    self.assertEqual(expected_url, ref_from_url.SelfLink())

  def testMultiplePathExpansions(self):
    api_name, api_version = 'dataproc', 'v1'
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    operation_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.operations',
        path='{+name}',
        flat_paths={
            'atomic': '{+name}',
            'full': 'projects/{projectId}/operations/{operation}',
        },
        params=['name'])
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]
    registry._RegisterCollection(operation_collection)

    ref = registry.Parse('{0}projects/p/operations/o'.format(base_url),
                         collection='dataproc.projects.operations.full')
    self.assertEqual('p', ref.projectId)
    self.assertEqual('o', ref.operation)

    ref = registry.Parse('operations-o',
                         collection='dataproc.projects.operations.atomic')
    self.assertEqual('operations-o', ref.name)

  def testUnknownCollection(self):
    # The collection is nonsense.
    with self.assertRaises(resources.InvalidCollectionException):
      self.registry.Parse(
          'project/zone/instance', {}, collection='compute.johninstances')

  def testWrongCollection(self):
    # The collection in the collectionpath does not match the parsing
    # constraint.
    with self.assertRaises(resources.WrongResourceCollectionException):
      self.registry.Parse(
          'https://www.googleapis.com/compute/v1/'
          'projects/p/zones/z/instances/i',
          {},
          collection='compute.disks')

  def testResolvers_TC1FromProperty(self):
    properties.VALUES.core.project.Set(self.Project())
    self.assertIsTC1(self.registry.Parse(
        'tc1',
        params={
            'project': properties.VALUES.core.project.GetOrFail,
            'zone': 'us-central1-a',
        },
        collection='compute.instances'))

  def testResolveMissingRequiredProperty(self):
    with self.assertRaises(properties.RequiredPropertyError):
      self.registry.Parse(
          'tc1',
          params={
              'zone': 'zone',
              'project': properties.VALUES.core.project.GetOrFail,
          },
          collection='compute.instances')

  def testUnresolvedBadResolver(self):
    with self.assertRaises(resources.RequiredFieldOmittedException):
      self.registry.Parse(
          'tc1',
          params={
              'project': 'p',
              'zone': (lambda: None),
          },
          collection='compute.instances')

  def testCloneAndSwitch(self):
    cloned_registry = self.registry.Clone()
    cloned_registry.RegisterApiByName('compute', 'beta')
    tc1beta = cloned_registry.Parse(
        'tc1',
        params={'project': self.Project(),
                'zone': 'us-central1-a'},
        collection='compute.instances')
    self.assertIsTC1Beta(tc1beta)
    # verify that the original registry still uses the original API.
    tc1 = self.registry.Parse(
        'tc1',
        params={'project': self.Project(),
                'zone': 'us-central1-a'},
        collection='compute.instances')
    self.assertIsTC1(tc1)

  def testCloneAndSwitchTwice(self):
    cloned_registry1 = self.registry.Clone()
    cloned_registry1.RegisterApiByName('sqladmin', 'v1beta3')
    cloned_registry2 = cloned_registry1.Clone()
    cloned_registry2.RegisterApiByName('sqladmin', 'v1beta3')

  def testCloneAndSwitch_ParseAsDifferentVersion(self):
    params = {'project': self.Project(), 'zone': 'us-central1-a'}
    tc1 = self.registry.Parse('tc1', params, collection='compute.instances')
    self.assertEqual(
        tc1.SelfLink(),
        'https://www.googleapis.com/compute/v1/projects/fake-project:fake/'
        'zones/us-central1-a/instances/tc1')
    cloned_registry = self.registry.Clone()
    cloned_registry.RegisterApiByName('compute', 'beta')
    tc1 = cloned_registry.Parse('tc1', params, collection='compute.instances')
    self.assertEqual(
        tc1.SelfLink(),
        'https://www.googleapis.com/compute/beta/projects/fake-project:fake/'
        'zones/us-central1-a/instances/tc1')

  def testCloneAndSwitch_ParseDifferentVersionUrl(self):
    cloned_registry = self.registry.Clone()
    cloned_registry.RegisterApiByName('compute', 'beta')
    tc1v1 = cloned_registry.Parse(
        'https://www.googleapis.com/compute/v1/'
        'projects/fake-project%3Afake/'
        'zones/us-central1-a/'
        'instances/tc1',
        collection='compute.instances')
    self.assertIsTC1(tc1v1)
    # verify that the original registry still uses the original API.
    tc1 = self.registry.Parse(
        'tc1',
        params={'project': self.Project(),
                'zone': 'us-central1-a'},
        collection='compute.instances')
    self.assertIsTC1(tc1)

  def testCloneAndSwitch_ParseAsOldVersionUrl(self):
    tcv1_url = ('https://www.googleapis.com/compute/v1/'
                'projects/fake-project%3Afake/'
                'zones/us-central1-a/'
                'instances/tc1')

    tc1v1 = self.registry.Parse(tcv1_url)
    self.assertIsTC1(tc1v1)

    cloned_registry = self.registry.Clone()
    cloned_registry.RegisterApiByName('compute', 'beta')
    tc2v1 = cloned_registry.Parse(tcv1_url)
    self.assertIsTC1(tc2v1)

  def testCloneAndSwitchSQL_ParseAsOldVersionUrl(self):
    # for sql api, package name (sqladmin) does not equal url api name (sql)
    url = ('https://www.googleapis.com/sql/v1beta3/projects/p/instances/i')

    ref = self.registry.Parse(url)
    self.assertEqual(url, ref.SelfLink())

    cloned_registry = self.registry.Clone()
    cloned_registry.RegisterApiByName('sql', 'v1beta4')
    ref = cloned_registry.Parse(url)
    self.assertEqual(url, ref.SelfLink())

    url4 = ('https://www.googleapis.com/sql/v1beta4/projects/p/instances/i')
    ref = cloned_registry.Parse(url4)
    self.assertEqual(url4, ref.SelfLink())

  def testAPIMethodOrder(self):
    base_url = 'https://www.googleapis.com/sql/v1beta3/'
    instances_collection = resource_util.CollectionInfo(
        'sql', 'v1beta3', base_url, 'https://cloud.google.com/docs',
        name='instances',
        path='projects/{project}/instances/{instance}',
        flat_paths=[],
        params=['project', 'instance'])
    operations_collection = resource_util.CollectionInfo(
        'sql', 'v1beta3', base_url, 'https://cloud.google.com/docs',
        name='operations',
        path='projects/{project}/instances/{instance}/operations/{operation}',
        flat_paths=[],
        params=['project', 'instance', 'operation'])

    reg1 = resources.Registry()
    reg1.registered_apis['sql'].append('v1beta3')

    reg1._RegisterCollection(instances_collection)
    reg1._RegisterCollection(operations_collection)
    # We only check that this .Parse() call doesn't raise an exception. The
    # bug whose regression is blocked by this test caused one of the services
    # to silently fail to register: only the first one registered would be
    # able to parse URLs.
    reg1.Parse('https://www.googleapis.com/sql/v1beta3/projects/p/instances/i')

    reg2 = resources.Registry()
    reg2.registered_apis['sql'].append('v1beta3')

    reg2._RegisterCollection(operations_collection)
    reg2._RegisterCollection(instances_collection)
    # Same URL, but the services are registered in the opposite order.
    reg2.Parse('https://www.googleapis.com/sql/v1beta3/projects/p/instances/i')

  def testNestedCollectionNames(self):
    registry = resources.Registry()
    registry.RegisterApiByName('dataflow', 'v1b3')

    job_url = 'https://dataflow.googleapis.com/v1b3/projects/p/jobs/j'

    ref = registry.Parse(job_url)  # this should not throw an exception
    self.assertEqual(ref.Collection(), 'dataflow.projects.jobs')
    self.assertEqual(ref.projectId, 'p')
    self.assertEqual(ref.jobId, 'j')

  def testSortable(self):
    ref1 = self.registry.Parse(
        'https://storage.googleapis.com/my_bucket/my_folder/my_file1.txt')
    ref2 = self.registry.Parse(
        'https://storage.googleapis.com/my_bucket/my_folder/my_file2.txt')
    self.assertEqual([ref1, ref2], sorted([ref2, ref1]))

  def testStr(self):
    uri = ('https://www.googleapis.com/storage/v1/'
           'b/my_bucket/o/my_folder/my_file.txt')
    ref = self.registry.Parse(uri)
    self.assertEqual(uri, str(ref))

  def testParseUri_LiteralOrParam(self):
    api_name, api_version = 'cloudfunctions', 'v1beta2'
    core_apis.AddToApisMap(api_name, api_version, default=False)
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    projects_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects',
        path='projects/{projectsId}',
        flat_paths={
            '': 'projects/{projectsId}',
        },
        params=['projectsId'])
    buckets_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.buckets',
        path='projects/_/buckets/{bucketId}',
        flat_paths={
            '': 'projects/_/buckets/{bucketId}',
        },
        params=['bucketId'])
    registry = resources.Registry()
    registry.registered_apis[api_name] = [api_version]
    registry._RegisterCollection(projects_collection)
    registry._RegisterCollection(buckets_collection)

    projects_uri = ('https://cloudfunctions.googleapis.com/v1beta2/'
                    'projects/my-projectsid-1')
    self.assertEqual(projects_uri, registry.Parse(projects_uri).SelfLink())

    buckets_uri = ('https://cloudfunctions.googleapis.com/v1beta2/'
                   'projects/_/buckets/my-bucket')
    self.assertEqual(buckets_uri, registry.Parse(buckets_uri).SelfLink())

  def testRepr(self):
    uri = ('https://www.googleapis.com/storage/v1/'
           'b/my_bucket/o/my_folder/my_file.txt')
    ref = self.registry.Parse(uri)
    self.assertEqual(uri, repr(ref))

  def testHash(self):
    uri1 = ('https://www.googleapis.com/storage/v1/'
            'b/my_bucket/o/my_folder/my_file.txt')
    uri2 = ('https://www.googleapis.com/storage/v1/'
            'b/my_bucket/o/my_folder/my_file2.txt')

    ref1 = self.registry.Parse(uri1)
    ref3 = self.registry.Parse(uri1)
    ref2 = self.registry.Parse(uri2)
    self.assertEqual(hash(ref1), hash(ref3))
    self.assertNotEqual(hash(ref1), hash(ref2))

  def testParentImplicit(self):
    # Atomic name style.
    ref = self.registry.Parse(
        'projects/p/locations/l/clusters/c',
        collection='container.projects.locations.clusters')
    parent = ref.Parent()
    self.assertEqual('projects/p/locations/l', parent.RelativeName())
    self.assertEqual('container.projects.locations', parent.Collection())

    # Legacy style.
    ref = self.registry.Parse('projects/p/zones/z/instances/i',
                              collection='compute.instances')
    parent = ref.Parent()
    self.assertEqual('projects/p/zones/z', parent.RelativeName())
    self.assertEqual('compute.zones', parent.Collection())

  def testParentImplicitErrors(self):
    junk_collection = resource_util.CollectionInfo(
        'compute', 'v1', 'https://www.googleapis.com/compute/v1/',
        'https://cloud.google.com/docs',
        name='junk',
        path='parentJunk/{parentJunkId}/junk/{junkId}',
        flat_paths={},
        params=['parentJunkId', 'junkId'])
    self.registry._RegisterCollection(junk_collection)
    ref = self.registry.Parse('parentJunk/p/junk/j', collection='compute.junk')
    with self.assertRaisesRegex(
        resources.ParentCollectionResolutionException,
        r'Could not resolve the parent collection of collection '
        r'\[compute.junk\]. No collections found with parameters '
        r'\[parentJunkId\]'):
      ref.Parent()

  def testParentExplicit(self):
    ref = self.registry.Parse('projects/p/zones/z/instances/i',
                              collection='compute.instances')

    parent = ref.Parent('compute.zones')
    self.assertEqual('projects/p/zones/z', parent.RelativeName())
    self.assertEqual('compute.zones', parent.Collection())

    with self.assertRaisesRegex(
        resources.ParentCollectionMismatchException,
        r'The parent collection \[compute.regions\] of collection '
        r'\[compute.instances\] does have have the expected parameters. '
        r'Expected \[project, zone\], found \[project, region\].'):
      ref.Parent('compute.regions')
    with self.assertRaisesRegex(
        resources.UnknownCollectionException,
        r'unknown collection for \[compute.foo\]'):
      ref.Parent('compute.foo')


class RelativePathTests(sdk_test_base.SdkBase):

  def SetUp(self):
    api_name, api_version = 'dataproc', 'v1'
    base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
    operation_collection = resource_util.CollectionInfo(
        api_name, api_version, base_url, 'https://cloud.google.com/docs',
        name='projects.operations',
        path='{+name}',
        flat_paths={
            'atomic': '{+name}',
            'full': 'projects/{projectId}/operations/{operation}',
        },
        params=['name'])
    self.registry = resources.Registry()
    self.registry.registered_apis[api_name] = [api_version]
    self.registry._RegisterCollection(operation_collection)

  def testAtomicName(self):
    ref = self.registry.ParseRelativeName(
        'projects/p/operations/o',
        collection='dataproc.projects.operations.atomic')
    self.assertEqual('projects/p/operations/o', ref.name)
    self.assertEqual({'name': 'projects/p/operations/o'}, ref.AsDict())
    self.assertEqual(['projects/p/operations/o'], ref.AsList())

    # Also able to use generic parse.
    ref = self.registry.Parse(
        'projects/p/operations/o',
        collection='dataproc.projects.operations.atomic')
    self.assertEqual('projects/p/operations/o', ref.name)

  def testAtomicNameInvalidApiVersion(self):
    with self.assertRaisesRegex(
        apis_util.UnknownVersionError,
        r'The \[dataproc] API does not have version \[v0] in the APIs map'):
      self.registry.ParseRelativeName(
          'projects/p/operations/o',
          collection='dataproc.projects.operations.atomic',
          api_version='v0')

    # Also able to use generic parse.
    with self.assertRaisesRegex(
        apis_util.UnknownVersionError,
        r'The \[dataproc] API does not have version \[v0] in the APIs map'):
      self.registry.Parse(
          'projects/p/operations/o',
          collection='dataproc.projects.operations.atomic',
          api_version='v0')

  def testFullName(self):
    ref = self.registry.ParseRelativeName(
        'projects/p/operations/o',
        collection='dataproc.projects.operations.full')
    self.assertEqual('p', ref.projectId)
    self.assertEqual('o', ref.operation)
    self.assertEqual({'operation': 'o', 'projectId': 'p'}, ref.AsDict())
    self.assertEqual(['p', 'o'], ref.AsList())

    # Also able to use generic parse.
    parsed_ref = self.registry.Parse(
        'projects/p/operations/o',
        collection='dataproc.projects.operations.full')
    self.assertEqual(ref, parsed_ref)

  def testFullName_WithSlash(self):
    ref = self.registry.ParseRelativeName(
        'projects/p/operations/o/fish',
        collection='dataproc.projects.operations.full')
    self.assertEqual('p', ref.projectId)
    self.assertEqual('o/fish', ref.operation)
    self.assertEqual({'operation': 'o/fish', 'projectId': 'p'}, ref.AsDict())
    self.assertEqual(['p', 'o/fish'], ref.AsList())

    # Also able to use generic parse.
    parsed_ref = self.registry.Parse(
        'projects/p/operations/o/fish',
        collection='dataproc.projects.operations.full')
    self.assertEqual(ref, parsed_ref)

  def testFullName_UrEscape(self):
    ref = self.registry.ParseRelativeName(
        'projects/p/operations/o%2Ffish',
        collection='dataproc.projects.operations.full',
        url_unescape=True)
    self.assertEqual('p', ref.projectId)
    self.assertEqual('o/fish', ref.operation)
    self.assertEqual('projects/p/operations/o%2Ffish',
                     ref.RelativeName(url_escape=True))
    self.assertEqual({'operation': 'o/fish', 'projectId': 'p'}, ref.AsDict())
    self.assertEqual(['p', 'o/fish'], ref.AsList())


class GRIParseTests(subtests.Base):

  def RunSubTest(self, gri, collection=None, validate=True):
    actual = resources.GRI.FromString(gri, collection=collection,
                                      validate=validate)
    return (actual.path_fields, actual.collection, actual.is_fully_qualified,
            str(actual))

  def testGoodParse(self):
    def T(gri, expected, collection=None, validate=True, append_gri=True):
      if append_gri:
        expected += (gri,)
      self.Run(expected, gri, collection=collection, validate=validate, depth=2)

    T(None, ([], None, False, ''), append_gri=False)
    T(None, ([], 'foo.bar', False, ''), collection='foo.bar', append_gri=False)
    T('', ([], None, False))
    T('', ([], 'foo.bar', False), collection='foo.bar')
    T('a', (['a'], None, False))
    T('a', (['a'], 'foo.bar', False), collection='foo.bar')
    T('a::foo.bar', (['a'], 'foo.bar', True))
    T('a::foo.bar', (['a'], 'foo.bar', True), collection='foo.bar')
    T('a{::foo.bar', (['a{'], 'foo.bar', True))
    T('a:b', (['a', 'b'], None, False))
    T('a:b::foo.bar', (['a', 'b'], 'foo.bar', True))
    T('a:b:c', (['a', 'b', 'c'], None, False))
    T('a{::}foo.bar', (['a::foo.bar'], None, False))
    T('a{{::}}foo.bar', (['a{::}foo.bar'], None, False))
    T('a:b:c::foo.bar', (['a', 'b', 'c'], 'foo.bar', True))
    T('instance:zone:proj::foo.bar', (['instance', 'zone', 'proj'], 'foo.bar',
                                      True))
    T('a{:}b:c::foo.bar', (['a:b', 'c'], 'foo.bar', True))
    T('a{{:}}b:c::foo.bar', (['a{:}b', 'c'], 'foo.bar', True))
    T('a{{:}b:c::foo.bar', (['a{:b', 'c'], 'foo.bar', True))
    T('a{:}}b:c::foo.bar', (['a:}b', 'c'], 'foo.bar', True))
    T('a{}b:c::foo.bar', (['a{}b', 'c'], 'foo.bar', True))
    T('a{b:c::foo.bar', (['a{b', 'c'], 'foo.bar', True))
    T('a}b:c::foo.bar', (['a}b', 'c'], 'foo.bar', True))
    T('a:}b:c::foo.bar', (['a', '}b', 'c'], 'foo.bar', True))
    T('a:{b:c::foo.bar', (['a', '{b', 'c'], 'foo.bar', True))
    T('a{:b:c::foo.bar', (['a{', 'b', 'c'], 'foo.bar', True))
    T('a}:b:c::foo.bar', (['a}', 'b', 'c'], 'foo.bar', True))
    T('a{::}b:c::foo.bar', (['a::b', 'c'], 'foo.bar', True))
    T('a{::}b:c{::}foo.bar', (['a::b', 'c::foo.bar'], None, False))
    T('a{:::}b:c::foo.bar', (['a:::b', 'c'], 'foo.bar', True))
    T('a{{:::}}b:c::foo.bar', (['a{:::}b', 'c'], 'foo.bar', True))
    T('a{:::}}b:c::foo.bar', (['a:::}b', 'c'], 'foo.bar', True))
    T('a{::::}b:c::foo.bar', (['a::::b', 'c'], 'foo.bar', True))
    T('a{{::::}}b:c::foo.bar', (['a{::::}b', 'c'], 'foo.bar', True))

  def testBadParse(self):
    def T(gri, exception, collection=None):
      self.Run(None, gri, depth=2, exception=exception, collection=collection)

    T(':', resources.InvalidGRIFormatException)
    T('::', resources.InvalidGRIFormatException)
    T(':::', resources.InvalidGRIFormatException)
    T('a:', resources.InvalidGRIFormatException)
    T('a::', resources.InvalidGRIFormatException)
    T('::a::', resources.InvalidGRIFormatException)
    T('::a', resources.InvalidGRIFormatException)
    T(':::a', resources.InvalidGRIFormatException)
    T('{::a', resources.InvalidGRIFormatException)
    T(':a', resources.InvalidGRIFormatException)
    T('a::b::foo.bar', resources.InvalidGRIFormatException)
    T('a::b::c::foo.bar', resources.InvalidGRIFormatException)
    T('::a::foo.bar', resources.InvalidGRIFormatException)
    T('a::foo.bar::', resources.InvalidGRIFormatException)
    T('a{::b::foo.bar', resources.InvalidGRIFormatException)
    T('a::}b::foo.bar', resources.InvalidGRIFormatException)

    T('::foo', resources.InvalidGRICollectionSyntaxException)
    T('a::foobar', resources.InvalidGRICollectionSyntaxException)
    T('a::}foo.bar', resources.InvalidGRICollectionSyntaxException)
    T('a::f/oo.bar', resources.InvalidGRICollectionSyntaxException)
    T('a', resources.InvalidGRICollectionSyntaxException, collection='foo/bar')

    T('::foo.bar', resources.InvalidGRIPathSyntaxException)
    T('::foo.bar', resources.InvalidGRIPathSyntaxException)
    T(':::foo.bar', resources.InvalidGRIPathSyntaxException)
    T('::::foo.bar', resources.InvalidGRIPathSyntaxException)
    T(':a::foo.bar', resources.InvalidGRIPathSyntaxException)

    T('a:b:c::foo.bar', resources.GRICollectionMismatchException,
      collection='bar.baz')

  def testNoValidateParse(self):
    def T(gri, expected=None, exception=None, collection=None,
          append_gri=False):
      if append_gri:
        expected += (gri,)
      self.Run(expected, gri, exception=exception, collection=collection,
               validate=False, depth=2)

    T(':', ([':'], None, False, '{:}'))
    T('::', (['::'], None, False, '{::}'))
    T(':::', ([':::'], None, False, '{:::}'))
    T('a:', (['a:'], None, False, 'a{:}'))
    T('a::', (['a::'], None, False, 'a{::}'))
    T('::a::', (['::a::'], None, False, '{::}a{::}'))
    T('::a', (['::a'], None, False, '{::}a'))
    T(':::a', ([':::a'], None, False, '{:::}a'))
    T('{::a', (['{'], 'a', True, '{::a'))
    T(':a', ([':a'], None, False, '{:}a'))
    T('a::b::foo.bar', exception=resources.InvalidGRIFormatException)
    T('a::b::c::foo.bar', exception=resources.InvalidGRIFormatException)
    T('::a::foo.bar', (['::a'], 'foo.bar', True, '{::}a::foo.bar'))
    T('a::foo.bar::', (['a'], 'foo.bar::', True, 'a::foo.bar::'))
    T('a{::b::foo.bar', exception=resources.InvalidGRIFormatException)
    T('a::}b::foo.bar', exception=resources.InvalidGRIFormatException)

    T('::foo', (['::foo'], None, False, '{::}foo'))
    T('a::foobar', (['a'], 'foobar', True, 'a::foobar'))
    T('a::}foo.bar', (['a'], '}foo.bar', True, 'a::}foo.bar'))
    T('a::f/oo.bar', (['a'], 'f/oo.bar', True, 'a::f/oo.bar'))
    T('a', (['a'], 'foo/bar', False, 'a'), collection='foo/bar')

    T('::foo.bar', (['::foo.bar'], None, False, '{::}foo.bar'))
    T('::foo.bar', (['::foo.bar'], None, False, '{::}foo.bar'))
    T(':::foo.bar', ([':::foo.bar'], None, False, '{:::}foo.bar'))
    T('::::foo.bar', (['::::foo.bar'], None, False, '{::::}foo.bar'))
    T(':a::foo.bar', ([':a'], 'foo.bar', True, '{:}a::foo.bar'))

    T('a:b:c::foo.bar', (['a', 'b', 'c'], 'bar.baz', True, 'a:b:c::bar.baz'),
      collection='bar.baz')


class GRIRegistryParseTests(subtests.Base):

  def RunSubTest(self, gri, params=None, collection=None):
    ref = self.registry.Parse(gri, params=params, collection=collection)
    return (ref.instance, ref.zone, ref.project, ref.Collection())

  def SetUp(self):
    properties.VALUES.core.enable_gri.Set(True)
    self.registry = resources.Registry()
    self.StartObjectPatch(apis_map, 'MAP', {})
    core_apis.AddToApisMap('compute', 'v1', True)
    core_apis.AddToApisMap('appengine', 'v1', True)

  def testGoodParse(self):
    def T(gri, params, collection, expected):
      self.Run(expected, gri, params=params, collection=collection, depth=2)

    T('i:z:p::compute.instances', {}, None,
      ('i', 'z', 'p', 'compute.instances'))
    T('i:z::compute.instances', {'project': 'p'}, None,
      ('i', 'z', 'p', 'compute.instances'))
    T('i::compute.instances', {'project': 'p', 'zone': 'z'}, None,
      ('i', 'z', 'p', 'compute.instances'))
    T(None, {'project': 'p', 'zone': 'z', 'instance': 'i'}, 'compute.instances',
      ('i', 'z', 'p', 'compute.instances'))
    T('i:other-zone::compute.instances', {'project': 'p', 'zone': 'z'}, None,
      ('i', 'other-zone', 'p', 'compute.instances'))
    T('i:other-zone:other-proj::compute.instances',
      {'project': 'p', 'zone': 'z'}, None,
      ('i', 'other-zone', 'other-proj', 'compute.instances'))
    T('i:z:p', {}, 'compute.instances',
      ('i', 'z', 'p', 'compute.instances'))

    # Check that we can parse collections with multiple segments.
    ref = self.registry.Parse('v:s:a::appengine.apps.services.versions')
    self.assertEqual(
        ('v', 's', 'a', 'appengine.apps.services.versions'),
        (ref.versionsId, ref.servicesId, ref.appsId, ref.Collection()))

  def testBadParse(self):
    with self.assertRaisesRegex(
        resources.UnknownCollectionException,
        r'unknown collection for \[i:z:p\]'):
      self.registry.Parse('i:z:p', params={}, collection=None)

    with self.assertRaisesRegex(
        resources.GRIPathMismatchException,
        r'It must match the format: \['
        r'instance:zone:project::compute.instances\]'):
      # Check that the error shows the full GRI because we gave a full GRI.
      self.registry.Parse('i:z:p:junk::compute.instances', params={},
                          collection=None)

    with self.assertRaisesRegex(
        resources.GRIPathMismatchException,
        r'It must match the format: \[instance:zone:project\]'):
      # Check that we only show the contextual GRI because we didn't provide
      # the collection.
      self.registry.Parse('i:z:p:junk', params={},
                          collection='compute.instances')


if __name__ == '__main__':
  test_case.main()
