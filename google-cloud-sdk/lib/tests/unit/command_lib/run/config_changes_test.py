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
"""Tests for config_changes.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import name_generator
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.run import base


CloudSQLArgs = collections.namedtuple('CloudSQLArgs', [
    'add_cloudsql_instances', 'remove_cloudsql_instances',
    'clear_cloudsql_instances', 'set_cloudsql_instances'])


EMPTY_CLOUDSQL_ARGS = CloudSQLArgs(None, None, None, None)


class ConfigChangesTest(base.ServerlessApiBase, test_case.TestCase,
                        parameterized.TestCase):

  def SetUp(self):
    self.resource = service.Service.New(
        self.mock_serverless_client, 'fake-project')
    self.resource.name = 'myservice'
    self.template = self.resource.template
    self.StartObjectPatch(
        name_generator,
        'GenerateName',
        side_effect=lambda **kwargs: '{}-genr8d'.format(kwargs['prefix']))

  def testReplaceServiceChange(self):
    new_service = service.Service.New(
        self.mock_serverless_client, 'fake-project')
    replace_change = config_changes.ReplaceServiceChange(new_service)
    self.resource.metadata.resourceVersion = 'abc'
    replaced_service = replace_change.Adjust(self.resource)
    self.assertEqual(replaced_service, new_service)
    self.assertEqual(replaced_service.metadata.resourceVersion, 'abc')

  def _MakeSecretEnvVarSource(self, name, key):
    return self.serverless_messages.EnvVarSource(
        secretKeyRef=self.serverless_messages.SecretKeySelector(
            key=key,
            name=name))

  def _MakeConfigMapEnvVarSource(self, name, key):
    return self.serverless_messages.EnvVarSource(
        configMapKeyRef=self.serverless_messages.ConfigMapKeySelector(
            key=key,
            name=name))

  def testEnvLiteralUpdate(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'})
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': 'x1',
        'k2': 'v2',
        'k3': 'v3',
    }, dict(self.template.env_vars.literals))

  def testEnvLiteralUpdateWithSpace(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_update={'   k1': 'x1', ' k3': 'v3'})
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': 'x1',
        'k2': 'v2',
        'k3': 'v3',
    }, dict(self.template.env_vars.literals))

  def testEnvLiteralRemove(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(env_vars_to_remove=['k1'])
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({'k2': 'v2'}, dict(self.template.env_vars.literals))

  def testEnvLiteralRemoveWithSpace(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_remove=['  k1'])
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({'k2': 'v2'}, dict(self.template.env_vars.literals))

  def testEnvLiteralUpdateRemove(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        env_vars_to_remove=['k1'])
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': 'x1',
        'k2': 'v2',
        'k3': 'v3',
    }, dict(self.template.env_vars.literals))

  def testEnvLiteralSet(self):
    self.template.env_vars.literals.update({'k1': 'v1', 'k2': 'v2'})
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_update={'k1': 'x1', 'k3': 'v3'},
        clear_others=True)
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': 'x1',
        'k3': 'v3',
    }, dict(self.template.env_vars.literals))

  def testEnvLiteralSetFailsWhenOtherTypeExists(self):
    self.template.env_vars.secrets.update({
        'k1': self._MakeSecretEnvVarSource('s1', 'key'),
    })
    env_change = config_changes.EnvVarLiteralChanges(
        env_vars_to_update={'k1': 'x1'},
        clear_others=True)
    with self.assertRaises(exceptions.ConfigurationError):
      self.resource = env_change.Adjust(self.resource)

  def testEnvVarSourceSet(self):
    self.template.env_vars.secrets.update({
        'k1': self._MakeSecretEnvVarSource('s1', 'key1'),
        'k2': self._MakeSecretEnvVarSource('s2', 'key2'),
    })
    env_change = config_changes.SecretEnvVarChanges(
        env_vars_to_update={'k1': 's3:key3', 'k3': 'secret:key'},
        clear_others=True)
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': self._MakeSecretEnvVarSource('s3', 'key3'),
        'k3': self._MakeSecretEnvVarSource('secret', 'key'),
    }, dict(self.template.env_vars.secrets))

  def testEnvVarSourceUpdate(self):
    self.template.env_vars.secrets.update({
        'k1': self._MakeSecretEnvVarSource('s1', 'key1'),
        'k2': self._MakeSecretEnvVarSource('s2', 'key2'),
    })
    env_change = config_changes.SecretEnvVarChanges(
        env_vars_to_update={'k1': 's3:key3', 'k3': 'secret:key'})
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k1': self._MakeSecretEnvVarSource('s3', 'key3'),
        'k2': self._MakeSecretEnvVarSource('s2', 'key2'),
        'k3': self._MakeSecretEnvVarSource('secret', 'key'),
    }, dict(self.template.env_vars.secrets))

  def testEnvSourceSetFailsWithNoKey(self):
    with self.assertRaises(exceptions.ConfigurationError):
      config_changes.SecretEnvVarChanges(env_vars_to_update={'k1': 's1'})

  def testEnvSourceSetFailsWhenLiteralExists(self):
    self.template.env_vars.literals.update({'k1': 'v1'})
    env_change = config_changes.SecretEnvVarChanges(
        env_vars_to_update={'k1': 's1:key'})
    with self.assertRaises(exceptions.ConfigurationError):
      self.resource = env_change.Adjust(self.resource)

  def testEnvSourceSetFailsWhenOtherSourceExists(self):
    self.template.env_vars.secrets.update({
        'k1': self._MakeSecretEnvVarSource('s1', 'key'),
    })
    env_change = config_changes.ConfigMapEnvVarChanges(
        env_vars_to_update={'k1': 'c1:key'})
    with self.assertRaises(exceptions.ConfigurationError):
      self.resource = env_change.Adjust(self.resource)

  def testEnvSourceClear(self):
    self.template.env_vars.literals.update({'k0': 'v0'})
    self.template.env_vars.secrets.update({
        'k1': self._MakeSecretEnvVarSource('s1', 'key'),
        'k2': self._MakeSecretEnvVarSource('s2', 'key'),
        'k3': self._MakeSecretEnvVarSource('s3', 'key'),
    })
    self.template.env_vars.config_maps.update({
        'k4': self._MakeConfigMapEnvVarSource('c1', 'key'),
        'k5': self._MakeConfigMapEnvVarSource('c2', 'key'),
    })
    env_change = config_changes.SecretEnvVarChanges(clear_others=True)
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({'k0': 'v0'}, dict(self.template.env_vars.literals))
    self.assertDictEqual({}, dict(self.template.env_vars.secrets))
    self.assertDictEqual({
        'k4': self._MakeConfigMapEnvVarSource('c1', 'key'),
        'k5': self._MakeConfigMapEnvVarSource('c2', 'key'),
    }, dict(self.template.env_vars.config_maps))

  def testEnvSourceRemove(self):
    self.template.env_vars.config_maps.update({
        'k1': self._MakeConfigMapEnvVarSource('c1', 'key'),
        'k2': self._MakeConfigMapEnvVarSource('c2', 'key'),
    })
    env_change = config_changes.ConfigMapEnvVarChanges(
        env_vars_to_remove=['k1'])
    self.resource = env_change.Adjust(self.resource)
    self.assertDictEqual({
        'k2': self._MakeConfigMapEnvVarSource('c2', 'key'),
    }, dict(self.template.env_vars.config_maps))

  def testCloudSQLAdd(self):
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    self.resource = sql_change.Adjust(self.resource)
    self.assertEqual(
        'proj:us-central1:foo,proj:us-central1:bar',
        self.template.annotations['run.googleapis.com/cloudsql-instances'])

  def testCloudSQLAddNoRegion(self):
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', None,
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.Adjust(self.resource)

  def testCloudSQLAddNoProject(self):
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges(None, 'us-central1',
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.Adjust(self.resource)

  def testCloudSQLBad(self):
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['like:a:spider::foo', 'bar'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    with self.assertRaises(exceptions.CloudSQLError):
      sql_change.Adjust(self.resource)

  def testCloudSQLRemove(self):
    self.template.annotations.update({
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar',
    })
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(remove_cloudsql_instances=
                                              ['foo'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    self.resource = sql_change.Adjust(self.resource)
    self.assertEqual(
        'proj:us-central1:bar',
        self.template.annotations['run.googleapis.com/cloudsql-instances'])

  def testCloudSQLSpecRegionProj(self):
    self.template.annotations.update({
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar',
    })
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(add_cloudsql_instances=
                                              ['proj2:us-central1:foo',
                                               'proj:us-east1:foo'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    self.resource = sql_change.Adjust(self.resource)
    self.assertEqual(
        ('proj:us-central1:foo,proj:us-central1:bar,'
         'proj2:us-central1:foo,proj:us-east1:foo'),
        self.template.annotations['run.googleapis.com/cloudsql-instances'])

  def testCloudSQLSet(self):
    self.template.annotations.update({
        'run.googleapis.com/cloudsql-instances':
            'proj:us-central1:foo,proj:us-central1:bar',
    })
    dummy_args = EMPTY_CLOUDSQL_ARGS._replace(set_cloudsql_instances=
                                              ['blag'])
    sql_change = config_changes.CloudSQLChanges('proj', 'us-central1',
                                                dummy_args)
    self.resource = sql_change.Adjust(self.resource)
    self.assertEqual(
        'proj:us-central1:blag',
        self.template.annotations['run.googleapis.com/cloudsql-instances'])

  def testRevisionSuffixSet(self):
    self.template.name = 'myservice-oldsuffix'
    revision_name_change = config_changes.RevisionNameChanges('newsuffix')
    self.resource = revision_name_change.Adjust(self.resource)
    self.assertEqual(self.template.name, 'myservice-newsuffix')

  def _MakeSecretVolumeSource(self, name, *items):
    source = self.serverless_messages.SecretVolumeSource(secretName=name)
    for key, path in items:
      source.items.append(
          self.serverless_messages.KeyToPath(key=key, path=path))
    return source

  def _MakeConfigMapVolumeSource(self, name, *items):
    source = self.serverless_messages.ConfigMapVolumeSource(name=name)
    for key, path in items:
      source.items.append(
          self.serverless_messages.KeyToPath(key=key, path=path))
    return source

  def testVolumeUpdate(self):
    self.template.volumes.secrets.update({
        'secret1-abc':
            self._MakeSecretVolumeSource('secret1', ('item0', 'item0')),
        'secret2-def':
            self._MakeSecretVolumeSource('secret2'),
        'secret3-ghi':
            self._MakeSecretVolumeSource('secret3'),
    })
    self.template.volumes.config_maps.update({
        'config1-abc': self._MakeConfigMapVolumeSource('config1'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
        '/path1/1': 'secret1-abc',
        '/path2': 'secret2-def',
        '/path3': 'secret3-ghi',
    })
    self.template.volume_mounts.config_maps.update({
        '/path4': 'config1-abc',
    })
    volume_change = config_changes.SecretVolumeChanges(
        mounts_to_update={
            '/path1/1': 'secret3:item1',
            '/path2': 'new-secret6:item1',
            '/path3': 'secret1',
            '/path5': 'new-secret5',
        })
    self.resource = volume_change.Adjust(self.resource)
    self.assertDictEqual({
        'secret1-abc':
            self._MakeSecretVolumeSource('secret1', ('item0', 'item0')),
        'new-secret5-genr8d':
            self._MakeSecretVolumeSource('new-secret5'),
        'secret1-genr8d':
            self._MakeSecretVolumeSource('secret1'),
        'secret3-genr8d':
            self._MakeSecretVolumeSource('secret3', ('item1', 'item1')),
        'new-secret6-genr8d':
            self._MakeSecretVolumeSource('new-secret6', ('item1', 'item1')),
    }, dict(self.template.volumes.secrets))
    self.assertDictEqual({
        'config1-abc': self._MakeConfigMapVolumeSource('config1'),
    }, dict(self.template.volumes.config_maps))
    self.assertDictEqual({
        '/path1': 'secret1-abc',
        '/path1/1': 'secret3-genr8d',
        '/path2': 'new-secret6-genr8d',
        '/path3': 'secret1-genr8d',
        '/path5': 'new-secret5-genr8d',
    }, dict(self.template.volume_mounts.secrets))
    self.assertDictEqual({
        '/path4': 'config1-abc',
    }, dict(self.template.volume_mounts.config_maps))

  def testVolumeUpdateFailsIfWrongType(self):
    self.template.volumes.secrets.update({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
    })
    volume_change = config_changes.ConfigMapVolumeChanges(
        mounts_to_update={
            '/path1': 'config1',
        })
    with self.assertRaises(exceptions.ConfigurationError):
      volume_change.Adjust(self.resource)

  def testVolumeClear(self):
    """Volumes and mounts are cleared that are of the type we want to clear."""
    self.template.volumes.secrets.update({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
        'secret2-def': self._MakeSecretVolumeSource('secret2'),
    })
    self.template.volumes.config_maps.update({
        'config1-abc': self._MakeConfigMapVolumeSource('config1'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
        '/path/1': 'secret1-abc',
        '/path2': 'secret2-def',
    })
    self.template.volume_mounts.config_maps.update({
        '/path3': 'config1-abc',
    })
    volume_change = config_changes.SecretVolumeChanges(clear_others=True)
    self.resource = volume_change.Adjust(self.resource)
    self.assertDictEqual({}, dict(self.template.volumes.secrets))
    self.assertDictEqual({
        'config1-abc': self._MakeConfigMapVolumeSource('config1'),
    }, dict(self.template.volumes.config_maps))
    self.assertDictEqual({}, dict(self.template.volume_mounts.secrets))
    self.assertDictEqual({
        '/path3': 'config1-abc',
    }, dict(self.template.volume_mounts.config_maps))

  def testVolumeRemove(self):
    self.template.volumes.secrets.update({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    })
    self.template.volumes.config_maps.update({
        'config1-abc': self._MakeConfigMapVolumeSource('config1'),
        'config2-def': self._MakeConfigMapVolumeSource('config2'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
    })
    self.template.volume_mounts.config_maps.update({
        '/path2': 'config1-abc',
        '/path3': 'config2-def',
    })
    volume_change = config_changes.ConfigMapVolumeChanges(
        mounts_to_remove=['/path2'])
    self.resource = volume_change.Adjust(self.resource)
    self.assertDictEqual({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    }, dict(self.template.volumes.secrets))
    self.assertDictEqual({
        'config2-def': self._MakeConfigMapVolumeSource('config2'),
    }, dict(self.template.volumes.config_maps))
    self.assertDictEqual({
        '/path1': 'secret1-abc',
    }, dict(self.template.volume_mounts.secrets))
    self.assertDictEqual({
        '/path3': 'config2-def',
    }, dict(self.template.volume_mounts.config_maps))

  def testRemoveSilentlyFailsIfDoesntExist(self):
    self.template.volumes.secrets.update({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
    })
    volume_change = config_changes.ConfigMapVolumeChanges(
        mounts_to_remove=['/path1', '/path2'])
    self.resource = volume_change.Adjust(self.resource)
    self.assertDictEqual({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    }, dict(self.template.volumes.secrets))
    self.assertDictEqual({
        '/path1': 'secret1-abc',
    }, dict(self.template.volume_mounts.secrets))

  def testVolumeRemoveKeepsVolumeIfUsed(self):
    """If the volume is still in use after mount removal, it isn't deleted."""
    self.template.volumes.secrets.update({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    })
    self.template.volume_mounts.secrets.update({
        '/path1': 'secret1-abc',
        '/path2': 'secret1-abc',
    })
    volume_change = config_changes.SecretVolumeChanges(
        mounts_to_remove=['/path2'])
    self.resource = volume_change.Adjust(self.resource)
    self.assertDictEqual({
        'secret1-abc': self._MakeSecretVolumeSource('secret1'),
    }, dict(self.template.volumes.secrets))
    self.assertDictEqual({
        '/path1': 'secret1-abc',
    }, dict(self.template.volume_mounts.secrets))

