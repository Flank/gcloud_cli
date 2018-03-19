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

"""Tests for the registry module."""

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import registry
from tests.lib import sdk_test_base
from tests.lib.command_lib.util.apis import base


class NonMockedTests(base.Base):
  """Some tests to make sure the registry actually works with our real APIs."""

  def testGetAllAPIs(self):
    all_apis = registry.GetAllAPIs()
    self.assertGreater(len(all_apis), 30)
    compute_apis = [a for a in all_apis if a.name == 'compute']
    self.assertGreater(len(compute_apis), 1)
    default_compute_apis = [a for a in compute_apis if a.is_default]
    self.assertEqual(1, len(default_compute_apis))

  def testGetAPI(self):
    a = registry.GetAPI('compute', 'v1')
    self.assertEqual('compute', a.name)
    self.assertEqual('v1', a.version)

    a = registry.GetAPI('compute')
    self.assertTrue(a.is_default)

    with self.assertRaises(registry.UnknownAPIError):
      registry.GetAPI('junk')
    with self.assertRaises(registry.UnknownAPIVersionError):
      registry.GetAPI('compute', 'junk')

  def testGetAPICollections(self):
    c = registry.GetAPICollections()
    self.assertGreater(len(c), 100)
    c = registry.GetAPICollections('compute')
    self.assertLess(len(c), 100)
    self.assertGreater(len(c), 10)
    c = registry.GetAPICollections('compute', 'v1')
    self.assertLess(len(c), 100)
    self.assertGreater(len(c), 10)

    with self.assertRaises(registry.UnknownAPIError):
      registry.GetAPICollections('junk')
    with self.assertRaises(registry.UnknownAPIVersionError):
      registry.GetAPICollections('compute', 'junk')

  def testGetAPICollection(self):
    # Flat path resource.
    c = registry.GetAPICollection('compute.instances', 'v1')
    self.assertEqual(c.api_name, 'compute')
    self.assertEqual(c.api_version, 'v1')
    self.assertEqual(c.name, 'instances')
    self.assertEqual(c.full_name, 'compute.instances')
    self.assertEqual(c.base_url, 'https://www.googleapis.com/compute/v1/')
    self.assertEqual(
        c.docs_url,
        'https://developers.google.com/compute/docs/reference/latest/')
    self.assertEqual(c.detailed_path,
                     'projects/{project}/zones/{zone}/instances/{instance}')
    self.assertEqual(c.detailed_params, ['project', 'zone', 'instance'])
    self.assertEqual(c.path,
                     'projects/{project}/zones/{zone}/instances/{instance}')
    self.assertEqual(c.params, ['project', 'zone', 'instance'])

    # Atomic name resource.
    c = registry.GetAPICollection('pubsub.projects.topics', 'v1')
    self.assertEqual(c.api_name, 'pubsub')
    self.assertEqual(c.api_version, 'v1')
    self.assertEqual(c.name, 'projects.topics')
    self.assertEqual(c.full_name, 'pubsub.projects.topics')
    self.assertEqual(c.base_url, 'https://pubsub.googleapis.com/v1/')
    self.assertEqual(c.docs_url, 'https://cloud.google.com/pubsub/docs')
    self.assertEqual(c.detailed_path,
                     'projects/{projectsId}/topics/{topicsId}')
    self.assertEqual(c.detailed_params, ['projectsId', 'topicsId'])
    self.assertEqual(c.path, '{+topic}')
    self.assertEqual(c.params, ['topic'])

    with self.assertRaises(registry.UnknownAPIError):
      registry.GetAPICollections('junk')
    with self.assertRaises(registry.UnknownCollectionError):
      registry.GetAPICollection('compute.junk')
    with self.assertRaises(registry.UnknownAPIVersionError):
      registry.GetAPICollection('compute.instances', 'junk')

  def testGetMethods(self):
    # Flat path resource
    c = registry.GetMethods('compute.instances')
    self.assertGreater(len(c), 10)
    c = registry.GetMethods('compute.instances', 'v1')
    self.assertGreater(len(c), 10)

    with self.assertRaises(registry.UnknownAPIError):
      registry.GetMethods('junk.foo')
    with self.assertRaises(registry.UnknownCollectionError):
      registry.GetMethods('compute.junk')
    with self.assertRaises(registry.UnknownAPIVersionError):
      registry.GetMethods('compute.instances', 'junk')

  def testGetMethodErrors(self):
    with self.assertRaises(registry.UnknownAPIError):
      registry.GetMethod('junk.foo', 'get')
    with self.assertRaises(registry.UnknownCollectionError):
      registry.GetMethod('compute.junk', 'get')
    with self.assertRaises(registry.UnknownMethodError):
      registry.GetMethod('compute.instances', 'junk')
    with self.assertRaises(registry.UnknownAPIVersionError):
      registry.GetMethod('compute.instances', 'get', 'junk')

  def testGetMethodGet(self):
    # Flat path resource.
    m = registry.GetMethod('compute.instances', 'get')
    self.assertEqual(m.collection.full_name, 'compute.instances')
    self.assertEqual(m.name, 'get')
    self.assertEqual(m.path,
                     'projects/{project}/zones/{zone}/instances/{instance}')
    self.assertEqual(m.params, ['project', 'zone', 'instance'])
    self.assertEqual(m.detailed_path,
                     'projects/{project}/zones/{zone}/instances/{instance}')
    self.assertEqual(m.detailed_params, ['project', 'zone', 'instance'])
    self.assertEqual(m.http_method, 'GET')
    self.assertEqual(m.request_field, '')
    self.assertEqual(m.request_type, 'ComputeInstancesGetRequest')
    self.assertEqual(m.response_type, 'Instance')

    client = apis.GetClientClass('compute', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(), messages.ComputeInstancesGetRequest)
    self.assertEqual(m.GetResponseType(), messages.Instance)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Instance)
    self.assertFalse(m.IsList())
    self.assertFalse(m.IsPageableList())
    self.assertIsNone(m.BatchPageSizeField())
    self.assertIsNone(m.ListItemField())
    self.assertEqual(m.request_collection, m.collection)
    self.assertEqual(m.resource_argument_collection.detailed_params,
                     ['project', 'zone', 'instance'])

    # Atomic name resource.
    m = registry.GetMethod('pubsub.projects.topics', 'get')
    self.assertEqual(m.collection.full_name, 'pubsub.projects.topics')
    self.assertEqual(m.name, 'get')
    self.assertEqual(m.path, '{+topic}')
    self.assertEqual(m.params, ['topic'])
    self.assertEqual(m.detailed_path, 'projects/{projectsId}/topics/{topicsId}')
    self.assertEqual(m.detailed_params, ['projectsId', 'topicsId'])
    self.assertEqual(m.http_method, 'GET')
    self.assertEqual(m.request_field, '')
    self.assertEqual(m.request_type, 'PubsubProjectsTopicsGetRequest')
    self.assertEqual(m.response_type, 'Topic')

    client = apis.GetClientClass('pubsub', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(),
                     messages.PubsubProjectsTopicsGetRequest)
    self.assertEqual(m.GetResponseType(), messages.Topic)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Topic)
    self.assertFalse(m.IsList())
    self.assertFalse(m.IsPageableList())
    self.assertIsNone(m.BatchPageSizeField())
    self.assertIsNone(m.ListItemField())
    self.assertEqual(m.request_collection, m.collection)
    self.assertEqual(m.resource_argument_collection, m.collection)
    self.assertEqual(m.resource_argument_collection.detailed_params,
                     ['projectsId', 'topicsId'])

  def testGetMethodList(self):
    # Flat path resource.
    m = registry.GetMethod('compute.instances', 'list')
    self.assertEqual(m.collection.full_name, 'compute.instances')
    self.assertEqual(m.name, 'list')
    self.assertEqual(m.path, 'projects/{project}/zones/{zone}/instances')
    self.assertEqual(m.params, ['project', 'zone'])
    self.assertEqual(m.detailed_path,
                     'projects/{project}/zones/{zone}/instances')
    self.assertEqual(m.detailed_params, ['project', 'zone'])
    self.assertEqual(m.http_method, 'GET')
    self.assertEqual(m.request_field, '')
    self.assertEqual(m.request_type, 'ComputeInstancesListRequest')
    self.assertEqual(m.response_type, 'InstanceList')

    client = apis.GetClientClass('compute', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(), messages.ComputeInstancesListRequest)
    self.assertEqual(m.GetResponseType(), messages.InstanceList)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Instance)
    self.assertTrue(m.IsList())
    self.assertTrue(m.IsPageableList())
    self.assertEqual(m.BatchPageSizeField(), 'maxResults')
    self.assertEqual(m.ListItemField(), 'items')
    self.assertEqual(m.request_collection.full_name, 'compute.zones')
    self.assertEqual(m.resource_argument_collection.full_name, 'compute.zones')
    self.assertEqual(
        m.resource_argument_collection.detailed_params, ['project', 'zone'])

    # Atomic name resource.
    m = registry.GetMethod('pubsub.projects.topics', 'list')
    self.assertEqual(m.collection.full_name, 'pubsub.projects.topics')
    self.assertEqual(m.name, 'list')
    self.assertEqual(m.path, '{+project}/topics')
    self.assertEqual(m.params, ['project'])
    self.assertEqual(m.detailed_path, 'projects/{projectsId}/topics')
    self.assertEqual(m.detailed_params, ['projectsId'])
    self.assertEqual(m.http_method, 'GET')
    self.assertEqual(m.request_field, '')
    self.assertEqual(m.request_type, 'PubsubProjectsTopicsListRequest')
    self.assertEqual(m.response_type, 'ListTopicsResponse')

    client = apis.GetClientClass('pubsub', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(),
                     messages.PubsubProjectsTopicsListRequest)
    self.assertEqual(m.GetResponseType(), messages.ListTopicsResponse)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Topic)
    self.assertTrue(m.IsList())
    self.assertTrue(m.IsPageableList())
    self.assertEqual(m.BatchPageSizeField(), 'pageSize')
    self.assertEqual(m.ListItemField(), 'topics')
    self.assertEqual(m.request_collection.full_name, 'pubsub.projects')
    self.assertEqual(
        m.resource_argument_collection.full_name, 'pubsub.projects')
    self.assertEqual(
        m.resource_argument_collection.detailed_params, ['projectsId'])

  def testGetMethodCreate(self):
    # Flat path resource.
    m = registry.GetMethod('compute.instances', 'insert')
    self.assertEqual(m.collection.full_name, 'compute.instances')
    self.assertEqual(m.name, 'insert')
    self.assertEqual(m.path, 'projects/{project}/zones/{zone}/instances')
    self.assertEqual(m.params, ['project', 'zone'])
    self.assertEqual(m.detailed_path,
                     'projects/{project}/zones/{zone}/instances')
    self.assertEqual(m.detailed_params, ['project', 'zone'])
    self.assertEqual(m.http_method, 'POST')
    self.assertEqual(m.request_field, 'instance')
    self.assertEqual(m.request_type, 'ComputeInstancesInsertRequest')
    self.assertEqual(m.response_type, 'Operation')

    client = apis.GetClientClass('compute', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(), messages.ComputeInstancesInsertRequest)
    self.assertEqual(m.GetResponseType(), messages.Operation)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Operation)
    self.assertFalse(m.IsList())
    self.assertFalse(m.IsPageableList())
    self.assertEqual(m.BatchPageSizeField(), None)
    self.assertEqual(m.ListItemField(), None)
    self.assertEqual(m.request_collection.full_name, 'compute.zones')
    self.assertEqual(m.resource_argument_collection.full_name,
                     'compute.instances')
    self.assertEqual(m.resource_argument_collection.detailed_params,
                     ['project', 'zone', 'instance'])

    # Atomic name resource.
    m = registry.GetMethod('cloudiot.projects.locations.registries', 'create')
    self.assertEqual(m.collection.full_name,
                     'cloudiot.projects.locations.registries')
    self.assertEqual(m.name, 'create')
    self.assertEqual(m.path, '{+parent}/registries')
    self.assertEqual(m.params, ['parent'])
    self.assertEqual(m.detailed_path,
                     'projects/{projectsId}/locations/{locationsId}/registries')
    self.assertEqual(m.detailed_params, ['projectsId', 'locationsId'])
    self.assertEqual(m.http_method, 'POST')
    self.assertEqual(m.request_field, 'deviceRegistry')
    self.assertEqual(m.request_type,
                     'CloudiotProjectsLocationsRegistriesCreateRequest')
    self.assertEqual(m.response_type, 'DeviceRegistry')

    client = apis.GetClientClass('cloudiot', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(),
                     messages.CloudiotProjectsLocationsRegistriesCreateRequest)
    self.assertEqual(m.GetResponseType(), messages.DeviceRegistry)
    self.assertEqual(m.GetEffectiveResponseType(), messages.DeviceRegistry)
    self.assertFalse(m.IsList())
    self.assertFalse(m.IsPageableList())
    self.assertEqual(m.BatchPageSizeField(), None)
    self.assertEqual(m.ListItemField(), None)
    self.assertEqual(m.request_collection.full_name,
                     'cloudiot.projects.locations')
    self.assertEqual(m.resource_argument_collection.full_name,
                     'cloudiot.projects.locations.registries')
    self.assertEqual(m.resource_argument_collection.detailed_params,
                     ['projectsId', 'locationsId', 'registriesId'])

    # Atomic name resource done differently for some reason.
    m = registry.GetMethod('pubsub.projects.topics', 'create')
    self.assertEqual(m.collection.full_name, 'pubsub.projects.topics')
    self.assertEqual(m.name, 'create')
    self.assertEqual(m.path, '{+name}')
    self.assertEqual(m.params, ['name'])
    self.assertEqual(m.detailed_path, 'projects/{projectsId}/topics/{topicsId}')
    self.assertEqual(m.detailed_params, ['projectsId', 'topicsId'])
    self.assertEqual(m.http_method, 'PUT')
    self.assertEqual(m.request_field, '<request>')
    self.assertEqual(m.request_type, 'Topic')
    self.assertEqual(m.response_type, 'Topic')

    client = apis.GetClientClass('pubsub', 'v1')
    messages = client.MESSAGES_MODULE
    self.assertEqual(m.GetRequestType(), messages.Topic)
    self.assertEqual(m.GetResponseType(), messages.Topic)
    self.assertEqual(m.GetEffectiveResponseType(), messages.Topic)
    self.assertFalse(m.IsList())
    self.assertFalse(m.IsPageableList())
    self.assertEqual(m.BatchPageSizeField(), None)
    self.assertEqual(m.ListItemField(), None)
    self.assertEqual(m.request_collection.full_name, 'pubsub.projects.topics')
    self.assertEqual(m.resource_argument_collection.full_name,
                     'pubsub.projects.topics')
    self.assertEqual(m.resource_argument_collection.detailed_params,
                     ['projectsId', 'topicsId'])


