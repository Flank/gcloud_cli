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
from __future__ import unicode_literals

import itertools
from apitools.base.py.testing import mock as apitools_mock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
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


class ServerlessSurfaceBase(cli_test_base.CliTestBase):
  """Base class for Serverless surface tests."""

  def _ServiceRef(self, name, region='us-central1', project='fake-project'):
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection='serverless.namespaces.services')

  def _NamespaceRef(self, region='us-central1', project='fake-project'):
    return self._registry.Parse(project, collection='serverless.namespaces')

  def _RevisionRef(self, name, region='us-central1', project='fake-project'):
    return self._registry.Parse(
        name,
        params={'namespacesId': project},
        collection='serverless.namespaces.revisions')

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self._registry = resources.REGISTRY.Clone()
    properties.VALUES.run.region.Set('us-central1')
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
        'serverless', 'v1alpha1')
    self.mock_serverless_client._VERSION = 'v1alpha1'  # pylint: disable=protected-access
    self.mock_serverless_client.MESSAGES_MODULE = self.serverless_messages
    self.operations.GetActiveRevisions.return_value = {'rev.1': 100}


class ServerlessBase(ServerlessSurfaceBase):
  """Base class for Google Serverless Engine unit tests."""

  def SetUp(self):
    # Mock ServerlessApiClient
    self.client_class = core_apis.GetClientClass('serverless', 'v1alpha1')
    self.real_client = core_apis.GetClientInstance(
        'serverless', 'v1alpha1', no_http=True)
    self.mock_serverless_client = apitools_mock.Client(
        self.client_class, self.real_client)

    self.mock_serverless_client.Mock()
    self.addCleanup(self.mock_serverless_client.Unmock)
