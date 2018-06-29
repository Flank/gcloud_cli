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

"""Unit tests for cpanner flags module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.core import resources
from tests.lib import completer_test_base
from tests.lib.surface.spanner import base


class CompletionTest(base.SpannerTestBase, completer_test_base.CompleterBase):

  def _Name(self, name, collection=None, params=None, uri=False):
    all_params = {'projectsId': self.Project()}
    if params:
      all_params.update(params)
    ref = resources.REGISTRY.Parse(
        name, params=all_params, collection=collection)
    if uri:
      return ref.RelativeName(), ref.SelfLink()
    return ref.RelativeName()

  def testInstanceCompleter(self):
    self.client.projects_instances.List.Expect(
        request=self.msgs.SpannerProjectsInstancesListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=self.msgs.ListInstancesResponse(instances=[
            self.msgs.Instance(name=self._Name(
                'insA', 'spanner.projects.instances')),
            self.msgs.Instance(name=self._Name(
                'insB', 'spanner.projects.instances')),
        ]))

    self.RunCompleter(
        flags.InstanceCompleter,
        expected_command=[
            'spanner',
            'instances',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['insA', 'insB'],
        cli=self.cli,
    )

  def testInstanceConfigCompleter(self):
    self.client.projects_instanceConfigs.List.Expect(
        request=self.msgs.SpannerProjectsInstanceConfigsListRequest(
            parent='projects/'+self.Project(), pageSize=100),
        response=self.msgs.ListInstanceConfigsResponse(instanceConfigs=[
            self.msgs.InstanceConfig(name=self._Name(
                'cfgA', 'spanner.projects.instanceConfigs')),
            self.msgs.InstanceConfig(name=self._Name(
                'cfgB', 'spanner.projects.instanceConfigs')),
        ]))

    self.RunCompleter(
        flags.InstanceConfigCompleter,
        expected_command=[
            'spanner',
            'instance-configs',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=['cfgA', 'cfgB'],
        cli=self.cli,
    )

  def testOperationCompleter(self):
    instance_id = 'insA'
    instance = self._Name(instance_id, 'spanner.projects.instances')
    params = {'instancesId': instance_id}
    self.client.projects_instances_operations.List.Expect(
        request=self.msgs.SpannerProjectsInstancesOperationsListRequest(
            name=instance+'/operations', pageSize=100),
        response=self.msgs.ListOperationsResponse(operations=[
            self.msgs.Operation(name=self._Name(
                'op1', 'spanner.projects.instances.operations', params=params,
            )),
            self.msgs.Operation(name=self._Name(
                'op2', 'spanner.projects.instances.operations', params=params,
            )),
        ]))

    self.RunCompleter(
        flags.OperationCompleter,
        expected_command=[
            'spanner',
            'operations',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--instance=' + instance_id,
        ],
        expected_completions=['op1', 'op2'],
        args={'--instance': instance_id},
        cli=self.cli,
    )

  def testDatabaseCompleter(self):
    instance_id = 'insA'
    instance = self._Name(instance_id, 'spanner.projects.instances')
    params = {'instancesId': instance_id}
    self.client.projects_instances_databases.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesListRequest(
            parent=instance, pageSize=100),
        response=self.msgs.ListDatabasesResponse(databases=[
            self.msgs.Database(name=self._Name(
                'db1', 'spanner.projects.instances.databases', params=params,
            )),
            self.msgs.Database(name=self._Name(
                'db2', 'spanner.projects.instances.databases', params=params,
            )),
        ]))

    self.RunCompleter(
        flags.DatabaseCompleter,
        expected_command=[
            'spanner',
            'databases',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--instance=' + instance_id,
        ],
        expected_completions=['db1', 'db2'],
        args={'--instance': instance_id},
        cli=self.cli,
    )

  def testDatabaseOperationCompleter(self):
    instance_id = 'insA'
    database_id = 'db1'
    params = {'instancesId': instance_id, 'databasesId': database_id}
    database = self._Name(
        database_id, 'spanner.projects.instances.databases', params)
    self.client.projects_instances_databases_operations.List.Expect(
        request=(
            self.msgs.SpannerProjectsInstancesDatabasesOperationsListRequest(
                name=database+'/operations', pageSize=100)),
        response=self.msgs.ListOperationsResponse(operations=[
            self.msgs.Operation(name=self._Name(
                'op1', 'spanner.projects.instances.databases.operations',
                params=params,
            )),
            self.msgs.Operation(name=self._Name(
                'op2', 'spanner.projects.instances.databases.operations',
                params=params,
            )),
        ]))

    self.RunCompleter(
        flags.DatabaseOperationCompleter,
        expected_command=[
            'spanner',
            'operations',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--instance=' + instance_id,
            '--database=' + database_id,
        ],
        expected_completions=['op1', 'op2'],
        args={'--instance': instance_id, '--database': database_id},
        cli=self.cli,
    )

  def testDatabaseSessionCompleter(self):
    instance_id = 'insA'
    database_id = 'db1'
    params = {'instancesId': instance_id, 'databasesId': database_id}
    database = resources.REGISTRY.Parse(
        database_id,
        params={
            'projectsId': self.Project(),
            'instancesId': instance_id,
        },
        collection='spanner.projects.instances.databases')
    self.client.projects_instances_databases_sessions.List.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
            database=database.RelativeName()),
        response=self.msgs.ListSessionsResponse(sessions=[
            self.msgs.Session(name=self._Name(
                'session1',
                'spanner.projects.instances.databases.sessions',
                params=params)),
            self.msgs.Session(name=self._Name(
                'session2',
                'spanner.projects.instances.databases.sessions',
                params=params))
        ]))

    self.RunCompleter(
        flags.DatabaseSessionCompleter,
        expected_command=[
            'beta',
            'spanner',
            'databases',
            'sessions',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
            '--database=' + database_id,
            '--instance=' + instance_id,
        ],
        expected_completions=['session1', 'session2'],
        args={'--database': database_id,
              '--instance': instance_id},
        cli=self.cli)


class HelperTest(base.SpannerTestBase):

  def testFixDdl(self):
    ddl_strings = [
        'CREATE TABLE MyTable;',
        'CREATE TABLE anotherTable;CREATE TABLE oneMoreTable'
    ]

    self.assertEqual([
        'CREATE TABLE MyTable', 'CREATE TABLE anotherTable',
        'CREATE TABLE oneMoreTable'
    ], flags.SplitDdlIntoStatements(ddl_strings))


if __name__ == '__main__':
  completer_test_base.main()
