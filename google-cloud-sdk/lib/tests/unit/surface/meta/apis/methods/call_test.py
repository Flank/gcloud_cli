# -*- coding: utf-8 -*- #
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

"""Tests of the 'gcloud meta apis methods describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import  properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib.command_lib.util.apis import base


class DescribeTests(base.Base, cli_test_base.CliTestBase,
                    sdk_test_base.WithFakeAuth):

  def SetUp(self):
    client = apis.GetClientClass('compute', 'v1')
    self.mocked_client = mock.Client(client)
    self.messages = client.MESSAGES_MODULE
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.mocked_client.instances.Get.Expect(
        self.messages.ComputeInstancesGetRequest(
            instance='testinstance',
            zone='zone1',
            project='foo',
        ),
        response={})

  def testDescribe(self):
    self.Run('meta apis methods call --collection=compute.instances get '
             'testinstance:zone1:foo')

  def testDescribeProjectProperty(self):
    properties.VALUES.core.project.Set('foo')
    self.Run('meta apis methods call --collection=compute.instances get '
             'testinstance:zone1')

  def testDescribeProjectPropertyOverride(self):
    properties.VALUES.core.project.Set('bar')
    self.Run('meta apis methods call --collection=compute.instances get '
             'testinstance:zone1:foo')

  def testDescribeUsingParams(self):
    self.Run('meta apis methods call --collection=compute.instances get '
             'testinstance --zone=zone1 --project=foo')

  def testDescribeParamOverride(self):
    self.Run('meta apis methods call --collection=compute.instances get '
             'testinstance:zone1:foo --zone=zone2 --project=bar')


class ListTests(base.Base, cli_test_base.CliTestBase,
                sdk_test_base.WithFakeAuth):

  def SetUp(self):
    client = apis.GetClientClass('compute', 'v1')
    self.mocked_client = mock.Client(client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    response = client.MESSAGES_MODULE.InstanceList(
        id='projcets/foo/zones/zone1/instances',
        items=[client.MESSAGES_MODULE.Instance(name='instance-1'),
               client.MESSAGES_MODULE.Instance(name='instance-2')]
    )
    self.mocked_client.instances.List.Expect(
        client.MESSAGES_MODULE.ComputeInstancesListRequest(
            zone='zone1',
            project='foo',
            pageToken=None,
        ),
        response=response)

  def testRawList(self):
    response = self.Run(
        'meta apis methods call --raw --collection=compute.instances list '
        'zone1:foo')
    self.assertEqual(len(response.items), 2)
    self.assertEqual(response.items[0].name, 'instance-1')
    self.assertEqual(response.items[1].name, 'instance-2')

  def testRawListWithFlags(self):
    response = self.Run(
        'meta apis methods call --raw --collection=compute.instances list '
        'zone1 --project=foo')
    self.assertEqual(len(response.items), 2)
    self.assertEqual(response.items[0].name, 'instance-1')
    self.assertEqual(response.items[1].name, 'instance-2')

  def testFlatList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = list(self.Run(
        'meta apis methods call --collection=compute.instances list '
        'zone1:foo'))
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0].name, 'instance-1')
    self.assertEqual(response[1].name, 'instance-2')

  def testFlatListWithFlags(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = list(self.Run(
        'meta apis methods call --collection=compute.instances list '
        'zone1 --project=foo'))
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0].name, 'instance-1')
    self.assertEqual(response[1].name, 'instance-2')


class NonPageableListTests(base.Base, cli_test_base.CliTestBase,
                           sdk_test_base.WithFakeAuth):

  def SetUp(self):
    client = apis.GetClientClass('container', 'v1')
    self.mocked_client = mock.Client(client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    response = client.MESSAGES_MODULE.ListClustersResponse(
        clusters=[client.MESSAGES_MODULE.Cluster(name='c-1'),
                  client.MESSAGES_MODULE.Cluster(name='c-2')]
    )
    self.mocked_client.projects_locations_clusters.List.Expect(
        client.MESSAGES_MODULE.ContainerProjectsLocationsClustersListRequest(
            parent='projects/foo/locations/zone1'),
        response=response)

  def testRawListNonPageable(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = self.Run('meta apis methods call --raw '
                        '--collection=container.projects.locations.clusters '
                        'list zone1:foo')
    self.assertEqual(len(response.clusters), 2)
    self.assertEqual(response.clusters[0].name, 'c-1')
    self.assertEqual(response.clusters[1].name, 'c-2')

  def testFlatListNonPageable(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = list(
        self.Run('meta apis methods call '
                 '--collection=container.projects.locations.clusters '
                 'list zone1:foo'))
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0].name, 'c-1')
    self.assertEqual(response[1].name, 'c-2')


class PageableNoPageSizeListTests(base.Base, cli_test_base.CliTestBase,
                                  sdk_test_base.WithFakeAuth):

  def SetUp(self):
    client = apis.GetClientClass('bigtableadmin', 'v2')
    self.mocked_client = mock.Client(client)
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    response = client.MESSAGES_MODULE.ListInstancesResponse(
        instances=[client.MESSAGES_MODULE.Instance(name='instance-1'),
                   client.MESSAGES_MODULE.Instance(name='instance-2')]
    )
    self.mocked_client.projects_instances.List.Expect(
        client.MESSAGES_MODULE.BigtableadminProjectsInstancesListRequest(
            parent='foo',
            pageToken=None,
        ),
        response=response)

  def testRawList(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = self.Run(
        'meta apis methods call --raw '
        '--collection=bigtableadmin.projects.instances '
        'list --parent=foo')
    self.assertEqual(len(response.instances), 2)
    self.assertEqual(response.instances[0].name, 'instance-1')
    self.assertEqual(response.instances[1].name, 'instance-2')

  def testFlatListNonPageable(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    response = list(self.Run(
        'meta apis methods call '
        '--collection=bigtableadmin.projects.instances '
        'list --parent=foo'))
    self.assertEqual(len(response), 2)
    self.assertEqual(response[0].name, 'instance-1')
    self.assertEqual(response[1].name, 'instance-2')


class InsertTests(base.Base, cli_test_base.CliTestBase,
                  sdk_test_base.WithFakeAuth):

  def SetUp(self):
    client = apis.GetClientClass('compute', 'v1')
    self.mocked_client = mock.Client(client)
    self.messages = client.MESSAGES_MODULE
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)
    self.mocked_client.instances.Insert.Expect(
        self.messages.ComputeInstancesInsertRequest(
            instance=self.messages.Instance(
                name='testinstance',
                networkInterfaces=[self.messages.NetworkInterface(
                    network='network',
                )],
            ),
            zone='zone1',
            project='foo'
        ),
        response={}
    )

  def testInsert(self):
    self.Run(
        'meta apis methods call --collection=compute.instances insert '
        'zone1:foo '
        '--instance.name=testinstance '
        '--instance.networkInterfaces.network=network')


class HelpTests(base.Base, cli_test_base.CliTestBase):

  def testHelp(self):
    with self.assertRaises(SystemExit):
      self.Run('meta apis methods call --help')
    self.AssertOutputContains('gcloud meta apis methods call METHOD ')

  def testHelpFlags(self):
    # TODO(b/38000796): Write some better tests once this prototype settles
    # down. Right now this just ensures it doesn't crash.
    with self.assertRaises(SystemExit):
      self.Run('meta apis methods call --collection=compute.addresses insert '
               '--help')

  def testMockHelp(self):
    # TODO(b/38000796): Write some better tests once this prototype settles
    # down. Right now this just ensures it doesn't crash.
    self.MockGetListCreateMethods(('foo.projects.clusters', False))
    with self.assertRaises(SystemExit):
      self.Run('meta apis methods call --collection foo.projects.clusters get '
               '--help')


class CompletionTests(base.Base, cli_test_base.CliTestBase):

  def testCollectionCompletion(self):
    self.MockCollections(('foo.projects.clusters', False),
                         ('foo.projects.clusters.instances', True))
    self.RunCompletion(
        'meta apis methods call --collection foo.projects.',
        ['foo.projects.clusters', 'foo.projects.clusters.instances'])

  def testMethodCompletion(self):
    self.MockGetListCreateMethods(('foo.projects.clusters', False))
    self.RunCompletion(
        'meta apis methods call --collection foo.projects.clusters ',
        ['get', 'list', 'create'])
    self.RunCompletion(
        'meta apis methods call --collection foo.projects.clusters g', ['get'])
    self.RunCompletion(
        'meta apis methods call --collection foo.projects.clusters f', [''])

    self.RunCompletion(
        'meta apis methods call --collection foo.projects.clusters get '
        '--clusters', ['--clustersId'])
    self.RunCompletion(
        'meta apis methods call --collection foo.projects.clusters list '
        '--page-s', ['--page-size'])


if __name__ == '__main__':
  cli_test_base.main()
