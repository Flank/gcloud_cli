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
"""Tests for tests.unit.command_lib.container.hub.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from apitools.base.py import exceptions as api_exceptions
from apitools.base.py.testing import mock as apimock
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.container.hub import api_adapter
from googlecloudsdk.command_lib.container.hub import util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from surface.container.hub import register_cluster
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util as test_util

import mock


class FakeKubernetesClient(object):
  """A test fake for the util.KubernetesClient class."""

  def __init__(self, labelled_namespaces=None):
    self.labelled_namespaces = labelled_namespaces

  def NamespacesWithLabelSelector(self, label):
    del label
    return self.labelled_namespaces


class GKEConnectNamespaceTest(sdk_test_base.SdkBase):

  def testGKEConnectNamespaceNeitherNamespaceLabelled(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=123)
    client = FakeKubernetesClient([])
    self.assertEqual('gke-connect',
                     util._GKEConnectNamespace(client, 'test-project'))

  def testGKEConnectNamespaceProjectNumberNamespaceExists(self):
    client = FakeKubernetesClient(['gke-connect-123'])
    self.assertEqual('gke-connect-123',
                     util._GKEConnectNamespace(client, 'test-project'))

  def testGKEConnectNamespaceNonProjectNumberNamespaceExists(self):
    client = FakeKubernetesClient(['gke-connect'])
    self.assertEqual('gke-connect',
                     util._GKEConnectNamespace(client, 'test-project'))

  def testGKEConnectNamespaceBothNamespacesExist(self):
    client = FakeKubernetesClient(['gke-connect', 'gke-connect-123'])
    with self.assertRaises(exceptions.Error):
      util._GKEConnectNamespace(client, 'test-project')


class DeployConnectAgentTest(sdk_test_base.WithFakeAuth,
                             cli_test_base.CliTestBase):

  def SetUp(self):
    self.mock_api_adapter = self.StartPatch(
        'googlecloudsdk.api_lib.container.hub.api_adapter.V1Beta1Adapter')()
    self.mock_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.KubernetesClient')()
    self.parser = test_util.ArgumentParser()
    register_cluster.RegisterCluster.Args(self.parser)
    self.registry = resources.Registry()

  def testSuccessfulAgentDeployment(self):
    properties.VALUES.core.project.Set('my-project')
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = None
    self.StartObjectPatch(api_adapter, 'InitAPIAdapter',
                          return_value = self.mock_api_adapter)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.mock_api_adapter.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]
    args = self.parser.parse_args(['my-membership', '--kubeconfig',
                                   '/tmp/kubeconfig', '--context', 'default',
                                   '--service-account-key-file',
                                   '/tmp/key.json'])
    util.DeployConnectAgent(args,
                            'some data',
                            'some other data',
                            'project/my-project/locations/global/memberships/my-membership')

class MembershipCRTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    processor_class_target = 'googlecloudsdk.command_lib.container.hub.util.KubeconfigProcessor'
    with mock.patch(
        processor_class_target, autospec=True, create=True) as mock_processor:
      mock_processor.return_value.GetKubeconfigAndContext.return_value = ('',
                                                                          '')
      self.client = util.KubernetesClient(None)
      self.mock_client = mock.create_autospec(
          util.KubernetesClient, instance=True)
      self.mock_client.GetMembershipOwnerID.side_effect = self.client.GetMembershipOwnerID
      self.client._RunKubectl = self.mock_client._RunKubectl
      self.client._MembershipCRDExists = self.mock_client._MembershipCRDExists

  def testValidMembershipOwnerID(self):
    self.mock_client._MembershipCRDExists.return_value = True
    self.mock_client._RunKubectl.return_value = ('projects/my-project', None)
    self.assertEqual(
        util.GetMembershipCROwnerID(self.mock_client), 'my-project')

  def testMissingMembershipCRD(self):
    self.mock_client._MembershipCRDExists.return_value = False
    self.assertEqual(util.GetMembershipCROwnerID(self.mock_client), None)

  def testMalformedMembershipOwnerID(self):
    self.mock_client._RunKubectl.return_value = ('invalid', None)
    with self.assertRaises(exceptions.Error):
      util.GetMembershipCROwnerID(self.mock_client)

  def testErrorGettingOwnerID(self):
    self.mock_client._RunKubectl.return_value = (None, 'unexpected error')
    with self.assertRaises(exceptions.Error):
      util.GetMembershipCROwnerID(self.mock_client)

  def testMissingMembership(self):
    self.mock_client._RunKubectl.return_value = (None, 'NotFound')
    self.assertEqual(None, util.GetMembershipCROwnerID(self.mock_client))


class DeploymentPodsAvailableOperationTest(sdk_test_base.SdkBase,
                                           parameterized.TestCase):

  def SetUp(self):
    self.mock_client = mock.create_autospec(
        util.KubernetesClient, instance=True)

  def testInit(self):
    d = util.DeploymentPodsAvailableOperation('namespace', 'test', 'testImage',
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
    d = util.DeploymentPodsAvailableOperation('namespace', 'test', 'testImage',
                                              self.mock_client)
    self.mock_client.GetResourceField.return_value = (
        None,
        'Error from server (NotFound): deployments.extensions "foo" not found')

    d.Update()

    self.assertFalse(d.done)
    self.assertFalse(d.succeeded)
    self.assertFalse(d.error)

  def testError(self):
    d = util.DeploymentPodsAvailableOperation('namespace', 'test', 'testImage',
                                              self.mock_client)
    self.mock_client.GetResourceField.return_value = (
        None, 'Error from server (SomethingIsWrong): something is wrong')

    d.Update()

    self.assertTrue(d.done)
    self.assertFalse(d.succeeded)
    self.assertTrue(d.error)

  def testDifferentImage(self):
    d = util.DeploymentPodsAvailableOperation('namespace', 'test', 'testImage',
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
    d = util.DeploymentPodsAvailableOperation('namespace', 'test', 'testImage',
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


class SubstringValidator(object):
  """Validates that a string contains another string as a substring."""

  def __init__(self, substring):
    self.substring = substring

  def __eq__(self, other):
    return self.substring in other


class GKEClusterSelfLinkTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.mock_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.KubernetesClient')()

    compute_api = 'compute'
    compute_api_version = core_apis.ResolveVersion(compute_api)
    self.compute_messages = core_apis.GetMessagesModule(compute_api,
                                                        compute_api_version)
    self.mock_compute_client = apimock.Client(
        client_class=core_apis.GetClientClass(compute_api, compute_api_version))
    self.mock_compute_client.Mock()
    self.addCleanup(self.mock_compute_client.Unmock)
    self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util._ComputeClient'
    ).return_value = self.mock_compute_client

  def testNoInstanceID(self):
    self.mock_kubernetes_client.GetResourceField.return_value = (None, None)
    self.assertIsNone(util.GKEClusterSelfLink({}))

    self.mock_kubernetes_client.GetResourceField.assert_has_calls([
        mock.call(
            mock.ANY, mock.ANY,
            SubstringValidator('container\\.googleapis\\.com/instance_id')),
    ])

    self.assertEqual(self.mock_kubernetes_client.GetResourceField.call_count, 1)

  def testErrorGettingInstanceID(self):
    self.mock_kubernetes_client.GetResourceField.return_value = (None, 'error')
    util.GKEClusterSelfLink({})

  def testNoProviderID(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (None, None),
    ]

    self_link = None
    with self.assertRaisesRegex(exceptions.Error, 'provider ID'):
      self_link = util.GKEClusterSelfLink({})
    self.assertIsNone(self_link)

    self.mock_kubernetes_client.GetResourceField.assert_has_calls([
        mock.call(
            mock.ANY, mock.ANY,
            SubstringValidator(
                'annotations.container\\.googleapis\\.com/instance_id')),
        mock.call(mock.ANY, mock.ANY, SubstringValidator('spec.providerID')),
    ])

    self.assertEqual(self.mock_kubernetes_client.GetResourceField.call_count, 2)

  def testErrorGettingProviderID(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (None, 'error'),
    ]
    with self.assertRaisesRegex(exceptions.Error, 'provider ID'):
      util.GKEClusterSelfLink({})

  @parameterized.parameters(
      'invalid',
      'gce:///bad',
      'gce://project',
      'gce://project/',
      'gce://project/location',
      'gce://project/location/',
  )
  def testErrorsParsingProviderID(self, provider_id):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        (provider_id, None),
    ]
    with self.assertRaisesRegex(exceptions.Error, 'parsing.*provider ID'):
      util.GKEClusterSelfLink({})

  def testComputeAPIError(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project_id/vm_zone/instance_id', None),
    ]

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project_id'),
        exception=api_exceptions.HttpError({'status': 404}, '', ''))

    self_link = None
    with self.assertRaises(api_exceptions.HttpError):
      self_link = util.GKEClusterSelfLink({})
    self.assertIsNone(self_link)

  def testInstanceWithoutMetadataFromComputeAPIRequest(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/vm-name', None),
    ]

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance())

    with self.assertRaisesRegex(exceptions.Error, 'empty metadata'):
      util.GKEClusterSelfLink({})

  def testInstanceWithoutClusterNameFromComputeAPIRequest(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(
                items=[item(key='foo', value='bar')])))

    with self.assertRaisesRegex(exceptions.Error, 'cluster name'):
      util.GKEClusterSelfLink({})

  def testInstanceWithoutClusterLocationFromComputeAPIRequest(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(items=[
                item(key='foo', value='bar'),
                item(key='cluster-name', value='cluster'),
            ])))

    with self.assertRaisesRegex(exceptions.Error, 'cluster location'):
      util.GKEClusterSelfLink({})

  def testGetSelfLink(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]

    item = self.compute_messages.Metadata.ItemsValueListEntry

    self.mock_compute_client.instances.Get.Expect(
        request=self.compute_messages.ComputeInstancesGetRequest(
            instance='instance_id', zone='vm_zone', project='project-id'),
        response=self.compute_messages.Instance(
            metadata=self.compute_messages.Metadata(items=[
                item(key='foo', value='bar'),
                item(key='cluster-name', value='cluster'),
                item(key='cluster-location', value='location'),
            ])))

    self.assertEqual(
        util.GKEClusterSelfLink({}),
        '//container.googleapis.com/projects/project-id/locations/location/clusters/cluster'
    )


if __name__ == '__main__':
  test_case.main()
