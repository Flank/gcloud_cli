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
"""Tests of the Configuration API message wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import k8s_object
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.api_lib.run import base


class ConfigurationTest(base.ServerlessApiBase, parameterized.TestCase):
  """Sanity check for Configuration.

  It's also a sanity check for k8s_object, since that's abstract.

  These tests are designed to fail if an attribute is misspelled or if there
  are inconsistencies between setters and getters.
  """

  def SetUp(self):
    self.conf = configuration.Configuration.New(
        self.mock_serverless_client, 'us-central1.{}'.format(self.Project()))
    # TODO(b/112662240): Remove once this field is public
    self.is_source_branch = hasattr(self.conf.Message().spec, 'build')

  def testNeverLimitsInMap(self):
    resource_cls = self.serverless_messages.ResourceRequirements
    self.conf.container.resources = k8s_object.InitializedInstance(resource_cls)
    self.conf.resource_limits['memory'] = '512Mi'
    self.assertIsNone(self.conf.container.resources.limitsInMap)
    self.assertIsNone(self.conf.container.resources.requestsInMap)
    self.conf.container.resources.limits = None
    self.conf.resource_limits['memory'] = '512Mi'
    self.assertIsNone(self.conf.container.resources.limitsInMap)
    self.assertIsNone(self.conf.container.resources.requestsInMap)

  def testRevisionLabels(self):
    self.conf.spec.revisionTemplate.metadata = None
    self.conf.template.labels['foo'] = 'bar'
    self.assertEqual(self.conf.template.labels['foo'], 'bar')

  def testGetMessage(self):
    """Sanity check on exported message object."""
    m = self.conf.Message()
    self.assertIsInstance(m, self.serverless_messages.Configuration)
    self.assertEquals(m.metadata.namespace, 'us-central1.fake-project')

  @parameterized.parameters(['build_template_name'])
  def testBuildProperties(self, attr):
    # TODO(b/112662240): Remove conditional once the build field is public
    if not self.is_source_branch:
      return
    self.assertEquals(getattr(self.conf, attr), None)
    setattr(self.conf, attr, 'foo')
    self.assertEquals(getattr(self.conf, attr), 'foo')

  def testReadWriteProperties(self):
    """Checks that the getters are consistent with the setters."""

    attrs = ['name', 'image', 'concurrency', 'deprecated_string_concurrency']
    int_attrs = ['concurrency']
    # TODO(b/112662240): Remove conditional once the build field is public
    if self.is_source_branch:
      attrs.extend(['source_manifest', 'source_archive', 'build_template_name'])
    for attr in attrs:
      value = 12 if attr in int_attrs else 'fake-{}'.format(attr)
      setattr(self.conf.template, attr, value)
      self.assertEqual(getattr(self.conf.template, attr), value)

  def testGenerationHack(self):
    """Test that the spec generation overrides the metadata one."""
    # TODO(b/110275620): remove this hack.
    self.conf._m.spec.generation = 3
    self.conf._m.metadata.generation = 1
    self.assertEqual(self.conf.generation, 3)

  def testGenerationNoHack(self):
    """Test that the metadata generation is used if no spec generation."""
    self.conf._m.metadata.generation = 5
    self.assertEqual(self.conf.generation, 5)

  def testConditions(self):
    """Checks that conditions are gettable and don't crash."""

    self.conf._m.status.conditions = [
        self.serverless_messages.ConfigurationCondition(
            type='type1', status='True'),
        self.serverless_messages.ConfigurationCondition(
            type='type2', status='False')]
    self.assertTrue(self.conf.conditions['type1']['status'])
    self.conf._m.status = None
    self.assertEquals(len(self.conf.conditions), 0)

  @parameterized.parameters(['env_vars.literals', 'labels', 'annotations'])
  def testReadWriteDictProperties(self, dict_attr):
    """Checks that some configuration attributes behave as dicts."""
    key = 'key-{}'.format(dict_attr)
    value = 'value-{}'.format(dict_attr)

    # Allow nested dicts via dot syntax
    dict_attrs = dict_attr.split('.')
    obj = self.conf
    for attr in dict_attrs:
      obj = getattr(obj, attr)

    # Check basic assignment, retrieval, and len()
    obj[key] = value
    self.assertEqual(obj[key], value)
    self.assertEqual(len(obj), 1)

    # Check deletion
    del obj[key]
    with self.assertRaises(KeyError):
      obj[key]  # pylint: disable=pointless-statement


if __name__ == '__main__':
  test_case.main()
