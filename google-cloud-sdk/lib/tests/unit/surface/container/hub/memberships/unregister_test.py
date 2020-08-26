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
"""Tests for the 'memberships unregister' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.hub import agent_util
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.hub.memberships import base

TEST_BUCKET_ISSUER_URL = 'https://storage.googleapis.com/gke-issuer-0'


def TestDataFile(*args):
  """Returns an SdkBase.Resource for a file from the test data directory.

  Args:
    *args: A list of path components to append to the base test data directory.

  Returns:
    An SdkBase.Resource for the file.
  """
  return sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'container',
                                        'hub', 'testdata', *args)


class UnregisterTest(base.MembershipsTestBase):
  """gcolud GA track using GKE Hub API.

  These tests are not meant to test the business logic in
  command_lib/container/hub/util.py, but only that the UnregisterCluster logic
  is correctly interacting with it.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.kubeconfig = TestDataFile('kubeconfig')
    self.mock_kubernetes_client = self.MockOutKubernetesClient()

  def RunCommand(self, params):
    """Runs the 'unregister' command with the provided params.

    Args:
      params: A list of parameters to pass to the 'unregister' command.

    Returns:
      The results of self.Run() with the provided params.

    Raises:
      Any exception raised by self.Run()
    """
    prefix = ['container', 'hub', 'memberships', 'unregister']
    return self.Run(prefix + params)

  def MockOutKubernetesClient(self):
    return self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.KubernetesClient')()

  def testWithoutArgs(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--gke-cluster | --gke-uri |'
        ' [--context : --kubeconfig]) must be specified'):
      self.RunCommand([])

  def testMissingClusterIdentifierFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--gke-cluster | --gke-uri |'
        ' [--context : --kubeconfig]) must be specified'):
      self.RunCommand(['my-cluster'])

  def testMultipleClusterIdentifierFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--gke-cluster | --gke-uri |'
        ' [--context : --kubeconfig]) must be specified'):
      self.RunCommand(
          ['my-cluster',
           '--gke-uri=my-gke-uri',
           '--gke-cluster=my-gke-cluster'])

  def testMissingContextFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'gument --kubeconfig: --context must be specified.'):
      self.RunCommand(
          ['my-cluster',
           '--kubeconfig=' + self.kubeconfig,
          ])

  def testEmptyProjectFlag(self):
    self.MockOutKubernetesClient()
    with self.AssertRaisesExceptionMatches(Exception, 'project'):
      self.RunCommand(['my-cluster', '--context=test-context', '--project='])

  def testSuccessfulUnregistrationWithContext(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True

    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithLocationGKEUri(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--gke-uri=https://container.googleapis.com/v1/projects/project/locations/location/clusters/cluster'
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithZonalGKEUri(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--gke-uri=https://container.googleapis.com/projects/project/zones/zone/clusters/cluster',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithRegionalGKEUri(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--gke-uri=https://container.googleapis.com/projects/project/regions/region/clusters/cluster',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithGKECluster(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--gke-cluster=location/cluster',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testUnregistrationWithoutMembership(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None, None)
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_once()
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithoutMembershipResource(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value=None)
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithoutKubeconfigFlag(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value='fake-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--context=test-context',
        '--project=fake-project',
    ])

    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithDifferentMembershipOwner(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.StartObjectPatch(api_util, 'DeleteMembership')
    self.StartObjectPatch(exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util,
        'GetMembershipCROwnerID',
        return_value='other-project')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])


class UnregisterTestBeta(UnregisterTest):
  """gcolud Beta track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UnregisterTestAlpha(UnregisterTestBeta):
  """gcolud Alpha track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDeleteWIMembershipContextManageBucket(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value=None)

    self.mock_kubernetes_client.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_BUCKET_ISSUER_URL})
    mock_delete_bucket = self.StartObjectPatch(
        api_util, 'DeleteWorkloadIdentityBucket')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()

    self.RunCommand([
        'my-cluster', '--kubeconfig=' + self.kubeconfig,
        '--context=test-context', '--project=fake-project',
        '--manage-workload-identity-bucket',
    ])

    self.mock_kubernetes_client.GetOpenIDConfiguration.assert_called_once_with()
    mock_delete_bucket.assert_called_once_with(TEST_BUCKET_ISSUER_URL)

    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testDeleteWIMembershipContextManageBucketDiscoveryException(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value=None)

    self.mock_kubernetes_client.GetOpenIDConfiguration.side_effect = exceptions.Error(
        'Oops!')
    mock_delete_bucket = self.StartObjectPatch(
        api_util, 'DeleteWorkloadIdentityBucket')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()

    # Test that the command works and only bucket deletion is skipped.
    self.RunCommand([
        'my-cluster', '--kubeconfig=' + self.kubeconfig,
        '--context=test-context', '--project=fake-project',
        '--manage-workload-identity-bucket',
    ])

    self.mock_kubernetes_client.GetOpenIDConfiguration.assert_called_once_with()
    mock_delete_bucket.assert_not_called()

    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

  def testDeleteWIMembershipContextManageBucketDeleteException(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        agent_util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        exclusivity_util, 'GetMembershipCROwnerID', return_value=None)

    self.mock_kubernetes_client.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_BUCKET_ISSUER_URL})
    mock_delete_bucket = self.StartObjectPatch(
        api_util, 'DeleteWorkloadIdentityBucket')
    mock_delete_bucket.side_effect = exceptions.Error('Oops!')
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(
        description='my-cluster', external_id='fake-uid')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()

    # Test that the command works and only bucket deletion is skipped.
    self.RunCommand([
        'my-cluster', '--kubeconfig=' + self.kubeconfig,
        '--context=test-context', '--project=fake-project',
        '--manage-workload-identity-bucket',
    ])

    self.mock_kubernetes_client.GetOpenIDConfiguration.assert_called_once_with()
    mock_delete_bucket.assert_called_with(TEST_BUCKET_ISSUER_URL)

    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/my-cluster',
        self.track)
    mock_delete_membership_resource.assert_called_once()

if __name__ == '__main__':
  test_case.main()