class CallTests(sdk_test_base.WithFakeAuth):

  def MockAPI(self, api, version):
    client = apis.GetClientClass(api, version)
    self.mocked_client = mock.Client(client)
    self.messages = client.MESSAGES_MODULE
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

  def testDescribe(self):
    self.MockAPI('compute', 'v1')
    request = self.messages.ComputeInstancesGetRequest(
        instance='testinstance', zone='zone1', project='foo')
    self.mocked_client.instances.Get.Expect(request, response={'foo': 'bar'})
    registry.GetMethod('compute.instances', 'get').Call(request)

  def testRawList(self):
    self.MockAPI('compute', 'v1')
    request = self.messages.ComputeInstancesListRequest(
        zone='zone1', project='foo', pageToken=None)
    response = self.messages.InstanceList(
        id='projcets/foo/zones/zone1/instances',
        items=[self.messages.Instance(name='instance-1'),
               self.messages.Instance(name='instance-2')])
    self.mocked_client.instances.List.Expect(request, response)
    actual = registry.GetMethod('compute.instances', 'list').Call(
        request, raw=True)
    self.assertEqual(len(actual.items), 2)
    self.assertEqual(actual.items[0].name, 'instance-1')
    self.assertEqual(actual.items[1].name, 'instance-2')

  def testFlatList(self):
    self.MockAPI('compute', 'v1')
    request = self.messages.ComputeInstancesListRequest(
        zone='zone1', project='foo', pageToken=None)
    response = self.messages.InstanceList(
        id='projcets/foo/zones/zone1/instances',
        items=[self.messages.Instance(name='instance-1'),
               self.messages.Instance(name='instance-2')])
    self.mocked_client.instances.List.Expect(request, response)
    actual = list(
        registry.GetMethod('compute.instances', 'list').Call(
            request, raw=False))
    self.assertEqual(len(actual), 2)
    self.assertEqual(actual[0].name, 'instance-1')
    self.assertEqual(actual[1].name, 'instance-2')

  def testRawListNonPageable(self):
    self.MockAPI('container', 'v1')
    request = self.messages.ContainerProjectsZonesClustersListRequest(
        zone='zone1', projectId='foo')
    response = self.messages.ListClustersResponse(
        clusters=[self.messages.Cluster(name='c-1'),
                  self.messages.Cluster(name='c-2')])
    self.mocked_client.projects_zones_clusters.List.Expect(request, response)
    actual = registry.GetMethod('container.projects.zones.clusters',
                                'list').Call(request, raw=True)
    self.assertEqual(len(actual.clusters), 2)
    self.assertEqual(actual.clusters[0].name, 'c-1')
    self.assertEqual(actual.clusters[1].name, 'c-2')

  def testFlatListNonPageable(self):
    self.MockAPI('container', 'v1')
    request = self.messages.ContainerProjectsZonesClustersListRequest(
        zone='zone1', projectId='foo')
    response = self.messages.ListClustersResponse(
        clusters=[self.messages.Cluster(name='c-1'),
                  self.messages.Cluster(name='c-2')])
    self.mocked_client.projects_zones_clusters.List.Expect(request, response)
    actual = list(
        registry.GetMethod('container.projects.zones.clusters', 'list').Call(
            request, raw=False))
    self.assertEqual(len(actual), 2)
    self.assertEqual(actual[0].name, 'c-1')
    self.assertEqual(actual[1].name, 'c-2')

  def testRawListNoPageSize(self):
    self.MockAPI('bigtableadmin', 'v2')
    request = self.messages.BigtableadminProjectsInstancesListRequest(
        parent='foo', pageToken=None)
    response = self.messages.ListInstancesResponse(
        instances=[self.messages.Instance(name='instance-1'),
                   self.messages.Instance(name='instance-2')])
    self.mocked_client.projects_instances.List.Expect(request, response)
    actual = registry.GetMethod('bigtableadmin.projects.instances',
                                'list').Call(request, raw=True)
    self.assertEqual(len(actual.instances), 2)
    self.assertEqual(actual.instances[0].name, 'instance-1')
    self.assertEqual(actual.instances[1].name, 'instance-2')

  def testFlatListNoPageSize(self):
    self.MockAPI('bigtableadmin', 'v2')
    request = self.messages.BigtableadminProjectsInstancesListRequest(
        parent='foo', pageToken=None)
    response = self.messages.ListInstancesResponse(
        instances=[self.messages.Instance(name='instance-1'),
                   self.messages.Instance(name='instance-2')])
    self.mocked_client.projects_instances.List.Expect(request, response)
    actual = list(
        registry.GetMethod('bigtableadmin.projects.instances', 'list').Call(
            request, raw=False))
    self.assertEqual(len(actual), 2)
    self.assertEqual(actual[0].name, 'instance-1')
    self.assertEqual(actual[1].name, 'instance-2')

  def testInsert(self):
    self.MockAPI('compute', 'v1')
    request = self.messages.ComputeInstancesInsertRequest(
        instance=self.messages.Instance(
            name='testinstance',
            networkInterfaces=[self.messages.NetworkInterface(
                network='network',
            )],
        ),
        zone='zone1',
        project='foo'
    )
    self.mocked_client.instances.Insert.Expect(request, {})
    self.assertEqual({}, registry.GetMethod('compute.instances', 'insert').Call(
        request))


if __name__ == '__main__':
  base.main()
