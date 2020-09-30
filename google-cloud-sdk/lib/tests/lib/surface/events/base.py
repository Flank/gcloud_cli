# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Base class for Events unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.events import eventflow_operations
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

import mock

MANAGED_EVENTS_CRD_API_VERSION = 'v1beta1'

ANTHOS_API_NAME = 'anthosevents'
ANTHOS_API_VERSION = 'v1beta1'

# API version used for working with CRDs.
ANTHOS_CRD_API_VERSION = 'v1'

# API name and version for CloudRun operator
_OPERATOR_API_NAME = 'anthosevents'
_OPERATOR_API_VERSION = 'v1alpha1'


class EventsBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for Events unit tests."""

  # Subclasses may change the values of these fields in PreSetUp().
  # This is the main API name and version for the test class. They are used
  # everywhere except when working with core resources (Anthos only) or CRDs.
  # For now, the only supported values are ALPHA_API_NAME/VERSION,
  # EVENTS_API_NAME/VERSION, and ANTHOS_API_NAME/VERSION.
  api_name = ANTHOS_API_NAME
  api_version = ANTHOS_API_VERSION
  platform = 'gke'
  region = 'us-central1'

  # API name and version used by Anthos for working with core resources.
  core_api_name = 'run'
  core_api_version = 'v1'

  def _NamespaceRef(self, project='fake-project'):
    collection = '{}.namespaces'.format(self.api_name)
    return self._registry.Parse(
        project, collection=collection, api_version=self.api_version)

  def _CoreNamespaceRef(self, project='fake-project'):
    """This method is for Anthos only."""
    collection = '{}.api.{}.namespaces'.format(self.core_api_name,
                                               self.core_api_version)
    return self._registry.Parse(
        project, collection=collection, api_version=self.core_api_version)

  def _TriggerRef(self, name, project='fake-project'):
    collection = '{}.namespaces.triggers'.format(self.api_name)
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection=collection,
        api_version=self.api_version)

  def _SourceRef(self, name, plural_kind, project='fake-project'):
    collection = '{}.namespaces.{}'.format(self.api_name, plural_kind)
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection=collection,
        api_version=self.api_version)

  def _SecretRef(self, name, project='fake-project'):
    """This method is for Anthos only."""
    collection = '{}.api.{}.namespaces.secrets'.format(self.core_api_name,
                                                       self.core_api_version)
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection=collection,
        api_version=self.core_api_version)

  def _MockConnectionContext(self, is_gke_context):
    """Causes GetConnectionContext() to return a mock connection context.

    Args:
      is_gke_context: bool, specifies whether or not the connection context
        should be for GKE.
    """
    context = mock.Mock()
    context.__enter__ = mock.Mock(return_value=context)
    context.__exit__ = mock.Mock(return_value=False)
    if is_gke_context:
      context.supports_one_platform = False
      context.endpoint = 'https://kubernetes.default/'
    else:
      context.supports_one_platform = True
      context.endpoint = 'https://{}-{}.googleapis.com/'.format(
          self.region, self.api_name)
    self.StartObjectPatch(
        connection_context, 'GetConnectionContext', return_value=context)

  def _SpecParameterAdditionalProperty(self, name, var_type, description):
    value = self.crd_messages.JSONSchemaProps(
        type=var_type, description=description)
    return self.crd_messages.JSONSchemaProps.PropertiesValue.AdditionalProperty(
        key=name, value=value)

  def _SourceSchemaProperties(self, spec_properties, required_properties):
    """Returns the schema for a source CRD.

    Args:
      spec_properties: list(JSONSchemaProps.PropertiesValue.AdditionalProperty),
        properties to specify in the schema spec.
      required_properties: list(str), names of spec_properties to mark as
        required.

    Returns:
      JSONSchemaProps for the source CRD's openAPIV3Schema.
    """
    spec_properties = [] if spec_properties is None else spec_properties
    required_properties = ([] if required_properties is None else
                           required_properties)
    return self.crd_messages.JSONSchemaProps(
        properties=self.crd_messages.JSONSchemaProps.PropertiesValue(
            additionalProperties=[
                self.crd_messages.JSONSchemaProps.PropertiesValue
                .AdditionalProperty(
                    key='spec',
                    value=self.crd_messages.JSONSchemaProps(
                        required=required_properties,
                        properties=self.crd_messages.JSONSchemaProps.
                        PropertiesValue(additionalProperties=spec_properties))),
            ]))

  def _CreateMockClient(self, api_name, api_version, mock_client_hash):
    """Returns apitools_mock.Client.

    Checks mock_client_hash for pre-existing mock clients to reuse.
    Args:
      api_name: str, API name
      api_version: str, API version
      mock_client_hash: dict, contains previous mock clients
    """
    try:
      return mock_client_hash[(api_name, api_version)]
    except KeyError:
      pass

    client_class = apis.GetClientClass(api_name, api_version)
    real_client = apis.GetClientInstance(api_name, api_version, no_http=True)
    mock_client = apitools_mock.Client(client_class, real_client)
    mock_client.Mock()
    self.addCleanup(mock_client.Unmock)

    mock_client_hash[(api_name, api_version)] = mock_client
    return mock_client

  def SetUp(self):
    """Runs before any test method to set up the test environment."""
    properties.VALUES.run.platform.Set(self.platform)
    properties.VALUES.run.region.Set(self.region)

    self._registry = resources.REGISTRY.Clone()
    self.is_interactive = self.StartObjectPatch(
        console_io, 'IsInteractive', return_value=True)
    self.namespace = self._NamespaceRef()

    if self.api_name == 'anthosevents':
      crd_version = ANTHOS_CRD_API_VERSION
    else:
      crd_version = MANAGED_EVENTS_CRD_API_VERSION

    self.messages = apis.GetMessagesModule(self.api_name, self.api_version)
    self.crd_messages = apis.GetMessagesModule(self.api_name, crd_version)
    self.core_messages = apis.GetMessagesModule(self.core_api_name,
                                                self.core_api_version)
    self.operator_messages = apis.GetMessagesModule(self.api_name,
                                                    _OPERATOR_API_VERSION)

    # Dict holding duplicate mock clients with (api_name, api_version) as key
    mock_client_hash = {}

    # Create mock clients.
    self.mock_client = self._CreateMockClient(self.api_name, self.api_version,
                                              mock_client_hash)
    self.mock_crd_client = self._CreateMockClient(self.api_name, crd_version,
                                                  mock_client_hash)
    self.mock_core_client = self._CreateMockClient(self.core_api_name,
                                                   self.core_api_version,
                                                   mock_client_hash)
    self.mock_operator_client = self._CreateMockClient(_OPERATOR_API_NAME,
                                                       _OPERATOR_API_VERSION,
                                                       mock_client_hash)

    self.operations = mock.Mock()
    if self.api_name == 'anthosevents':
      self.operations.IsCluster.return_value = True
    else:
      self.operations.IsCluster.return_value = False
    self.operations.client = self.mock_client
    self.operations.messages = self.messages
    self.operations.api_name = self.api_name
    self.operations.api_version = self.api_version

    operations_context = mock.Mock()
    operations_context.__enter__ = mock.Mock(return_value=self.operations)
    operations_context.__exit__ = mock.Mock(return_value=False)
    self.StartObjectPatch(
        eventflow_operations, 'Connect', return_value=operations_context)
