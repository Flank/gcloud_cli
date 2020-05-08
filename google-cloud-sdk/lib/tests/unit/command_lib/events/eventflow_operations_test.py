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

import random

from apitools.base.protorpclite import protojson
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.events import custom_resource_definition
from googlecloudsdk.api_lib.events import iam_util
from googlecloudsdk.api_lib.events import source
from googlecloudsdk.api_lib.events import trigger
from googlecloudsdk.api_lib.run import secret
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import stages
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.console import progress_tracker
from tests.lib import test_case
from tests.lib.surface.run import base

import mock


class EventflowConnectTest(test_case.TestCase):
  """Tests eventflow_operations.Connect()."""

  def SetUp(self):
    self.mock_client = mock.Mock()
    self.StartObjectPatch(
        apis_internal, '_GetClientInstance', return_value=self.mock_client)

  def testConnectAnthos(self):
    mock_context = mock.Mock()
    mock_context.__enter__ = mock.Mock(return_value=mock_context)
    mock_context.__exit__ = mock.Mock(return_value=False)
    mock_context.supports_one_platform = False
    mock_context.region = None

    with eventflow_operations.Connect(mock_context) as eventflow_client:
      self.assertEqual(eventflow_client._client, self.mock_client)
      self.assertEqual(eventflow_client._core_client, self.mock_client)
      self.assertEqual(eventflow_client._crd_client, self.mock_client)
      self.assertEqual(eventflow_client._op_client, self.mock_client)
      self.assertIsNone(eventflow_client._region)

  def testConnectManaged(self):
    mock_context = mock.Mock()
    mock_context.__enter__ = mock.Mock(return_value=mock_context)
    mock_context.__exit__ = mock.Mock(return_value=False)
    mock_context.supports_one_platform = True
    mock_context.region = base.DEFAULT_REGION

    with eventflow_operations.Connect(mock_context) as eventflow_client:
      self.assertEqual(eventflow_client._client, self.mock_client)
      self.assertIsNone(eventflow_client._core_client)
      self.assertEqual(eventflow_client._crd_client, self.mock_client)
      self.assertEqual(eventflow_client._op_client, self.mock_client)
      self.assertEqual(eventflow_client._region, base.DEFAULT_REGION)


