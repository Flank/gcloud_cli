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
"""Tests for tests.unit.command_lib.iot.edge.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.command_lib.iot.edge import util

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.edge import base

_CONTAINER = 'container'
_FUNCTION = 'function'


class HookTest(base.CloudIotEdgeBase, parameterized.TestCase):

  def testNameAnnotateHookContainer(self):
    expected_name = self.full_container_name
    req = self.container_create_req(
        parent=self.parent,
        container=self.messages.Container(name=self.container_name))
    hook = util.NameAnnotateHook(_CONTAINER)
    req_processed = hook(self.container_ref, None, req)
    self.assertEqual(expected_name, req_processed.container.name)

  def testNameAnnotateHookFunction(self):
    expected_name = self.full_function_name
    req = self.function_create_req(
        parent=self.parent,
        function=self.messages.Function(name=self.function_name))
    hook = util.NameAnnotateHook(_FUNCTION)
    req_processed = hook(self.function_ref, None, req)
    self.assertEqual(expected_name, req_processed.function.name)

  def testAddDefaultTopicHookContainer(self):
    req = (
        self.container_create_req(
            parent=self.parent,
            container=self.messages.Container(name=self.full_container_name)))
    req = util.AddDefaultTopicHook(_CONTAINER)(self.container_ref, None, req)
    self.assertEqual(len(req.container.inputTopics), 1)
    self.assertEqual(len(req.container.outputTopics), 1)
    self.assertEqual(req.container.inputTopics[0].topic, '/container/foo/input')
    self.assertEqual(req.container.outputTopics[0].topic,
                     '/container/foo/output')

    req = (
        self.container_patch_req(
            container=self.messages.Container(),
            name=self.full_container_name))
    req = util.AddDefaultTopicHook(_CONTAINER)(self.container_ref, None, req)
    self.assertEqual(len(req.container.inputTopics), 1)
    self.assertEqual(len(req.container.outputTopics), 1)
    self.assertEqual(req.container.inputTopics[0].topic, '/container/foo/input')
    self.assertEqual(req.container.outputTopics[0].topic,
                     '/container/foo/output')

  def testAddDefaultTopicHookFunction(self):
    req = (
        self.function_create_req(
            parent=self.parent,
            function=self.messages.Function(name=self.full_function_name)))
    req = util.AddDefaultTopicHook(_FUNCTION)(self.function_ref, None, req)
    self.assertEqual(len(req.function.inputTopics), 1)
    self.assertEqual(len(req.function.outputTopics), 1)
    self.assertEqual(req.function.inputTopics[0].topic, '/function/foo/input')
    self.assertEqual(req.function.outputTopics[0].topic, '/function/foo/output')

  @parameterized.named_parameters(
      {
          'testcase_name': 'base case',
          'arg_names': ['--docker-image'],
          'mask': ['dockerImageUri']
      },
      {
          'testcase_name': 'complex case 1',
          'arg_names': [
              '--docker-image', '--no-autostart', '--input-topic',
              '--output-topic'
          ],
          'mask':
              ['dockerImageUri', 'autostart', 'inputTopics', 'outputTopics']
      },
      {
          'testcase_name':
              'complex case 2',
          'arg_names': [
              '--env-vars-file', '--device-binding', '--volume-binding',
              '--description'
          ],
          'mask': [
              'environmentVariables', 'deviceBindings', 'volumeBindings',
              'description'
          ]
      },
      {
          'testcase_name': 'env var case',
          'arg_names': ['--remove-env-vars', '--update-env-vars'],
          'mask': ['environmentVariables']
      },
  )
  def testUpdateMaskHookContainer(self, arg_names, mask):
    args = argparse.Namespace()
    args.GetSpecifiedArgNames = lambda: arg_names
    req = self.container_patch_req(
        container=self.messages.Container(),
        name=self.full_container_name)
    req = util.UpdateMaskHook(None, args, req)
    self.assertCountEqual(req.updateMask.split(','), mask)

  @parameterized.named_parameters(
      {
          'testcase_name': 'base case',
          'arg_names': ['--source'],
          'mask': ['dockerImageUri']
      },
      {
          'testcase_name':
              'complex case 1',
          'arg_names': [
              '--source', '--input-topic', '--output-topic', '--timeout',
              '--function-type'
          ],
          'mask': [
              'dockerImageUri', 'inputTopics', 'outputTopics', 'requestTimeout',
              'functionType'
          ]
      },
      {
          'testcase_name':
              'complex case 2',
          'arg_names': [
              '--env-vars-file', '--device-binding', '--volume-binding',
              '--description', '--entry-point'
          ],
          'mask': [
              'environmentVariables', 'deviceBindings', 'volumeBindings',
              'description', 'entryPoint'
          ]
      },
      {
          'testcase_name': 'env var case',
          'arg_names': ['--remove-env-vars', '--update-env-vars'],
          'mask': ['environmentVariables']
      },
  )
  def testUpdateMaskHookFunction(self, arg_names, mask):
    args = argparse.Namespace()
    args.GetSpecifiedArgNames = lambda: arg_names
    req = self.function_patch_req(
        function=self.messages.Function(), name=self.full_function_name)
    req = util.UpdateMaskHook(None, args, req)
    self.assertCountEqual(req.updateMask.split(','), mask)

  def _AdditionalPropertiesToDict(self, items):
    return [{'key': item.key, 'value': item.value} for item in items]

  def _ContainerWithEnvVars(self, env_vars):
    """Makes Container message with given name and environment variables."""
    return self.messages.Container(
        environmentVariables=self.container_env_var_type(
            additionalProperties=list(env_vars)))

  def _FunctionWithEnvVars(self, env_vars):
    """Makes Function message with given name and environment variables."""
    return self.messages.Function(
        environmentVariables=self.function_env_var_type(
            additionalProperties=list(env_vars)))

  def testUpdateEnvVarsHookBaseContainer(self):
    args = argparse.Namespace()
    args.IsSpecified = lambda arg_name: False
    req = self.container_patch_req(
        container=self._ContainerWithEnvVars(self.env_vars),
        name=self.full_container_name)
    req = util.UpdateEnvVarsHook(_CONTAINER)(None, args, req)
    self.assertCountEqual(
        self._AdditionalPropertiesToDict(
            req.container.environmentVariables.additionalProperties),
        self.env_vars)

  def testUpdateEnvVarsHookBaseFunction(self):
    args = argparse.Namespace()
    args.IsSpecified = lambda arg_name: False
    req = self.function_patch_req(
        function=self._FunctionWithEnvVars(self.env_vars),
        name=self.full_function_name)
    req = util.UpdateEnvVarsHook(_FUNCTION)(None, args, req)
    self.assertCountEqual(
        self._AdditionalPropertiesToDict(
            req.function.environmentVariables.additionalProperties),
        self.env_vars)

  def testUpdateEnvVarsHookClear(self):
    args = argparse.Namespace()
    args.IsSpecified = lambda arg_name: arg_name == 'clear_env_vars'
    req = self.container_patch_req(
        container=self._ContainerWithEnvVars(self.env_vars),
        name=self.full_container_name)
    req = util.UpdateEnvVarsHook(_CONTAINER)(None, args, req)
    self.assertCountEqual(
        self._AdditionalPropertiesToDict(
            req.container.environmentVariables.additionalProperties), [])

  def testUpdateEnvVarsHookRemoveAndUpdate(self):
    args = argparse.Namespace()
    specified_args = ['remove_env_vars', 'update_env_vars']
    args.IsSpecified = lambda arg_name: arg_name in specified_args
    args.remove_env_vars = ['KEY1', 'KEY2']
    args.update_env_vars = {'KEY1': 'NEW_VALUE', 'KEY4': 'FOO'}
    req = self.container_patch_req(
        container=self._ContainerWithEnvVars(self.env_vars),
        name=self.full_container_name)
    req = util.UpdateEnvVarsHook(_CONTAINER)(None, args, req)
    self.assertCountEqual(
        self._AdditionalPropertiesToDict(
            req.container.environmentVariables.additionalProperties), [{
                'key': 'KEY1',
                'value': 'NEW_VALUE'
            }, {
                'key': 'KEY3',
                'value': 'VALUE3'
            }, {
                'key': 'KEY4',
                'value': 'FOO'
            }])

  def testUpdateEmptyEnvVarsHookRemoveAndUpdate(self):
    args = argparse.Namespace()
    specified_args = ['remove_env_vars', 'update_env_vars']
    args.IsSpecified = lambda arg_name: arg_name in specified_args
    args.remove_env_vars = ['KEY1', 'KEY2']
    args.update_env_vars = {'KEY1': 'NEW_VALUE', 'KEY4': 'FOO'}
    req = self.container_patch_req(
        container=self.messages.Container(), name=self.full_container_name)
    req = util.UpdateEnvVarsHook(_CONTAINER)(None, args, req)
    self.assertCountEqual(
        self._AdditionalPropertiesToDict(
            req.container.environmentVariables.additionalProperties), [{
                'key': 'KEY1',
                'value': 'NEW_VALUE'
            }, {
                'key': 'KEY4',
                'value': 'FOO'
            }])

  def SetUp(self):
    self.parent = ('projects/fake-project/locations/asia-east1/'
                   'registries/my-registry/devices/my-device')
    self.container_name = 'foo'
    self.full_container_name = (
        'projects/fake-project/locations/asia-east1/'
        'registries/my-registry/devices/my-device/containers/foo')
    self.container_ref = self.resources.Parse(
        self.full_container_name,
        collection='edge.projects.locations.registries.devices.containers')
    self.function_name = 'foo'
    self.full_function_name = (
        'projects/fake-project/locations/asia-east1/'
        'registries/my-registry/devices/my-device/functions/foo')
    self.function_ref = self.resources.Parse(
        self.full_function_name,
        collection='edge.projects.locations.registries.devices.functions')
    self.env_vars = [{
        'key': 'KEY1',
        'value': 'VALUE1'
    }, {
        'key': 'KEY2',
        'value': 'VALUE2'
    }, {
        'key': 'KEY3',
        'value': 'VALUE3'
    }]

    self.container_env_var_type = (
        self.messages.Container.EnvironmentVariablesValue)
    self.function_env_var_type = (
        self.messages.Function.EnvironmentVariablesValue)
    self.container_create_req = (
        self.messages
        .EdgeProjectsLocationsRegistriesDevicesContainersCreateRequest)
    self.container_patch_req = (
        self.messages
        .EdgeProjectsLocationsRegistriesDevicesContainersPatchRequest)
    self.function_create_req = (
        self.messages
        .EdgeProjectsLocationsRegistriesDevicesFunctionsCreateRequest)
    self.function_patch_req = (
        self.messages
        .EdgeProjectsLocationsRegistriesDevicesFunctionsPatchRequest)


class UtilTest(base.CloudIotEdgeBase, parameterized.TestCase):

  @parameterized.named_parameters(
      ('100MB', 100 * 1024 * 1024, 100),
      ('less than 1MB', 100, 1),
  )
  def testMemoryBytesToMb(self, input_byte, expected_mb):
    actual_mb = util.MemoryBytesToMb(input_byte)
    self.assertEqual(expected_mb, actual_mb)


if __name__ == '__main__':
  test_case.main()
