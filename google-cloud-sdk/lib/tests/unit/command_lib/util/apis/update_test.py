# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for the update file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.apis import update
from googlecloudsdk.command_lib.util.apis import yaml_command_schema
from tests.lib import parameterized
from tests.lib import sdk_test_base

import mock


class GetMaskStringTest(sdk_test_base.WithOutputCapture,
                        parameterized.TestCase):
  """GetMaskString Tests"""

  def SetUp(self):
    mock_arguments = mock.MagicMock(params=[])
    self.spec = mock.MagicMock(arguments=mock_arguments)

  def _MakeSpec(self, param_list):
    self.spec.arguments.params = []
    for param in param_list:
      mock_param = mock.MagicMock(arg_name=param[0], api_field=param[1])
      self.spec.arguments.params.append(mock_param)

  @parameterized.parameters(
      ([['description', 'updateInstanceRequest.instance.displayName'], [
          'nodes', 'updateInstanceRequest.instance.nodeCount'
      ]], 'updateInstanceRequest.fieldMask', 'displayName,nodeCount'),
      ([['description', 'instance.displayName'],
        ['nodes', 'instance.nodeCount']], 'fieldMask', 'displayName,nodeCount'),
  )
  def testGet(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'nodes': '--nodes',
        'description': '--description'
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(args, self.spec, mask_path)
    self.assertEqual(expected_string, mask_string)

  @parameterized.parameters(
      ([['description', None]], 'fieldMask', ''),
      ([['description', None], ['nodes', 'instance.nodeCount']],
       'fieldMask', 'nodeCount')
  )
  def testGetNoApiField(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'nodes': '--nodes',
        'description': '--description'
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(args, self.spec, mask_path)
    self.assertEqual(expected_string, mask_string)

  @parameterized.parameters(
      ([['description', 'updateInstanceRequest.instance.display.name'], [
          'nodes', 'updateInstanceRequest.instance.node.count'
      ]], 'updateInstanceRequest.fieldMask', 'display.name,node.count'),
      ([['description', 'instance.display.name'], [
          'nodes', 'instance.node.count'
      ]], 'fieldMask', 'display.name,node.count'),
  )
  def testGetNestedFields(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'nodes': '--nodes',
        'description': '--description'
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(args, self.spec, mask_path)
    self.assertEqual(expected_string, mask_string)

  @parameterized.parameters(
      ([['description', 'updateInstanceRequest.instance.display.name'], [
          'nodes', 'updateInstanceRequest.instance.node.count'
      ]], 'updateInstanceRequest.fieldMask', 'display,node'),
      ([['description', 'instance.display.name'],
        ['nodes', 'instance.node.count']], 'fieldMask', 'display,node'),
  )
  def testGetNestedFieldsNonDotted(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'nodes': '--nodes',
        'description': '--description'
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(
        args, self.spec, mask_path, is_dotted=False)
    self.assertEqual(expected_string, mask_string)

  @parameterized.parameters(
      ([[
          'update-labels',
          'updateInstanceRequest.instance.labels.additionalProperties'
      ], [
          'set-labels',
          'updateInstanceRequest.instance.labels.additionalProperties'
      ]], 'updateInstanceRequest.fieldMask', 'labels'),)
  def testGetLabels(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'update-labels': '--update-labels',
        'set-labels': '--update-labels'
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(args, self.spec, mask_path)
    self.assertEqual(expected_string, mask_string)

  @parameterized.parameters(
      ([['enable-feature', 'updateInstanceRequest.instance.enableFeature']],
       'updateInstanceRequest.fieldMask',
       'enableFeature'),)
  def testGetNegativeBooleanArgs(self, param_arr, mask_path, expected_string):
    args = parser_extensions.Namespace(_specified_args={
        'enable-feature': '--no-enable-feature',
    })
    self._MakeSpec(param_arr)
    mask_string = update.GetMaskString(args, self.spec, mask_path)
    self.assertEqual(expected_string, mask_string)

  def testGetArgGroup(self):
    arg1 = mock.MagicMock(arg_name='arg1', api_field='updateRequest.field1')
    arg2 = mock.MagicMock(arg_name='arg2', api_field='updateRequest.field2')
    arg3 = mock.MagicMock(arg_name='arg3', api_field='updateRequest.field3')
    group1 = mock.MagicMock(
        spec=yaml_command_schema.ArgumentGroup,
        arguments=[arg2, arg3])
    self.spec.arguments.params = [arg1, group1]

    args = parser_extensions.Namespace(_specified_args={
        'arg1': '--arg1',
        'arg2': '--arg2',
        'arg3': '--arg3'
    })
    mask_string = update.GetMaskString(args, self.spec, 'fieldMask')
    self.assertEqual('field1,field2,field3', mask_string)


class GetMaskFieldPathTest(sdk_test_base.WithOutputCapture,
                           parameterized.TestCase):
  """GetMaskFieldPath Tests"""

  def _MakeMethod(self, collection, method_name='patch'):
    return registry.GetMethod(collection, method_name)

  @parameterized.parameters(
      ('ml.projects.jobs', 'updateMask'),
      ('pubsub.projects.subscriptions', 'updateSubscriptionRequest.updateMask'),
      ('spanner.projects.instances', 'updateInstanceRequest.fieldMask'),
  )
  def testGetInPatch(self, collection, expected_path):
    path = update.GetMaskFieldPath(self._MakeMethod(collection))
    self.assertEqual(expected_path, path)

  @parameterized.parameters(
      ('cloudiot.projects.locations.registries.devices',
       'modifyCloudToDeviceConfig', None),
      ('sourcerepo.projects', 'updateConfig',
       'updateProjectConfigRequest.updateMask'),
  )
  def testGetInOthers(self, collection, method_name, expected_path):
    path = update.GetMaskFieldPath(self._MakeMethod(collection, method_name))
    self.assertEqual(expected_path, path)
