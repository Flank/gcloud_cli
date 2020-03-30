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
# Lint as: python3
"""Tests for google3.third_party.py.tests.unit.command_lib.container.hub.agent_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.hub import gkehub_api_adapter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.hub import agent_util
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from surface.container.hub.memberships import register
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util as test_util

import mock


class DeployConnectAgentTest(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_api_adapter = self.StartPatch(
        'googlecloudsdk.api_lib.container.hub.gkehub_api_adapter.APIAdapter')()
    self.mock_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.KubernetesClient')()
    self.mock_old_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.OldKubernetesClient'
    )()
    self.parser = test_util.ArgumentParser()
    register.Register.Args(self.parser)
    self.registry = resources.Registry()

  def testSuccessfulAgentDeploymentBeta(self):
    properties.VALUES.core.project.Set('my-project')
    self.mock_kubernetes_client.Apply.return_value = ('some output', None)
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = None
    self.StartObjectPatch(gkehub_api_adapter, 'InitAPIAdapter',
                          return_value=self.mock_api_adapter)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    args = self.parser.parse_args([
        'my-membership', '--kubeconfig', '/tmp/kubeconfig', '--context',
        'default', '--service-account-key-file', '/tmp/key.json'
    ])
    agent_util.DeployConnectAgent(
        self.mock_kubernetes_client, args,
        'some data', 'some other data',
        'project/my-project/locations/global/memberships/my-membership',
        calliope_base.ReleaseTrack.BETA)

  def testSuccessfulAgentDeploymentGA(self):
    properties.VALUES.core.project.Set('my-project')
    self.mock_kubernetes_client.Apply.return_value = ('some output', None)
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = None
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        api_util,
        'GenerateConnectAgentManifest')

    args = self.parser.parse_args([
        'my-membership', '--kubeconfig', '/tmp/kubeconfig', '--context',
        'default', '--service-account-key-file', '/tmp/key.json'
    ])
    agent_util.DeployConnectAgent(
        self.mock_kubernetes_client, args,
        'some data', 'some other data',
        'project/my-project/locations/global/memberships/my-membership',
        calliope_base.ReleaseTrack.GA)

  def testSuccessfulAgentDeploymentWithOldKubernetesClient(self):
    properties.VALUES.core.project.Set('my-project')
    self.mock_old_kubernetes_client.Apply.return_value = ('some output', None)
    self.mock_old_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_old_kubernetes_client.Delete.return_value = None
    self.mock_old_kubernetes_client.NamespaceExists.return_value = False
    self.mock_old_kubernetes_client.NamespacesWithLabelSelector.return_value = None
    self.StartObjectPatch(gkehub_api_adapter, 'InitAPIAdapter',
                          return_value=self.mock_api_adapter)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.mock_api_adapter.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]
    args = self.parser.parse_args([
        'my-membership', '--kubeconfig', '/tmp/kubeconfig', '--context',
        'default', '--service-account-key-file', '/tmp/key.json'
    ])
    agent_util.DeployConnectAgent(
        self.mock_old_kubernetes_client, args,
        'some data', 'some other data',
        'project/my-project/locations/global/memberships/my-membership',
        calliope_base.ReleaseTrack.BETA)


class DeploymentPodsAvailableOperationTest(sdk_test_base.SdkBase,
                                           parameterized.TestCase):

  def SetUp(self):
    self.mock_client = mock.create_autospec(
        kube_util.KubernetesClient, instance=True)

  def testInit(self):
    d = kube_util.DeploymentPodsAvailableOperation('namespace', 'test',
                                                   'testImage',
                                                   self.mock_client)
    self.assertEqual(d.namespace, 'namespace')
    self.assertEqual(d.deployment_name, 'test')
    self.assertEqual(d.image, 'testImage')
    self.assertEqual(d.kube_client, self.mock_client)

    self.mock_client.GetResourceField.assert_not_called()

    self.assertFalse(d.done)
    self.assertFalse(d.succeeded)
    self.assertFalse(d.error)

  def testNotFoundError(self):
    d = kube_util.DeploymentPodsAvailableOperation('namespace', 'test',
                                                   'testImage',
                                                   self.mock_client)
    self.mock_client.GetResourceField.return_value = (
        None,
        'Error from server (NotFound): deployments.extensions "foo" not found')

    d.Update()

    self.assertFalse(d.done)
    self.assertFalse(d.succeeded)
    self.assertFalse(d.error)

  def testError(self):
    d = kube_util.DeploymentPodsAvailableOperation('namespace', 'test',
                                                   'testImage',
                                                   self.mock_client)
    self.mock_client.GetResourceField.return_value = (
        None, 'Error from server (SomethingIsWrong): something is wrong')

    d.Update()

    self.assertTrue(d.done)
    self.assertFalse(d.succeeded)
    self.assertTrue(d.error)

  def testDifferentImage(self):
    d = kube_util.DeploymentPodsAvailableOperation('namespace', 'test',
                                                   'testImage',
                                                   self.mock_client)
    self.mock_client.GetResourceField.return_value = ('differentImage', None)

    d.Update()

    self.assertFalse(d.done)
    self.assertFalse(d.succeeded)
    self.assertFalse(d.error)

  @parameterized.parameters(
      (1, 1, 1, 0, False),
      (1, 2, 1, 1, False),
      (1, 1, 0, 1, False),
      (1, 1, 1, 1, True),
  )
  def testReplicaCounts(self, spec_replicas, status_replicas,
                        available_replicas, updated_replicas,
                        done_and_succeeded):
    d = kube_util.DeploymentPodsAvailableOperation('namespace', 'test',
                                                   'testImage',
                                                   self.mock_client)
    self.mock_client.GetResourceField.side_effect = [
        ('testImage', None),
        (spec_replicas, None),
        (status_replicas, None),
        (available_replicas, None),
        (updated_replicas, None),
    ]

    d.Update()
    self.mock_client.GetResourceField.assert_has_calls([
        mock.call('namespace', 'deployment/test',
                  '.spec.template.spec.containers[0].image'),
        mock.call('namespace', 'deployment/test', '.spec.replicas'),
        mock.call('namespace', 'deployment/test', '.status.replicas'),
        mock.call('namespace', 'deployment/test', '.status.availableReplicas'),
        mock.call('namespace', 'deployment/test', '.status.updatedReplicas')
    ])

    self.assertEqual(d.done, done_and_succeeded)
    self.assertEqual(d.succeeded, done_and_succeeded)
    self.assertFalse(d.error)


if __name__ == '__main__':
  test_case.main()