# TODO(b/112157693): Add tests for ConcurrencyChanges and ResourceChanges.

  def testSetVpcConnector(self):
    vpc_connector_change = config_changes.VpcConnectorChange('test-change-name')

    self.resource = vpc_connector_change.Adjust(self.resource)
    self.assertDictEqual({
        'run.googleapis.com/vpc-access-connector': 'test-change-name',
    }, dict(self.resource.annotations))

  def testClearVpcConnector(self):
    self.resource.annotations[
        'run.googleapis.com/vpc-access-connector'] = 'something'
    self.resource = config_changes.ClearVpcConnectorChange(
        ).Adjust(self.resource)
    self.assertDictEqual({}, dict(self.resource.annotations))

  def testClearVpcConnectorDoesntExist(self):
    self.resource = config_changes.ClearVpcConnectorChange(
        ).Adjust(self.resource)
    self.assertDictEqual({}, dict(self.resource.annotations))

  def testSetTemplateAnnotationChange(self):
    config_changes.SetTemplateAnnotationChange(
        'k', 'v').Adjust(self.resource)
    self.assertDictEqual({'k': 'v'}, dict(self.template.annotations))

  def testDeleteTemplateAnnotationChange(self):
    self.template.annotations.update({
        'k': 'v',
        'k2': 'v2',
    })
    self.resource = config_changes.DeleteTemplateAnnotationChange(
        'k2').Adjust(self.resource)
    self.assertDictEqual({'k': 'v'}, dict(self.template.annotations))

  def testTrafficChanges(self):
    latest100 = self.serverless_messages.TrafficTarget(
        latestRevision=True, percent=100)
    self.resource.traffic[traffic.LATEST_REVISION_KEY] = latest100
    self.resource = config_changes.TrafficChanges(
        {'r1': 90}, 10).Adjust(self.resource)
    latest10 = self.serverless_messages.TrafficTarget(
        latestRevision=True, percent=10)
    r190 = self.serverless_messages.TrafficTarget(
        revisionName='r1', percent=90)
    expect = {'r1': r190, traffic.LATEST_REVISION_KEY: latest10}
    self.assertEqual(expect, self.resource.traffic)

  @parameterized.parameters(
      ('somecmd', ['somecmd']),
      ('some/cmd   and\nmore', ['some/cmd', 'and', 'more']),
      ('some "quoted command"', ['some', 'quoted command']))
  def testContainerCommandChange(self, input_str, expected_list):
    self.template.container.command = []
    self.resource = config_changes.ContainerCommandChange(input_str).Adjust(
        self.resource)
    self.assertEqual(expected_list, self.template.container.command)

  @parameterized.parameters(
      ('--flag value', ['--flag', 'value']),
      ('$(VAR)   --flag     value', ['$(VAR)', '--flag', 'value']),
      ('--flag="multi word  value"', ['--flag=multi word  value']))
  def testContainerArgsChange(self, input_str, expected_list):
    self.template.container.args = []
    self.resource = config_changes.ContainerArgsChange(input_str).Adjust(
        self.resource)
    self.assertEqual(expected_list, self.template.container.args)
