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
"""Tests for the 'hub register-cluster' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.hub import util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

TEST_CONTAINER_IMAGE = 'gcr.io/test/test'


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


def _GetResourceFieldSideEffect(namespace, resource, json_path):
  """Implements a side_effect for a mock of KubernetesClient.GetResourceField().

  Args:
    namespace: The namespace
    resource: the resource, in the format <resourceType>/<name>; e.g.,
      'configmap/foo'
    json_path: the JSONPath expression to filter with

  Returns:
    The mocked field value
  """
  del namespace, resource

  # This method on KubernetesClient is currently only called by
  # DeploymentPodsAvailableOperation, which uses it to check the container
  # image and the replica counts in the object's status.

  # If the JSONPath expression is for the container image, return the image
  # used in the tests.
  if json_path == '.spec.template.spec.containers[0].image':
    return TEST_CONTAINER_IMAGE, None

  # Otherwise, return a replica count of 1 across the board, which represents
  # an up-to-date steady state.
  return '1', None


class RegisterTestBeta(cli_test_base.CliTestBase,
                       sdk_test_base.WithFakeAuth):
  """Tests the logic in the Register class.

  These tests are not meant to test the business logic in
  command_lib/container/hub/util.py, but only that the RegisterCluster logic is
  correctly interacting with it.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.kubeconfig = TestDataFile('kubeconfig')
    self.serviceaccount_file = TestDataFile('service_account.json')
    self.docker_credential_file = TestDataFile('docker_credential.json')
    self.mock_kubernetes_client = self.MockOutKubernetesClient()
    self.mock_api_adatper = self.MockOutApiAdapter()
    self.mock_gke_cluster_self_link = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.GKEClusterSelfLink')

  def RunCommand(self, params):
    """Runs the 'register' command with the provided params.

    Args:
      params: A list of parameters to pass to the 'register' command.

    Returns:
      The results of self.Run() with the provided params.

    Raises:
      Any exception raised by self.Run()
    """
    prefix = ['container', 'memberships', 'register']
    return self.Run(prefix + params)

  def MockOutKubernetesClient(self):
    return self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.KubernetesClient')()

  def MockOutApiAdapter(self):
    return self.StartPatch(
        'googlecloudsdk.api_lib.container.hub.api_adapter.V1Beta1Adapter')()

  def testWithoutArgs(self):
    with self.AssertRaisesArgumentErrorMatches('CLUSTER_NAME'):
      self.RunCommand([])

  def testMissingContextFlag(self):
    with self.AssertRaisesArgumentErrorMatches('context'):
      self.RunCommand(['my-cluster', '--service-account-key-file=/key.json'])

  def testMissingServiceAccountKeyFileFlag(self):
    with self.AssertRaisesArgumentErrorMatches('service-account-key-file'):
      self.RunCommand(['my-cluster', '--context=test-context'])

  def testInvalidServiceAccountKeyFile(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)

    with self.AssertRaisesExceptionMatches(Exception,
                                           'service-account-key-file'):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=bad'
          '--project=fake-project',
      ])

  def testInvalidDockerServiceAccountKeyFile(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)

    with self.AssertRaisesExceptionMatches(Exception, 'docker-credential-file'):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
          '--docker-credential-file=bad',
          '--project=fake-project',
      ])

  def testEmptyProjectFlag(self):
    with self.AssertRaisesExceptionMatches(Exception, 'project'):
      self.RunCommand([
          'my-cluster', '--context=test-context', '--project=',
          '--service-account-key-file=bad'
      ])

  def testGKEClusterSelfLinkRaises(self):
    self.mock_gke_cluster_self_link.side_effect = Exception('self link')
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)

    with self.AssertRaisesExceptionMatches(Exception, 'self link'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testListMembershipsNotFound(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    mock_list_memberships = self.StartObjectPatch(util, 'ProjectForClusterUUID')
    mock_list_memberships.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    with self.AssertRaisesExceptionMatches(Exception, 'Could not access'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipConfictNotAlreadyExists(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'CONFLICT'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)

    with self.AssertRaisesExceptionMatches(calliope_exceptions.HttpException,
                                           'CONFLICT'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipAlreadyExistsWithDifferentName(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-other-cluster')

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'conflicts with'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipAlreadyExistsWithSameName(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')

    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           ''):
      self.WriteInput('N')
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipWithClusterLink(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_gke_cluster_self_link.return_value = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_create_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    # The GKE cluster selflink is passed into the membership resource that is
    # created. this test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with(
        'fake-project', 'fake-uid', 'my-cluster',
        '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    )

  def testFailedAgentDeployment(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.Apply.return_value = 'Error applying manifest'
    self.mock_api_adatper.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]

    self.StartObjectPatch(
        util, 'UserAccessibleProjectIDSet', return_value={'fake-project'})
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(exceptions.Error, ''):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
      ])
      mock_delete_membership.assert_called_with(
          'projects/fake-project/locations/global/memberships/fake-uid')
      mock_delete_membership_resource.assert_called_once()

  def successfulMockSetup(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_api_adatper.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

  def testSuccessfulAgentDeployment(self):
    self.successfulMockSetup()
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

  def testSuccessfulAgentDeploymentWithProxy(self):
    self.successfulMockSetup()
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--proxy=https://proxy.com:8080'
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

  def testSuccessfulAgentDeploymentWithEncodedProxy(self):
    self.successfulMockSetup()
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--proxy=aHR0cHM6Ly8xMjM0LmNvbTo4MDgw'
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

  def testSuccessfulAgentDeploymentWithPrivateRegistry(self):
    self.successfulMockSetup()
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')
    # TODO(b/139814516): remove this.
    self.StartObjectPatch(util, 'DeployConnectAgentAlpha', return_value=None)
    self.RunCommand([
        'my-cluster',
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--docker-registry=myprivateregistry.com',
        '--docker-credential-file=' + self.docker_credential_file,
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

  def testSuccessfulAgentUpgradeWithProjectNumberNamespace(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect'
    ]
    self.mock_api_adatper.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.StartObjectPatch(p_util, 'GetProjectNumber')
    self.StartObjectPatch(util, '_DeleteNamespaceForReinstall')

    # The prompt is for membership deletion.
    self.WriteInput('Y')
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--project=fake-project',
    ])
    # DeleteMembership should only be called for cancellations/failures if
    # this invocation caused a membership to be created.
    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    # The Connect namespace should be searched for by its label.
    self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')

    manifest_yaml_call_arg = self.mock_kubernetes_client.Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertNotIn('namespace: gke-connect-12321', manifest_yaml_call_arg[0])
    self.assertIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithNonProjectNumberNamespace(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect'
    ]
    self.mock_api_adatper.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    self.StartObjectPatch(util, '_DeleteNamespaceForReinstall')
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    apply_membership_resources = self.StartObjectPatch(
        util, 'ApplyMembershipResources')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    self.WriteInput('Y')
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--project=fake-project',
    ])
    # DeleteMembership should only be called for cancellations/failures if
    # this invocation caused a membership to be created.
    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

    # The Connect namespace should be searched for by its label.
    self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')

    # This was a successful registration; make sure we created the Membership
    # resources.
    apply_membership_resources.assert_called_once()

    # If the connect namespace does not have a project number, that should be
    # reflected in the generated manifest.
    manifest_yaml_call_arg = self.mock_kubernetes_client.Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])
    self.assertNotIn('namespace: gke-connect-12321\n',
                     manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithMultipleConnectNamespaces(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect',
        'gke-connect-2',
    ]
    self.mock_api_adatper.GenerateConnectAgentManifest.return_value = [
        {'manifest': 'some content'},
    ]

    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='fake-project')
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        util, 'DeleteMembershipResources')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'Multiple'):
      self.WriteInput('Y')
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
          '--project=fake-project',
      ])

      mock_delete_membership.assert_called_once()
      mock_delete_membership_resource.assert_called_once()

      # If the membership already exists, then the existence of the namespace
      # should not be verified.
      self.mock_kubernetes_client.NamespaceExists.assert_not_called()

      # The Connect namespace should be searched for by its label.
      self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
          'hub.gke.io/project=fake-project')

  def testCreateDifferentMembershipOwnerID(self):
    self.mock_kubernetes_client = self.MockOutKubernetesClient()
    self.StartObjectPatch(
        util, 'GetMembershipCROwnerID', return_value='fake-project')
    self.StartObjectPatch(
        util,
        'UserAccessibleProjectIDSet',
        return_value={'fake-project', 'other-project'})

    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'already registered'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=my-project',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateExistingMembershipOtherProject(self):
    self.StartObjectPatch(util, 'GetClusterUUID', return_value='fake-uid')
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util, 'UserAccessibleProjectIDSet', return_value={'my-project'})
    self.StartObjectPatch(
        util, 'ProjectForClusterUUID', return_value='other-project')
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')

    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'already registered'):
      self.WriteInput('Y')
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=my-project',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

      mock_create_membership.assert_not_called()

      # If the membership already exists, then the existence of the namespace
      # should not be verified.
      self.mock_kubernetes_client.NamespaceExists.assert_not_called()

      # The Connect namespace should be searched for by its label.
      self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
          'hub.gke.io/project=fake-project')

  def testCreateWithUnauthorizedProject(self):
    self.StartObjectPatch(util, 'GetClusterUUID', return_value='fake-uid')
    self.StartObjectPatch(util, 'GetMembershipCROwnerID', return_value=None)
    self.StartObjectPatch(
        util, 'UserAccessibleProjectIDSet', return_value={'other-project'})
    self.StartObjectPatch(util, 'ProjectForClusterUUID', return_value=None)
    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'not authorized'):
      self.WriteInput('Y')
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

      mock_create_membership.assert_not_called()

      # If the membership already exists, then the existence of the namespace
      # should not be verified.
      self.mock_kubernetes_client.NamespaceExists.assert_not_called()

      # The Connect namespace should be searched for by its label.
      self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
          'hub.gke.io/project=fake-project')


class RegisterTestAlpha(RegisterTestBeta):
  """gcloud Alpha track using GKE Hub v1 API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

if __name__ == '__main__':
  test_case.main()
# LINT.ThenChange(../hub/register_cluster_test.py)
