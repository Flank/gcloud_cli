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
"""Integration tests for Cloud Spanner."""
from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib

from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class SpannerIntegrationTest(e2e_base.WithServiceAuth):
  """Integration tests for Cloud Spanner."""

  def SetUp(self):
    id_gen = e2e_utils.GetResourceNameGenerator(prefix='spanner')
    self.instance = next(id_gen)
    self.instance_name = next(id_gen)
    self.database = next(id_gen)
    self.table = next(id_gen)
    self.column1 = next(id_gen)
    self.column2 = next(id_gen)
    self.messages = core_apis.GetMessagesModule('spanner', 'v1')

    self.retryer = retry.Retryer(max_wait_ms=60000)

  def ClearAndRun(self, command):
    self.ClearOutput()
    self.ClearErr()
    return self.Run('spanner {0}'.format(command))

  def _CheckListContains(self, list_cmd, resource_name):
    self.ClearAndRun(list_cmd)
    self.AssertOutputContains(resource_name)

  @contextlib.contextmanager
  def _CreateInstance(self):
    instance_id = self.instance
    instance_name = self.instance_name
    try:
      self.ClearAndRun('instances list')
      self.AssertOutputNotContains(instance_id)
      self.ClearAndRun('instances create {0}'
                       ' --config=regional-us-central1'
                       ' --description {1} '
                       '--nodes 1'.format(instance_id, instance_name))
      yield instance_id

    finally:
      self.Run('spanner instances delete {} --quiet'.format(instance_id))

  @contextlib.contextmanager
  def _CreateDatabase(self, instance_id):
    database_id = self.database
    try:
      self.ClearAndRun('databases list --instance {}'.format(instance_id))
      self.AssertOutputNotContains(database_id)
      self.ClearAndRun('databases create {}'
                       ' --instance {}'.format(database_id, instance_id))
      yield database_id

    finally:
      self.Run('spanner databases delete {}'
               ' --instance {} --quiet'.format(database_id, instance_id))

  @contextlib.contextmanager
  def _CreateSession(self, instance_id, database_id):
    session = self.messages.Session()
    database_ref = resources.REGISTRY.Parse(
        database_id,
        params={
            'projectsId': self.Project(),
            'instancesId': instance_id,
        },
        collection='spanner.projects.instances.databases')
    try:
      session = database_sessions.Create(database_ref)

      yield session

    finally:
      session_id = session.name.split('/')[-1]
      self.Run('spanner databases sessions delete {} --quiet'
               ' --instance {}'
               ' --database {}'.format(session_id, instance_id, database_id))

  def testMainOps(self):
    with self._CreateInstance() as instance_id:
      # There is a delay between creation and the instance appearing in list
      self.retryer.RetryOnException(self._CheckListContains,
                                    ['instances list', instance_id])

      with self._CreateDatabase(instance_id) as database_id:
        # There is a delay between creation and the database appearing in list
        self.retryer.RetryOnException(
            self._CheckListContains,
            ['databases list --instance {}'.format(instance_id), database_id])

        with self._CreateSession(instance_id, database_id) as session:
          # There is a delay between creation and the session appearing in list
          self.retryer.RetryOnException(self._CheckListContains, [
              'databases sessions list --instance {} --database {} --uri'.
              format(instance_id, database_id),
              session.name.split('/').pop()
          ])


if __name__ == '__main__':
  test_case.main()
