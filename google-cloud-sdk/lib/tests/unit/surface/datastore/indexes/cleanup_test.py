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
"""Tests of the datastore indexes cleanup command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from __future__ import with_statement

from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.app import util as test_util
from tests.lib.surface.datastore import base
from googlecloudsdk.third_party.appengine.datastore import datastore_index
import mock


class CleanupTestsGA(test_util.WithAppData, parameterized.TestCase,
                     base.DatastoreCommandUnitTest, test_case.WithInput):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.StartPatch('time.sleep')
    patcher = mock.patch(
        'googlecloudsdk.api_lib.datastore.index_api.DeleteIndexes')
    self.delete_indexes = patcher.start()
    properties.VALUES.core.disable_prompts.Set(False)

  def Project(self):
    return 'fakeproject'

  def testCleanNoIndexFile(self):
    f = self.WriteApp('app.yaml', service='default')
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        'You must provide the path to a valid index.yaml file.'):
      self.Run('--quiet datastore indexes cleanup ' + f)

  def testNo(self):
    f = self.Touch(self.temp_path, 'index.yaml', 'indexes:\n')
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('datastore indexes cleanup ' + f)

  def testDeleteIndexes_deleteAll(self):
    current_indexes = [
        index_api.BuildIndexProto(
            index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='asc'),
                datastore_index.Property(name=str('age'), direction='asc')
            ]),
        index_api.BuildIndexProto(
            index_api.ALL_ANCESTORS, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='desc'),
                datastore_index.Property(name=str('age'), direction='asc')
            ])
    ]
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=current_indexes))

    f = self.Touch(self.temp_path, 'index.yaml', 'indexes:\n')
    self.WriteInput('y\n')
    self.Run('datastore indexes cleanup ' + f)
    expected_indexes_to_be_deleted = {
        index_api.ApiMessageToIndexDefinition(index)[0]
        for index in current_indexes
    }
    self.delete_indexes.assert_called_once_with('fakeproject',
                                                expected_indexes_to_be_deleted)

  def testDeleteIndexes_nothingToDelete(self):
    current_indexes = [
        index_api.BuildIndexProto(
            index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='asc'),
                datastore_index.Property(name=str('age'), direction='desc'),
                datastore_index.Property(name=str('y'), direction='asc')
            ]),
    ]
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=current_indexes))
    self.MakeApp()
    self.WriteInput('y\n')
    self.Run('datastore indexes cleanup ' + self.FullPath('index.yaml'))
    self.delete_indexes.assert_called_once_with('fakeproject', set([]))

  def testDeleteIndexes_deleteOne(self):
    current_indexes = [
        index_api.BuildIndexProto(
            index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='asc'),
                datastore_index.Property(name=str('age'), direction='desc'),
                datastore_index.Property(name=str('y'), direction='asc')
            ]),
        index_api.BuildIndexProto(
            index_api.ALL_ANCESTORS, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='desc'),
                datastore_index.Property(name=str('age'), direction='asc')
            ])
    ]
    current_indexes[0].indexId = str('123')
    current_indexes[1].indexId = str('456')
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=current_indexes))
    self.MakeApp()
    self.WriteInput('y\n')
    self.Run('datastore indexes cleanup ' + self.FullPath('index.yaml'))
    expected_indexes_to_be_deleted = {
        index_api.ApiMessageToIndexDefinition(current_indexes[1])[0]
    }
    self.delete_indexes.assert_called_once_with('fakeproject',
                                                expected_indexes_to_be_deleted)

  def testDeleteIndexes_withKeyProperty(self):
    current_indexes = [
        index_api.BuildIndexProto(
            index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='asc'),
                datastore_index.Property(name=str('age'), direction='desc')
            ]),
        index_api.BuildIndexProto(
            index_api.NO_ANCESTOR, 'Cat', self.Project(), [
                datastore_index.Property(name=str('name'), direction='asc'),
                datastore_index.Property(name=str('city'), direction='desc')
            ])
    ]
    self.projects_indexes.List.Expect(
        request=self.messages.DatastoreProjectsIndexesListRequest(
            projectId=self.Project()),
        response=self.messages.GoogleDatastoreAdminV1ListIndexesResponse(
            indexes=current_indexes))
    self.MakeApp()
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
      - name: city
        direction: desc
      - name: __key__
    """))

    self.WriteInput('y\n')
    self.Run('datastore indexes cleanup ' + self.FullPath('index.yaml'))
    expected_indexes_to_be_deleted = set([])
    self.delete_indexes.assert_called_once_with('fakeproject',
                                                expected_indexes_to_be_deleted)


class CleanupTestsBeta(CleanupTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CleanupTestsAlpha(CleanupTestsGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
