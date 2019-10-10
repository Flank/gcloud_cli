# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.run import k8s_object
from tests.lib import cli_test_base
from tests.lib.api_lib.run import base

import mock


class FakeMessage(object):
  """Fake message object."""

  def __init__(self, name, value):
    self.name = name
    self.value = value

  def __eq__(self, other):
    if isinstance(other, type(self)):
      return self.name == other.name and self.value == other.value
    return False


class FakeK8sObject(k8s_object.KubernetesObject):
  """Fake service class."""


class KubernetesObjectTest(base.ServerlessApiBase):
  """Test KubernetesObject class."""

  def SetUp(self):
    FakeK8sObject.KIND = 'FakeKind'
    FakeK8sObject.API_CATEGORY = 'fake.api.category'

  def _EmptyServiceMessage(self):
    return self.serverless_messages.Service(
        metadata=self.serverless_messages.ObjectMeta(),
        spec=self.serverless_messages.ServiceSpec(),
        status=self.serverless_messages.ServiceStatus())

  def _EmptyTriggerMessage(self):
    return self.serverless_messages.Trigger(
        metadata=self.serverless_messages.ObjectMeta(),
        spec=self.serverless_messages.TriggerSpec(),
        status=self.serverless_messages.TriggerStatus())

  def testInitializeObject(self):
    FakeK8sObject.KIND = 'Service'
    obj = FakeK8sObject(
        self._EmptyServiceMessage(), self.serverless_messages)
    self.assertEqual(obj.Message(), self._EmptyServiceMessage())

  def testInitializeObjectWithKind(self):
    obj = FakeK8sObject(
        self._EmptyTriggerMessage(), self.serverless_messages, kind='Trigger')
    self.assertEqual(obj.Message(), self._EmptyTriggerMessage())

  def testNewObject(self):
    FakeK8sObject.KIND = 'Service'
    FakeK8sObject.API_CATEGORY = 'my.api.category'
    init_instance = self.StartObjectPatch(
        k8s_object,
        'InitializedInstance',
        return_value=self._EmptyServiceMessage())
    obj = FakeK8sObject.New(self.mock_serverless_client, 'fake-project')

    init_instance.assert_called_once_with(
        self.serverless_messages.Service, mock.ANY)
    expected = self._EmptyServiceMessage()
    expected.metadata.namespace = 'fake-project'
    expected.kind = 'Service'
    expected.apiVersion = 'my.api.category/v1alpha1'
    self.assertEqual(obj.Message(), expected)

  def testNewObjectWithKindAndApiCategory(self):
    init_instance = self.StartObjectPatch(
        k8s_object, 'InitializedInstance',
        return_value=self._EmptyTriggerMessage())
    obj = FakeK8sObject.New(self.mock_serverless_client, 'fake-project',
                            kind='Trigger', api_category='my.api.category')

    init_instance.assert_called_once_with(
        self.serverless_messages.Trigger, mock.ANY)
    expected = self._EmptyTriggerMessage()
    expected.metadata.namespace = 'fake-project'
    expected.kind = 'Trigger'
    expected.apiVersion = 'my.api.category/v1alpha1'
    self.assertEqual(obj.Message(), expected)

  def testSpecOnly(self):
    FakeK8sObject.KIND = 'Service'
    serv = self._EmptyServiceMessage()
    serv.spec.generation = 1
    obj = FakeK8sObject.SpecOnly(serv.spec, self.serverless_messages)

    expected = self._EmptyServiceMessage()
    expected.spec.generation = 1
    expected.metadata = None
    expected.status = None
    self.assertEqual(obj.Message(), expected)

  def testSpecOnlyWithKind(self):
    trigger = self._EmptyTriggerMessage()
    trigger.spec.broker = 'broke'
    obj = FakeK8sObject.SpecOnly(
        trigger.spec, self.serverless_messages, kind='Trigger')

    expected = self._EmptyTriggerMessage()
    expected.spec.broker = 'broke'
    expected.metadata = None
    expected.status = None
    self.assertEqual(obj.Message(), expected)

  def testTemplate(self):
    FakeK8sObject.KIND = 'Service'
    serv = self._EmptyServiceMessage()
    serv.metadata.name = 'serv'
    serv.spec.generation = 1
    obj = FakeK8sObject.Template(serv, self.serverless_messages)

    expected = self._EmptyServiceMessage()
    expected.metadata.name = 'serv'
    expected.spec.generation = 1
    expected.status = None
    self.assertEqual(obj.Message(), expected)

  def testTemplateWithKind(self):
    trigger = self._EmptyTriggerMessage()
    trigger.metadata.name = 'trig'
    trigger.spec.broker = 'broke'
    obj = FakeK8sObject.Template(
        trigger, self.serverless_messages, kind='Trigger')

    expected = self._EmptyTriggerMessage()
    expected.metadata.name = 'trig'
    expected.spec.broker = 'broke'
    expected.status = None
    self.assertEqual(obj.Message(), expected)


