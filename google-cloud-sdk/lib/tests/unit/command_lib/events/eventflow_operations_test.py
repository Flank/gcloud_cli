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
"""Tests of the Eventflow API Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.command_lib.events import exceptions
from tests.lib.surface.run import base


class EventflowOperationsTest(base.ServerlessBase):

  def testGetTrigger(self):
    """Test the get trigger api call."""
    trigger_ref = self._TriggerRef('my-trigger')
    expected_request = (
        self.serverless_messages.RunNamespacesTriggersGetRequest(
            name=trigger_ref.RelativeName()))

    expected_response = self.serverless_messages.Trigger(apiVersion='1')
    self.mock_serverless_client.namespaces_triggers.Get.Expect(
        expected_request, expected_response)

    trigger_obj = self.eventflow_client.GetTrigger(trigger_ref)
    self.assertEqual(
        trigger_obj.Message(), self.serverless_messages.Trigger(apiVersion='1'))

  def testGetTriggerReturnsNoneIfNotFound(self):
    """Test the get trigger api call returns None if no trigger found."""
    trigger_ref = self._TriggerRef('my-trigger')
    expected_request = (
        self.serverless_messages.RunNamespacesTriggersGetRequest(
            name=trigger_ref.RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Get.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    trigger_obj = self.eventflow_client.GetTrigger(trigger_ref)
    self.assertIsNone(trigger_obj)

  def testDeleteTrigger(self):
    """Test the delete trigger api call."""
    trigger_ref = self._TriggerRef('my-trigger')
    expected_request = (
        self.serverless_messages.RunNamespacesTriggersDeleteRequest(
            name=trigger_ref.RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Delete.Expect(
        expected_request, self.serverless_messages.Empty())

    self.eventflow_client.DeleteTrigger(trigger_ref)

  def testDeleteTriggerFailsIfNotFound(self):
    """Test the delete trigger api call raises an error if no trigger found."""
    trigger_ref = self._TriggerRef('my-trigger')
    expected_request = (
        self.serverless_messages.RunNamespacesTriggersDeleteRequest(
            name=trigger_ref.RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Delete.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    with self.assertRaises(exceptions.TriggerNotFound):
      self.eventflow_client.DeleteTrigger(trigger_ref)

  def testListTriggers(self):
    """Test the list triggers api call."""
    expected_request = (
        self.serverless_messages.RunNamespacesTriggersListRequest(
            parent='namespaces/{}'.format(self.namespace.namespacesId)))

    expected_response = self.serverless_messages.ListTriggersResponse(
        items=[self.serverless_messages.Trigger(apiVersion='1')])
    self.mock_serverless_client.namespaces_triggers.List.Expect(
        expected_request, expected_response)

    triggers = self.eventflow_client.ListTriggers(self.namespace)

    self.assertListEqual(
        [t.Message() for t in triggers],
        [self.serverless_messages.Trigger(apiVersion='1')])

  def testListSourceCustomResourceDefinitions(self):
    """Test the list source CRDs api call."""
    expected_request = (
        self.crd_messages.RunCustomresourcedefinitionsListRequest(
            labelSelector='eventing.knative.dev/source=true'))

    expected_response = self.crd_messages.ListCustomResourceDefinitionsResponse(
        items=[self.crd_messages.CustomResourceDefinition(apiVersion='1')])
    self.mock_crd_client.customresourcedefinitions.List.Expect(
        expected_request, expected_response)

    source_crds = self.eventflow_client.ListSourceCustomResourceDefinitions()

    self.assertListEqual(
        [crd.Message() for crd in source_crds],
        [self.crd_messages.CustomResourceDefinition(apiVersion='1')])
