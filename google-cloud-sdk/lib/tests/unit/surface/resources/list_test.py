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

"""Test for the api_lit.util.resource_search module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import resource_search
from tests.lib.api_lib.util import resource_search_test_base


class ResourceSearchTest(resource_search_test_base.ResourceSearchTestBase):
  """Cloud Resource Search tests.

  uri=True is done client side, all of the other options are done server side.
  Except for limit the mocks don't emulate the server side options, so most of
  the tests ignore the return content. The List() metho return value is
  converted to a list because the API and mocked API return value is a
  generator and we need to commit the generator values for the tests to take
  effect.
  """

  def testComputeInstances(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(
            results=self.ResourceSearchResults(count=3),
        ),
    )
    self.Run('alpha resources list '
             '--format=table(name,zone.scope(zones),status)')
    self.AssertOutputContains("""\
NAME         ZONE         STATUS
test-name-0  test-zone-0  PROVISIONING
test-name-1  test-zone-1  PROVISIONING
test-name-2  test-zone-2  PROVISIONING
""")

  def testComputeInstancesUri(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(
            results=self.ResourceSearchResults(count=3),
        ),
    )
    self.Run('alpha resources list --uri')
    self.AssertOutputContains("""\
https://www.googleapis.com/compute/beta/projects/test-project-0/zones/test-zone-0/instances/test-name-0
https://www.googleapis.com/compute/beta/projects/test-project-1/zones/test-zone-1/instances/test-name-1
https://www.googleapis.com/compute/beta/projects/test-project-2/zones/test-zone-2/instances/test-name-2
""")

  def testComputeInstancesUriLimit(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=1,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(
            results=self.ResourceSearchResults(count=3),
        ),
    )
    self.Run('alpha resources list --limit=1 --uri')
    self.AssertOutputContains("""\
https://www.googleapis.com/compute/beta/projects/test-project-0/zones/test-zone-0/instances/test-name-0
""")

  def testComputeInstancesNamePageSize(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=2,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(
            results=self.ResourceSearchResults(count=3),
        ),
    )
    self.Run('alpha resources list --format=value(name) --page-size=2')
    self.AssertOutputContains("""\
test-name-0
test-name-1
test-name-2
""")

  def testComputeInstancesSortBy(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy='name,zone',
            pageSize=500,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list --sort-by=name,zone')

  def testComputeInstancesSortByReverse(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy='name desc,zone',
            pageSize=500,
            pageToken=None,
            query=None,
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list --sort-by=~name,zone')

  def testComputeInstancesQuery(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query='name:test',
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list --filter=name:test')

  def testComputeInstancesQueryNotSupported(self):
    with self.AssertRaisesExceptionMatches(
        resource_search.QueryOperatorNotSupported,
        'The [~] operator is not supported in cloud resource search queries.'):
      self.Run('alpha resources list --filter=name~test')

  def testComputeInstancesCollection(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query='@type:Instance',
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list --filter=@type:compute.instances')

  def testComputeInstancesCollectionQuery(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query='@type:Instance AND name:test',
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list '
             '--filter="@type:compute.instances name:test"')

  def testComputeInstancesNameListOperandQuery(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query='@type:Instance AND ( name:test OR name:prod )',
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list '
             '--filter="@type:compute.instances name:(test,prod)"')

  def testComputeInstancesProjectListOperandQuery(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query=('@type:Instance AND '
                   '( selfLink:/projects/test/ OR selfLink:/projects/prod/ )'),
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list '
             '--filter="@type:compute.instances project:(test,prod)"')

  def testComputeInstancesCollectionResourcesType(self):
    self.client.ResourcesService.Search.Expect(
        self.messages.CloudresourcesearchResourcesSearchRequest(
            orderBy=None,
            pageSize=500,
            pageToken=None,
            query='@type:FooBar',
        ),
        response=self.messages.SearchResponse(results=[]),
    )
    self.Run('alpha resources list --filter=@type:resources.FooBar')

  def testComputeInstancesCollectionNotSupported(self):
    with self.AssertRaisesExceptionMatches(
        resource_search.CollectionNotIndexed,
        'Collection [no.such.collection] not indexed for search.'):
      self.Run('alpha resources list --filter=@type:no.such.collection')


if __name__ == '__main__':
  resource_search_test_base.main()
