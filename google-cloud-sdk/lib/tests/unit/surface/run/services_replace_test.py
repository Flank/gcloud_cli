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
"""Unit tests for the `run services update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import messages_util
from tests.lib import parameterized
from tests.lib.surface.run import base

import mock


class ReplaceTestAlpha(base.ServerlessSurfaceBase, parameterized.TestCase):
  """Tests `services replace` command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.operations.messages_module = self.serverless_messages
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.Project())
    self.service.name = 'my-service'
    self.service.domain = 'https://foo-bar.baz'
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status_traffic.SetPercent('rev.1', 100)
    self.service.spec_traffic.SetPercent('rev.1', 100)
    self.operations.GetService.return_value = self.service
    self.operations.ReleaseService.return_value = None
    self.StartObjectPatch(messages_util, 'GetStartDeployMessage')
    self.StartObjectPatch(messages_util,
                          'GetSuccessMessageForSynchronousDeploy')
    self.StartObjectPatch(projects_util, 'GetProjectNumber', return_value=123)
    self._MockConnectionContext()

  def _MakeFile(self, yaml_data):
    return self.Touch(
        self.temp_path, 'test.yaml', contents=yaml_data, makedirs=True)

  def testWithFormat(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    serv = self.Run('run services replace {} --format=yaml'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='fake-project'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)
    self.assertIsNotNone(serv)
    self.AssertOutputContains('apiVersion: serving.knative.dev/v1')
    self.AssertOutputContains('kind: Service')
    self.AssertOutputContains('url: https://foo-bar.baz')

  def testNoNamespaceSpecifiedManaged(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {}'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='fake-project'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testNoNamespaceSpecifiedAnthos(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {} --platform=gke'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='default'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testMetadataNamespaceSpecifiedManaged(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: fake-project
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {}'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='fake-project'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testMetadataNamespaceNumericSpecifiedManaged(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: '123'
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {}'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='123'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testMetadataNamespaceSpecifiedManagedDoesntMatchProject(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: wrong-project
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    with self.assertRaises(exceptions.ConfigurationError):
      self.Run('run services replace {}'.format(filename))

  def testMetadataNamespaceSpecifiedAnthos(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: mynamespace
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {} --platform=gke'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='mynamespace'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testNamespaceFlagSpecifiedAnthos(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {} --namespace=mynamespace '
             '--platform=gke'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='mynamespace'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testBothNamespaceSpecifiedAnthos(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: mynamespace
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    self.Run('run services replace {} --namespace=mynamespace '
             '--platform=gke'.format(filename))
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service', project='mynamespace'),
        mock.ANY,
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        for_replace=True)

  def testBothNamespaceSpecifiedAnthosMismatch(self):
    yaml_data = """
    apiVersion: serving.knative.dev/v1alpha1
    kind: Service
    metadata:
      name: my-service
      namespace: mynamespace1
    spec:
      template:
        spec:
          containers:
          - image: gcr.io/my-image
    """
    filename = self._MakeFile(yaml_data)
    with self.assertRaises(exceptions.ConfigurationError):
      self.Run('run services replace {} --namespace=mynamespace2 '
               '--platform=gke'.format(filename))
