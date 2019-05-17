# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for config_changes.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions
from tests.lib import test_case
import mock


CloudSQLArgs = collections.namedtuple('CloudSQLArgs', [
    'add_cloudsql_instances', 'remove_cloudsql_instances',
    'clear_cloudsql_instances', 'set_cloudsql_instances'])


EMPTY_CLOUDSQL_ARGS = CloudSQLArgs(None, None, None, None)


class ConfigChangesTest(test_case.TestCase):

  def SetUp(self):
    self.config = mock.Mock()
    self.config.env_vars = {'k1': 'v1', 'k2': 'v2'}
    self.metadata = mock.Mock()

  def testEnvUpdate(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'})
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(
        self.config.env_vars, {'k1': 'x1', 'k2': 'v2', 'k3': 'v3'})

  def testEnvUpdateWithSpace(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'   k1': 'x1', ' k3': 'v3'})
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(
        self.config.env_vars, {'k1': 'x1', 'k2': 'v2', 'k3': 'v3'})

  def testEnvRemove(self):
    env_change = config_changes.EnvVarChanges(env_vars_to_remove=['k1'])
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(self.config.env_vars, {'k2': 'v2'})

  def testEnvRemoveWithSpace(self):
    env_change = config_changes.EnvVarChanges(env_vars_to_remove=['  k1'])
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(self.config.env_vars, {'k2': 'v2'})

  def testEnvUpdateRemove(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        env_vars_to_remove=['k1'])
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(
        self.config.env_vars, {'k1': 'x1', 'k2': 'v2', 'k3': 'v3'})

  def testEnvSet(self):
    env_change = config_changes.EnvVarChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        clear_others=True)
    env_change.AdjustConfiguration(self.config, self.metadata)
    self.assertDictEqual(self.config.env_vars, {'k1': 'x1', 'k3': 'v3'})

  def testCloudSQLAdd(self):
    self.config.revision_annotations = {}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    sql_change.AdjustConfiguration(self.config, self.metadata)
    annot = self.config.revision_annotations[
        'run.googleapis.com/cloudsql-instances']
    self.assertEqual(annot, 'proj:us-central1:foo,proj:us-central1:bar')

  def testCloudSQLAddNoRegion(self):
    self.config.revision_annotations = {}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', None,
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.AdjustConfiguration(self.config, self.metadata)

  def testCloudSQLAddNoProject(self):
    self.config.revision_annotations = {}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges(None, 'us-central1',
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.AdjustConfiguration(self.config, self.metadata)

  def testCloudSQLBad(self):
    self.config.revision_annotations = {}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['like:a:spider::foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.AdjustConfiguration(self.config, self.metadata)

  def testCloudSQLRemove(self):
    self.config.revision_annotations = {
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar'}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(remove_cloudsql_instances=
                                              ['foo'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    sql_change.AdjustConfiguration(self.config, self.metadata)
    annot = self.config.revision_annotations[
        'run.googleapis.com/cloudsql-instances']
    self.assertEqual(annot, 'proj:us-central1:bar')

  def testCloudSQLSpecRegionProj(self):
    self.config.revision_annotations = {
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar'}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['proj2:us-central1:foo',
                                               'proj:us-east1:foo'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    sql_change.AdjustConfiguration(self.config, self.metadata)
    annot = self.config.revision_annotations[
        'run.googleapis.com/cloudsql-instances']
    self.assertEqual(annot, 'proj:us-central1:foo,proj:us-central1:bar,'
                     'proj2:us-central1:foo,proj:us-east1:foo')

  def testCloudSQLSet(self):
    self.config.revision_annotations = {
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar'}
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(set_cloudsql_instances=
                                              ['blag'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    sql_change.AdjustConfiguration(self.config, self.metadata)
    annot = self.config.revision_annotations[
        'run.googleapis.com/cloudsql-instances']
    self.assertEqual(annot, 'proj:us-central1:blag')

# TODO(b/112157693): Add tests for ConcurrencyChanges and ResourceChanges.
