# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests of the datastore indexes create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from __future__ import with_statement


from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.app import util as test_util
from tests.lib.surface.datastore import base
from googlecloudsdk.third_party.appengine.datastore import datastore_index
import mock


class CreateTestsGA(test_util.AppTestBase, test_util.WithAppData,
                    base.DatastoreCommandUnitTest, test_case.WithInput):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.StartPatch('time.sleep')
    properties.VALUES.core.disable_prompts.Set(False)

  def Project(self):
    return 'fakeproject'

  def NewRpcServer(self, server, *unused_args, **unused_kw):
    ret = super(CreateTestsGA, self).NewRpcServer(server)
    ret.set_save_request_data()
    return ret

  def testCreateNoIndexFile(self):
    f = self.WriteApp('app.yaml', service='default')
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'You must provide the path to a valid index.yaml file.'):
      self.Run('datastore indexes create ' + f)

  def testCreateNo(self):
    self.strict = False
    self.MakeApp()
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('datastore indexes create ' + self.FullPath('index.yaml'))

  @mock.patch.object(index_api, 'CreateIndexes')
  def testCreate_noCurrentIndex(self, create_indexes):
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=[]))
    self.strict = False
    self.MakeApp()
    self.WriteInput('y\n')
    self.Run('datastore indexes create ' + self.FullPath('index.yaml'))
    create_indexes.assert_called_once_with(
        'fakeproject', {
            index_api.BuildIndex(False, 'Cat', [('name', 'asc'),
                                                ('age', 'desc'), ('y', 'asc')])
        })

  @mock.patch.object(index_api, 'CreateIndexes')
  def testCreate_duplicateIndexInYaml(self, create_indexes):
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=[]))
    self.strict = False
    self.MakeApp()
    self.WriteInput('y\n')
    self.WriteConfig(('index.yaml', """
    indexes:
    - kind: Cat
      ancestor: no
      properties:
      - name: name
      - name: age
        direction: desc
    - kind: Cat
      ancestor: no
      properties:
      - name: name
      - name: age
        direction: desc
    - kind: Cat
      ancestor: no
      properties:
      - name: name
      - name: age
        direction: desc
      - name: __key__
    """))
    self.Run('datastore indexes create ' + self.FullPath('index.yaml'))
    create_indexes.assert_called_once_with('fakeproject', {
        index_api.BuildIndex(False, 'Cat', [('name', 'asc'), ('age', 'desc')])
    })

  @mock.patch.object(index_api, 'CreateIndexes')
  def testCreate_indexAlreadyExists(self, create_indexes):
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=[
                index_api.BuildIndexProto(
                    index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                        datastore_index.Property(
                            name=str('name'), direction=str('asc')),
                        datastore_index.Property(
                            name=str('age'), direction=str('desc')),
                    ])
            ]))
    self.strict = False
    self.MakeApp()
    self.WriteInput('y\n')
    self.WriteConfig(('index.yaml', """
    indexes:
    - kind: Cat
      ancestor: no
      properties:
      - name: name
      - name: age
    - kind: Cat
      ancestor: no
      properties:
      - name: name
      - name: age
        direction: desc
    """))
    self.Run('datastore indexes create ' + self.FullPath('index.yaml'))
    create_indexes.assert_called_once_with(
        'fakeproject', {
            index_api.BuildIndex(False, str('Cat'), [(str('name'), 'asc'),
                                                     (str('age'), 'asc')])
        })


class CreateTestsBeta(CreateTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateTestsAlpha(CreateTestsBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