class EventflowOperationsTest(base.ServerlessBase):

  def SetUp(self):
    self.StartObjectPatch(random, 'random', return_value=0)
    self.StartObjectPatch(util, 'WaitForCondition')
    gsa_key = apis.GetMessagesModule('iam', 'v1').ServiceAccountKey(
        name='projects/fake-project/serviceAccounts/svcacc@gserviceaccount.com/keys/somehexstring',
        privateKeyData=b'service account key')
    self.StartObjectPatch(
        iam_util,
        'CreateServiceAccountKey',
        return_value=gsa_key)
    self.tracker = progress_tracker.StagedProgressTracker(
        None,
        stages.TriggerAndSourceStages(),
        suppress_output=True,
        aborted_message='aborted')

  def _MakeEventType(self,
                     source_kind,
                     source_plural,
                     type_='google.com.my.event.type',
                     description='desc'):
    """Creates a source CRD with an event type."""
    self.source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    self.source_crd.spec.names = self.crd_messages.CustomResourceDefinitionNames(
        kind=source_kind, plural=source_plural)
    self.event_type = custom_resource_definition.EventType(
        self.source_crd, type=type_, description=description)
    self.source_crd.event_types = [self.event_type]

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
    self.assertEqual(trigger_obj.Message(),
                     self.serverless_messages.Trigger(apiVersion='1'))

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

  def testCreateTrigger(self):
    """Test the create trigger api call."""
    source_obj = self._MakeSource(**{'metadata.name': 'source-for-my-trigger'})
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name': 'my-trigger',
            'metadata.annotations.additionalProperties': [{
                'key':
                    trigger.DEPENDENCY_ANNOTATION_FIELD,
                'value':
                    protojson.encode_message(source_obj.AsObjectReference())
            }],
            'spec.subscriber.ref': {
                'name': 'my-service',
                'kind': 'Service',
                'apiVersion': 'serving.knative.dev/v1alpha1'
            },
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }, {
                'key': trigger.EVENT_TYPE_FIELD,
                'value': 'google.com.my.event.type'
            }],
            'spec.broker': 'my-broker',
        })

    expected_request = (
        self.serverless_messages.RunNamespacesTriggersCreateRequest(
            trigger=trigger_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Create.Expect(
        expected_request, trigger_obj.Message())

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    created_trigger = self.eventflow_client.CreateTrigger(
        self._TriggerRef('my-trigger', 'default'),
        source_obj,
        self.event_type.type,
        'my-service',
        'my-broker',
    )
    self.assertEqual(trigger_obj, created_trigger)

  def testCreateTriggerDefaultBroker(self):
    """Test the create trigger api call."""
    source_obj = self._MakeSource(**{'metadata.name': 'source-for-my-trigger'})
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name': 'my-trigger',
            'metadata.annotations.additionalProperties': [{
                'key':
                    trigger.DEPENDENCY_ANNOTATION_FIELD,
                'value':
                    protojson.encode_message(source_obj.AsObjectReference())
            }, {
                'key': trigger._INJECTION_ANNOTATION_FIELD,
                'value': 'enabled'
            }],
            'spec.subscriber.ref': {
                'name': 'my-service',
                'kind': 'Service',
                'apiVersion': 'serving.knative.dev/v1alpha1'
            },
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }, {
                'key': trigger.EVENT_TYPE_FIELD,
                'value': 'google.com.my.event.type'
            }],
            'spec.broker': 'default',
        })

    expected_request = (
        self.serverless_messages.RunNamespacesTriggersCreateRequest(
            trigger=trigger_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Create.Expect(
        expected_request, trigger_obj.Message())

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    created_trigger = self.eventflow_client.CreateTrigger(
        self._TriggerRef('my-trigger', 'default'),
        source_obj,
        self.event_type.type,
        'my-service',
        'default',
    )
    self.assertEqual(trigger_obj, created_trigger)

  def testCreateTriggerFailsIfAlreadyExists(self):
    """Test the create trigger api call."""
    source_obj = self._MakeSource(**{'metadata.name': 'source-for-my-trigger'})
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name': 'my-trigger',
            'metadata.annotations.additionalProperties': [{
                'key':
                    trigger.DEPENDENCY_ANNOTATION_FIELD,
                'value':
                    protojson.encode_message(source_obj.AsObjectReference())
            }],
            'spec.subscriber.ref': {
                'name': 'my-service',
                'kind': 'Service',
                'apiVersion': 'serving.knative.dev/v1alpha1'
            },
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }, {
                'key': trigger.EVENT_TYPE_FIELD,
                'value': 'google.com.my.event.type'
            }],
            'spec.broker': 'my-broker',
        })

    expected_request = (
        self.serverless_messages.RunNamespacesTriggersCreateRequest(
            trigger=trigger_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_triggers.Create.Expect(
        expected_request,
        exception=api_exceptions.HttpConflictError(None, None, None))

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    with self.assertRaises(exceptions.TriggerCreationError):
      self.eventflow_client.CreateTrigger(
          self._TriggerRef('my-trigger', 'default'),
          source_obj,
          self.event_type.type,
          'my-service',
          'my-broker',
      )

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

    self.assertListEqual([t.Message() for t in triggers],
                         [self.serverless_messages.Trigger(apiVersion='1')])

  def testGetSource(self):
    """Test the get source api call."""
    source_ref = self._SourceRef('my-source', 'cloudpubsubsources')
    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesGetRequest(
            name=source_ref.RelativeName()))

    expected_response = self.serverless_messages.CloudPubSubSource(
        apiVersion='1')
    self.mock_serverless_client.namespaces_cloudpubsubsources.Get.Expect(
        expected_request, expected_response)

    source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='CloudPubSubSource', plural='cloudpubsubsources'))
    source_obj = self.eventflow_client.GetSource(source_ref, source_crd)
    self.assertEqual(source_obj.Message(),
                     self.serverless_messages.CloudPubSubSource(apiVersion='1'))

  def testGetSourceReturnsNoneIfNotFound(self):
    """Test the get source api call returns None if no source found."""
    source_ref = self._SourceRef('my-source', 'cloudpubsubsources')
    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesGetRequest(
            name=source_ref.RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Get.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='CloudPubSubSource', plural='cloudpubsubsources'))
    source_obj = self.eventflow_client.GetSource(source_ref, source_crd)
    self.assertIsNone(source_obj)

  def testCreateSource(self):
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name':
                'my-trigger',
            'metadata.uid':
                '123',
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
        })
    source_obj = self._MakeSource(
        'CloudPubSubSource', 'cloudpubsubsource.google.cloud.run', **{
            'metadata.name': 'source-for-my-trigger',
            'metadata.ownerReferences': [{
                'apiVersion': 'eventing.knative.dev/v1alpha1',
                'kind': 'Trigger',
                'name': 'my-trigger',
                'uid': '123',
                'controller': True
            }],
            'spec.ceOverrides.extensions.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
            'spec.sink.ref': {
                'name': 'my-broker',
                'kind': 'Broker',
                'apiVersion': 'eventing.knative.dev/v1alpha1'
            },
        })

    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesCreateRequest(
            cloudPubSubSource=source_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Create.Expect(
        expected_request, source_obj.Message())

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    created_source = self.eventflow_client.CreateSource(
        source_obj,
        self.source_crd,
        trigger_obj,
        self._NamespaceRef(project='default'),
        'my-broker',
        {},
    )
    self.assertEqual(source_obj, created_source)

  def testCreateSourceFailsIfAlreadyExists(self):
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name':
                'my-trigger',
            'metadata.uid':
                '123',
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
        })
    source_obj = self._MakeSource(
        'CloudPubSubSource', 'cloudpubsubsource.google.cloud.run', **{
            'metadata.name': 'source-for-my-trigger',
            'metadata.ownerReferences': [{
                'apiVersion': 'eventing.knative.dev/v1alpha1',
                'kind': 'Trigger',
                'name': 'my-trigger',
                'uid': '123',
                'controller': True
            }],
            'spec.ceOverrides.extensions.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
            'spec.sink.ref': {
                'name': 'my-broker',
                'kind': 'Broker',
                'apiVersion': 'eventing.knative.dev/v1alpha1'
            },
        })

    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesCreateRequest(
            cloudPubSubSource=source_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Create.Expect(
        expected_request,
        exception=api_exceptions.HttpConflictError(None, None, None))

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    with self.assertRaises(exceptions.SourceCreationError):
      self.eventflow_client.CreateSource(
          source_obj,
          self.source_crd,
          trigger_obj,
          self._NamespaceRef(project='default'),
          'my-broker',
          {},
      )

  def testCreateSourceWithParameters(self):
    trigger_obj = self._MakeTrigger(
        **{
            'metadata.name':
                'my-trigger',
            'metadata.uid':
                '123',
            'spec.filter.attributes.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
        })
    source_obj = self._MakeSource(
        'CloudPubSubSource', 'cloudpubsubsource.google.cloud.run', **{
            'metadata.name': 'source-for-my-trigger',
            'metadata.ownerReferences': [{
                'apiVersion': 'eventing.knative.dev/v1alpha1',
                'kind': 'Trigger',
                'name': 'my-trigger',
                'uid': '123',
                'controller': True
            }],
            'spec.ceOverrides.extensions.additionalProperties': [{
                'key': trigger.SOURCE_TRIGGER_LINK_FIELD,
                'value': 'link0'
            }],
            'spec.sink.ref': {
                'name': 'my-broker',
                'kind': 'Broker',
                'apiVersion': 'eventing.knative.dev/v1alpha1'
            },
            'spec.topic': 'my-topic',
            'spec.project': 'fake-project',
            'spec.secret': {
                'name': 'secret-name',
                'key': 'secret-key'
            }
        })

    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesCreateRequest(
            cloudPubSubSource=source_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Create.Expect(
        expected_request, source_obj.Message())

    self._MakeEventType('CloudPubSubSource', 'cloudpubsubsources')
    created_source = self.eventflow_client.CreateSource(
        source_obj,
        self.source_crd,
        trigger_obj,
        self._NamespaceRef(project='default'),
        'my-broker',
        {
            'topic': 'my-topic',
            'project': 'fake-project',
            'secret': {
                'name': 'secret-name',
                'key': 'secret-key'
            }
        },
    )
    self.assertEqual(source_obj, created_source)

  def testDeleteSource(self):
    """Test the delete source api call."""
    source_ref = self._SourceRef('my-source', 'cloudpubsubsources')
    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesDeleteRequest(
            name=source_ref.RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Delete.Expect(
        expected_request, self.serverless_messages.Empty())

    source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='CloudPubSubSource', plural='cloudpubsubsources'))

    self.eventflow_client.DeleteSource(source_ref, source_crd)

  def testDeleteSourceFailsIfNotFound(self):
    """Test the delete source api call raises an error if no source found."""
    source_ref = self._SourceRef('my-source', 'cloudpubsubsources')
    expected_request = (
        self.serverless_messages.RunNamespacesCloudpubsubsourcesDeleteRequest(
            name=source_ref.RelativeName()))

    self.mock_serverless_client.namespaces_cloudpubsubsources.Delete.Expect(
        expected_request,
        exception=api_exceptions.HttpNotFoundError(None, None, None))

    source_crd = (
        custom_resource_definition.SourceCustomResourceDefinition.New(
            self.mock_crd_client, 'fake-project'))
    source_crd.spec.names = (
        self.crd_messages.CustomResourceDefinitionNames(
            kind='CloudPubSubSource', plural='cloudpubsubsources'))

    with self.assertRaises(exceptions.SourceNotFound):
      self.eventflow_client.DeleteSource(source_ref, source_crd)

  def testListSourceCustomResourceDefinitions(self):
    """Test the list source CRDs api call."""
    expected_request = (
        self.crd_messages.RunCustomresourcedefinitionsListRequest(
            parent=self._NamespaceRef(project='fake-project').RelativeName(),
            labelSelector='duck.knative.dev/source=true'))

    crds = [
        self.crd_messages.CustomResourceDefinition(apiVersion='1')
        for _ in range(5)
    ]
    for crd in crds:
      arg_utils.SetFieldInMessage(crd, 'spec.names.kind', 'UnknownSourceKind')
    arg_utils.SetFieldInMessage(crds[0], 'spec.names.kind', 'CloudPubSubSource')

    expected_response = self.crd_messages.ListCustomResourceDefinitionsResponse(
        items=crds)
    self.mock_crd_client.customresourcedefinitions.List.Expect(
        expected_request, expected_response)

    source_crds = self.eventflow_client.ListSourceCustomResourceDefinitions()

    self.assertEqual(1, len(source_crds))
    self.assertEqual(source_crds[0].source_kind, 'CloudPubSubSource')

  def _MakeNamespace(self, **kwargs):
    namespace = self.core_messages.Namespace()
    arg_utils.ParseStaticFieldsIntoMessage(namespace, kwargs)
    return namespace

  def testUpdateNamespaceWithLabels(self):
    namespace = self._MakeNamespace(**{
        'metadata.labels.additionalProperties': [{
            'key': 'labelkey',
            'value': 'labelvalue'
        }]
    })

    expected_request = self.core_messages.RunApiV1NamespacesPatchRequest(
        name=self._CoreNamespaceRef('my-namespace').RelativeName(),
        namespace=namespace,
        updateMask='metadata.labels')

    self.mock_core_client.api_v1_namespaces.Patch.Expect(
        expected_request, self.core_messages.Namespace())

    self.eventflow_client.UpdateNamespaceWithLabels(
        self._CoreNamespaceRef('my-namespace'), {'labelkey': 'labelvalue'})

  def _MakeSecret(self, **kwargs):
    secret_obj = secret.Secret.New(self.mock_core_client, 'default')
    arg_utils.ParseStaticFieldsIntoMessage(secret_obj.Message(), kwargs)
    return secret_obj

  def testCreateOrReplaceServiceAccountSecret(self):
    secret_obj = self._MakeSecret(**{
        'metadata.name': 'mysecret',
        'data.additionalProperties': [{
            'key': 'key.json',
            'value': 'c2VydmljZSBhY2NvdW50IGtleQ=='
        }]
    })

    expected_request = (
        self.core_messages.RunApiV1NamespacesSecretsCreateRequest(
            secret=secret_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_core_client.api_v1_namespaces_secrets.Create.Expect(
        expected_request, secret_obj.Message())

    service_account_ref = self._registry.Parse(
        'svcacc@gserviceaccount.com',
        params={'projectsId': '-'},
        collection='iam.projects.serviceAccounts')
    self.eventflow_client.CreateOrReplaceServiceAccountSecret(
        self._SecretRef('mysecret', project='default'), service_account_ref)

  def testCreateOrReplaceServiceAccountSecretExistingSecret(self):
    secret_obj = self._MakeSecret(**{
        'metadata.name': 'mysecret',
        'data.additionalProperties': [{
            'key': 'key.json',
            'value': 'c2VydmljZSBhY2NvdW50IGtleQ=='
        }]
    })

    expected_create_request = (
        self.core_messages.RunApiV1NamespacesSecretsCreateRequest(
            secret=secret_obj.Message(),
            parent=self._NamespaceRef(project='default').RelativeName()))

    self.mock_core_client.api_v1_namespaces_secrets.Create.Expect(
        expected_create_request,
        exception=api_exceptions.HttpConflictError(None, None, None))

    secret_ref = self._SecretRef('mysecret', project='default')
    expected_replace_request = (
        self.core_messages.RunApiV1NamespacesSecretsReplaceSecretRequest(
            secret=secret_obj.Message(),
            name=secret_ref.RelativeName()))

    self.mock_core_client.api_v1_namespaces_secrets.ReplaceSecret.Expect(
        expected_replace_request, secret_obj.Message())

    service_account_ref = self._registry.Parse(
        'svcacc@gserviceaccount.com',
        params={'projectsId': '-'},
        collection='iam.projects.serviceAccounts')
    self.eventflow_client.CreateOrReplaceServiceAccountSecret(
        secret_ref, service_account_ref)

  def _MakeTrigger(self, **kwargs):
    """Creates a new trigger.Trigger.

    Args:
      **kwargs: fields on the underlying Trigger message mapped to the values
        they should be set to. Fields of arbitrary depth can be specified via
        dot-notation (e.g "metadata.name").

    Returns:
      trigger.Trigger whose underlying message has been modified with the given
        values.
    """
    trigger_obj = trigger.Trigger.New(self.mock_serverless_client, 'default')
    arg_utils.ParseStaticFieldsIntoMessage(trigger_obj.Message(), kwargs)
    return trigger_obj

  def _MakeSource(self,
                  kind='CloudPubSubSource',
                  api_category='sources.eventing.knative.dev',
                  **kwargs):
    """Creates a new source.Source.

    Args:
      kind: the Kind of source (e.g. CloudPubSubSource)
      api_category: the api group of the source (e.g. events.cloud.google.com)
      **kwargs: fields on the underlying Source message mapped to the values
        they should be set to. Fields of arbitrary depth can be specified via
        dot-notation (e.g "metadata.name").

    Returns:
      source.Source whose underlying message has been modified with the given
        values.
    """
    source_obj = source.Source.New(self.mock_serverless_client, 'default', kind,
                                   api_category)
    arg_utils.ParseStaticFieldsIntoMessage(source_obj.Message(), kwargs)
    return source_obj
