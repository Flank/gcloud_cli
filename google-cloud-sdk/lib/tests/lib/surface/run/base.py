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
"""Base class for Google Serverless Engine unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import itertools
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
import mock

ENV_FLAGS = ['--update-env-vars', '--set-env-vars',
             '--remove-env-vars', '--clear-env-vars']
# All env var-related flags are mutually exclusive, except update and remove.
INVALID_ENV_FLAG_PAIRS = set(itertools.combinations(ENV_FLAGS, 2))
INVALID_ENV_FLAG_PAIRS.discard(('--remove-env-vars', '--update-env-vars'))
INVALID_ENV_FLAG_PAIRS.discard(('--update-env-vars', '--remove-env-vars'))
INVALID_ENV_FLAG_PAIRS = list(INVALID_ENV_FLAG_PAIRS)


DEFAULT_REGION = 'us-central1'

_API_NAME = 'run'


class ServerlessSurfaceBase(cli_test_base.CliTestBase):
  """Base class for Serverless surface tests."""

  def _ServiceRef(self, name, region=DEFAULT_REGION, project='fake-project'):
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection='run.namespaces.services')

  def _NamespaceRef(self, region=DEFAULT_REGION, project='fake-project'):
    ret = self._registry.Parse(project, collection='run.namespaces')
    return ret

  def _RevisionRef(self, name, project='fake-project'):
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection='run.namespaces.revisions')

  def _DomainmappingRef(self, name, project='fake-project'):
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection='run.namespaces.domainmappings')

  def _MockConnectionContext(self):
    self.connection_context = mock.Mock()
    self.connection_context.__enter__ = mock.Mock(return_value=self)
    self.connection_context.__exit__ = mock.Mock(return_value=False)
    self.connection_context.endpoint = 'https://{}-run.googleapis.com/'.format(
        DEFAULT_REGION)
    self.StartObjectPatch(
        connection_context,
        'GetConnectionContext',
        return_value=self.connection_context)

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._registry = resources.REGISTRY.Clone()
    properties.VALUES.run.region.Set(DEFAULT_REGION)
    self.namespace = self._NamespaceRef()
    self.operations = mock.Mock()
    self.operations_context = mock.Mock()
    self.operations_context.__enter__ = mock.Mock(return_value=self.operations)
    self.operations_context.__exit__ = mock.Mock(return_value=False)
    self.factory = self.StartObjectPatch(serverless_operations, 'Connect',
                                         return_value=self.operations_context)
    self.is_interactive = self.StartObjectPatch(
        console_io, 'IsInteractive', return_value=True)

    self.mock_serverless_client = mock.Mock()
    self.serverless_messages = core_apis.GetMessagesModule(
        _API_NAME, 'v1alpha1')
    self.mock_serverless_client._VERSION = 'v1alpha1'  # pylint: disable=protected-access
    self.mock_serverless_client.MESSAGES_MODULE = self.serverless_messages
    self.operations.GetActiveRevisions.return_value = {'rev.1': 100}


class ServerlessBase(ServerlessSurfaceBase):
  """Base class for Google Serverless Engine unit tests."""

  def SetUp(self):
    # Mock ServerlessApiClient
    self.client_class = core_apis.GetClientClass(_API_NAME, 'v1alpha1')
    self.real_client = core_apis.GetClientInstance(
        _API_NAME, 'v1alpha1', no_http=True)
    self.mock_serverless_client = apitools_mock.Client(
        self.client_class, self.real_client)
    self.mock_serverless_client.Mock()
    self.addCleanup(self.mock_serverless_client.Unmock)

    # apitools_mock has trouble mocking the same API client twice, so
    # mock_serverless_client must be used for both `client` and `op_client`.
    # This doesn't cause a problem because the only difference between the two
    # is the api_endpoint_overrides parameter at time of initialization, which
    # is immaterial to unit tests.
    self.serverless_client = (
        serverless_operations.ServerlessOperations(
            client=self.mock_serverless_client,
            api_name='run',
            api_version='v1alpha1',
            region='us-central1',
            op_client=self.mock_serverless_client))

    # Convenience attributes for IAM policy testing.
    self.etag = b'my-etag'
    self.b64etag = base64.b64encode(self.etag).decode('utf-8')
    self.service_format = ('projects/fake-project/locations/'
                           '{region}/services/{service}')
    self.service = self.service_format.format(service='my-service',
                                              region=DEFAULT_REGION)
    self.my_binding = self.serverless_messages.Binding(
        members=['user:my-account@gmail.com'], role='roles/my-role')
    self.next_binding = self.serverless_messages.Binding(
        members=['user:next@gmail.com'], role='roles/next')
    self.other_binding = self.serverless_messages.Binding(
        members=['user:other-account@gmail.com'], role='roles/other-role')

  def _ExpectGetIamPolicy(self, service_name=None, bindings=None):
    if service_name:
      expected_service = self.service_format.format(
          region=DEFAULT_REGION, service=service_name)
    else:
      expected_service = self.service
    expected = (
        self.serverless_messages
        .RunProjectsLocationsServicesGetIamPolicyRequest(
            resource=expected_service))

    if bindings is None:
      expected_bindings = [self.my_binding, self.next_binding]
    else:
      expected_bindings = bindings

    response = self.serverless_messages.Policy(
        bindings=expected_bindings,
        etag=b'my-etag')
    self.mock_serverless_client.projects_locations_services.GetIamPolicy.Expect(
        expected, response=response)

  def _ExpectSetIamPolicy(
      self, service=None, bindings=None, update_mask=None, exception=None):
    """Expect a SetIamPolicy request with given bindings and updateMask.

    Args:
      service: str, The name of the service to expect to be updated.
      bindings: [Binding], List of policy bindings to expect.
      update_mask: str, The updateMask to expect.
      exception: Exception, Exception causing failure.

    """
    if service:
      expected_service = self.service_format.format(
          region=DEFAULT_REGION, service=service)
    else:
      expected_service = self.service
    response = None
    if exception is None:
      response = self.serverless_messages.Policy(
          bindings=bindings,
          etag=self.etag)
    self.mock_serverless_client.projects_locations_services.SetIamPolicy.Expect(
        self.serverless_messages
        .RunProjectsLocationsServicesSetIamPolicyRequest(
            resource=expected_service,
            setIamPolicyRequest=self.serverless_messages.SetIamPolicyRequest(
                policy=self.serverless_messages.Policy(
                    bindings=bindings,
                    etag=self.etag),
                updateMask=update_mask)),
        response=response,
        exception=exception)
