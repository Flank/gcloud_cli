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
"""Tests for the 'hub unregister-cluster' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.hub import util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


# LINT.IfChange
def TestDataFile(*args):
  """Returns an SdkBase.Resource for a file from the test data directory.

  Args:
    *args: A list of path components to append to the base test data directory.

  Returns:
    An SdkBase.Resource for the file.
  """
  return sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'container',
                                        'hub', 'testdata', *args)


class UnregisterTestBeta(cli_test_base.CliTestBase,
                         sdk_test_base.WithFakeAuth):
  """Tests the logic in the UnregisterCluster class.

  These tests are not meant to test the business logic in
  command_lib/container/hub/util.py, but only that the UnregisterCluster logic
  is correctly interacting with it.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

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
    prefix = ['container', 'memberships', 'unregister']
    return self.Run(prefix + params)

  def MockOutKubernetesClient(self):
    return self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.KubernetesClient')()

  def testWithoutArgs(self):
    with self.AssertRaisesArgumentErrorMatches('context'):
      self.RunCommand([])

  def testEmptyProjectFlag(self):
    self.MockOutKubernetesClient()
    with self.AssertRaisesExceptionMatches(Exception, 'project'):
      self.RunCommand(['--context=test-context', '--project='])

  def testSuccessfulUnregistration(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='fake-project')
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.RunCommand([
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/fake-uid')
    mock_delete_membership_resource.assert_called_once()

  def testUnregistrationWithoutMembership(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None, None)
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='fake-project')
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    self.RunCommand([
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_not_called()
    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithoutMembershipResource(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    self.RunCommand([
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--project=fake-project',
    ])
    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/fake-uid')
    mock_delete_membership_resource.assert_called_once()

  def testSuccessfulUnregistrationWithoutKubeconfigFlag(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='fake-project')
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    self.RunCommand([
        '--context=test-context',
        '--project=fake-project',
    ])

    mock_delete_connect_namespace.assert_called_once()
    mock_delete_membership.assert_called_with(
        'projects/fake-project/locations/global/memberships/fake-uid')
    mock_delete_membership_resource.assert_called_once()

  def testUnsuccessfulUnregistrationWithDifferentMembershipOwner(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='other-project')
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'registered to another'):
      self.RunCommand([
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--project=fake-project',
      ])
      mock_delete_connect_namespace.assert_not_called()
      mock_delete_membership.assert_not_called()
      mock_delete_membership_resource.assert_not_called()

  def testUnsuccessfulUnregistrationWithExistingMembership(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'ProjectForClusterUUID',
        return_value={'fake-uid': 'other-project'})
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'registered to another'):
      self.RunCommand([
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--project=fake-project',
      ])
      mock_delete_connect_namespace.assert_not_called()
      mock_delete_membership.assert_not_called()
      mock_delete_membership_resource.assert_not_called()

  def testUnsuccessfulUnregistrationWithUnauthorizedProject(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.DeleteNamespace.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    mock_delete_connect_namespace = self.StartObjectPatch(
        util, 'DeleteConnectNamespace')
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='other-project')
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    self.StartObjectPatch(
        util, 'UserAccessibleProjectIDSet', return_value={'fake-project'})

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'not authorized'):
      self.RunCommand([
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--project=fake-project',
      ])
      mock_delete_connect_namespace.assert_not_called()
      mock_delete_membership.assert_not_called()
      mock_delete_membership_resource.assert_not_called()


class UnregisterTestAlpha(UnregisterTestBeta):
  """gcolud Alpha track using GKE Hub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
# LINT.ThenChange(../hub/unregister_cluster_test.py)
