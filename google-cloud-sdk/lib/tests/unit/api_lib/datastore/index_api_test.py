# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for api_lib.datastore.index_api."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.api_lib.datastore import util
from tests.lib import test_case
from googlecloudsdk.third_party.appengine.datastore import datastore_index

PROJECT_ID = 'my_project'
KIND = 'kind'


class DatastoreIndexUtilTest(test_case.TestCase):

  def _IndexDefinitionToApiMessage(self, project_id, index_definition):
    """Converts an index definition to GoogleDatastoreAdminV1Index."""
    messages = util.GetMessages()
    proto = messages.GoogleDatastoreAdminV1Index()
    proto.projectId = project_id
    proto.state = index_api.CREATING
    proto.kind = index_definition.kind
    if index_definition.ancestor:
      proto.ancestor = index_api.ALL_ANCESTORS
    else:
      proto.ancestor = index_api.NO_ANCESTOR
    props = []
    if index_definition.properties is not None:
      for prop in index_definition.properties:
        prop_proto = messages.GoogleDatastoreAdminV1IndexedProperty()
        prop_proto.name = prop.name
        props.append(prop_proto)
        if prop.IsAscending():
          prop_proto.direction = index_api.ASCENDING
        else:
          prop_proto.direction = index_api.DESCENDING
    proto.properties = props
    return proto

  def testIndexDefinitionToProtoRoundTrip(self):
    index_definition = index_api.BuildIndex(False, KIND, [
        ('prop1', 'asc'),
        ('prop2', 'desc'),
    ])
    self.assertEqual(
        index_definition,
        index_api.ApiMessageToIndexDefinition(
            self._IndexDefinitionToApiMessage(PROJECT_ID, index_definition))[1])

  def testIndexProtoToDefinitionRoundTrip(self):
    proto = index_api.BuildIndexProto(
        index_api.ALL_ANCESTORS, KIND, PROJECT_ID, [
            datastore_index.Property(name=str('prop1'), direction=str('asc')),
            datastore_index.Property(name=str('prop2'), direction=str('desc')),
        ])
    self.assertEqual(
        proto,
        self._IndexDefinitionToApiMessage(
            PROJECT_ID,
            index_api.ApiMessageToIndexDefinition(proto)[1]))


if __name__ == '__main__':
  test_case.main()