class HelpersTest(cli_test_base.CliTestBase):
  """Test support classes in the k8s_object module."""

  def SetUp(self):
    self.messages = [
        FakeMessage(name='m{}'.format(i), value=i) for i in range(5)
    ]

  def testListAsDictionaryWrapperWraps(self):
    wrapped_msgs = k8s_object.ListAsDictionaryWrapper(
        self.messages, FakeMessage)
    self.assertDictEqual({
        'm0': 0,
        'm1': 1,
        'm2': 2,
        'm3': 3,
        'm4': 4,
    }, dict(wrapped_msgs))

  def testListAsDictionaryWrapperSetObj(self):
    wrapped_msgs = k8s_object.ListAsDictionaryWrapper(
        self.messages, FakeMessage)
    wrapped_msgs['m0'] = -1
    wrapped_msgs['m5'] = 5
    self.assertDictEqual({
        'm0': -1,
        'm1': 1,
        'm2': 2,
        'm3': 3,
        'm4': 4,
        'm5': 5,
    }, dict(wrapped_msgs))

  def testListAsDictionaryWrapperFilterFunc(self):
    def _FilterFunc(obj):
      return obj.value > 2
    wrapped_msgs = k8s_object.ListAsDictionaryWrapper(
        self.messages, FakeMessage, filter_func=_FilterFunc)
    self.assertDictEqual({
        'm3': 3,
        'm4': 4,
    }, dict(wrapped_msgs))

  def testListAsDictionaryWrapperSetFailsIfBadOverwrite(self):
    """Overwriting should fail if existing message is not wrapped.

    If there's an existing message with the same unique key field, but is not
    included in the wrapped dict due to the filter func, overwrite should fail.
    """
    def _FilterFunc(obj):
      return obj.value > 2
    wrapped_msgs = k8s_object.ListAsDictionaryWrapper(
        self.messages, FakeMessage, filter_func=_FilterFunc)
    wrapped_msgs['m3'] = -3  # succeeds because included by filter
    with self.assertRaises(KeyError):
      wrapped_msgs['m0'] = -1

  def testListAsReadOnlyDictionaryWrapperWraps(self):
    wrapped_msgs = k8s_object.ListAsReadOnlyDictionaryWrapper(self.messages)
    self.assertDictEqual({
        'm0': FakeMessage(name='m0', value=0),
        'm1': FakeMessage(name='m1', value=1),
        'm2': FakeMessage(name='m2', value=2),
        'm3': FakeMessage(name='m3', value=3),
        'm4': FakeMessage(name='m4', value=4),
    }, dict(wrapped_msgs))

  def testListAsReadOnlyDictionaryWrapperFilterFunc(self):
    def _FilterFunc(obj):
      return obj.value > 2
    wrapped_msgs = k8s_object.ListAsReadOnlyDictionaryWrapper(
        self.messages, filter_func=_FilterFunc)
    self.assertDictEqual({
        'm3': FakeMessage(name='m3', value=3),
        'm4': FakeMessage(name='m4', value=4),
    }, dict(wrapped_msgs))
