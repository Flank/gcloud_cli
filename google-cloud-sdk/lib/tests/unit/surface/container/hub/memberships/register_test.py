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
"""Tests for the 'memberships register' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.hub import gkehub_api_adapter
from googlecloudsdk.api_lib.container.hub import gkehub_api_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.hub import agent_util
from googlecloudsdk.command_lib.container.hub import api_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.hub.memberships import base


TEST_CONTAINER_IMAGE = 'gcr.io/test/test'
TEST_UID = 'fake-uid'
TEST_ISSUER_URL = 'https://issuer.example.com/v1'
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


class RegisterTest(base.MembershipsTestBase):
  """gcloud GA track using GKE Hub API.

  These tests are not meant to test the business logic in
  command_lib/container/hub/util.py, but only that the RegisterCluster logic is
  correctly interacting with it.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.kubeconfig = TestDataFile('kubeconfig')
    self.serviceaccount_file = TestDataFile('service_account.json')
    self.docker_credential_file = TestDataFile('docker_credential.json')
    self.mock_kubernetes_client = self.MockOutKubernetesClient()
    # TODO(b/145955278): Use release_track to select the right Exclusivity API.
    self.exclusivity_msg = core_apis.GetMessagesModule(
        self.MODULE_NAME, gkehub_api_util.GKEHUB_BETA_API_VERSION)

  def RunCommand(self, params):
    """Runs the 'register' command with the provided params.

    Args:
      params: A list of parameters to pass to the 'register' command.

    Returns:
      The results of self.Run() with the provided params.

    Raises:
      Any exception raised by self.Run()
    """
    prefix = ['container', 'hub', 'memberships', 'register']
    return self.Run(prefix + params)

  def MockOutKubernetesClient(self):
    return self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.KubernetesClient')()

  def MockOutGenerateConnectAgentManifestSucceed(self):
    # Based on the API version, use api_adapter if GenerateConnectAgentManifest
    # is a nested message, else use default the api_client.
    # note: the response type is different for both the interfaces.
    # TODO(b/148312097): Re-visit following condition when we update alpha_api.
    if self.api_version in ['v1beta1']:
      return self.StartObjectPatch(
          gkehub_api_adapter.APIAdapter,
          'GenerateConnectAgentManifest',
          return_value=[{
              'manifest': 'some content'
          }])
    messages = core_apis.GetMessagesModule(self.MODULE_NAME, self.api_version)
    return self.StartObjectPatch(
        api_util,
        'GenerateConnectAgentManifest',
        return_value=messages.GenerateConnectManifestResponse())

  def MockOutGenerateConnectAgentManifestError(self):
    # Based on the API version, use api_adapter if GenerateConnectAgentManifest
    # is a nested message, else use default api_client.
    # note: the response type is different for both the interfaces.
    if self.api_version in ['v1beta1']:
      mock_get_manifest_api = self.StartObjectPatch(
          gkehub_api_adapter.APIAdapter, 'GenerateConnectAgentManifest')
    else:
      mock_get_manifest_api = self.StartObjectPatch(
          api_util, 'GenerateConnectAgentManifest')
    # Mock GenerateConnectAgentManifest to give error
    mock_get_manifest_api.side_effect = apitools_exceptions.Error(
        None, None, None)

  def MockOutCreateMembershipNotFound(self):
    # Mock GetMembership and membership not found.
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    mock_get_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    # Mock CreateMembership and it gives back NotFoundError.
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_create_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)
    return mock_create_membership

  def MockOutCreateMembershipNew(self):
    name = 'projects/fake-project/locations/global/memberships/my-cluster'
    description = 'my-cluster'
    # Mock GetMembership and membership not found.
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    mock_get_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    # Mock CreateMembership and it successfully created a membership.
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    membership = self._MakeMembership(name=name, description=description)
    mock_create_membership.return_value = membership
    return mock_create_membership

  def MockOutCreateMembershipAlreadyExists(self):
    name = 'projects/fake-project/locations/global/memberships/my-cluster'
    description = 'my-cluster'
    # Mock GetMembership for:
    # On first call, membership is not found.
    # On second call, membership is found.
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(name=name,
                                      description=description,
                                      external_id=TEST_UID)
    membership_not_found_return_value = apitools_exceptions.HttpNotFoundError(
        None, None, None)
    membership_found_return_value = membership
    mock_get_membership.side_effect = [
        membership_not_found_return_value, membership_found_return_value
    ]

    # Mock CreateMembership and membership already exists.
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_create_membership.return_value = membership
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    return mock_create_membership

  def mockValidateExclusivitySucceed(self):
    mock_validate_exclusivity = self.StartObjectPatch(api_util,
                                                      'ValidateExclusivity')
    mock_validate_exclusivity.return_value = self.exclusivity_msg.ValidateExclusivityResponse(
        status=self.exclusivity_msg.GoogleRpcStatus(code=0))
    mock_generate_exclusivity_manifest = self.StartObjectPatch(
        api_util, 'GenerateExclusivityManifest')
    mock_generate_exclusivity_manifest.return_value = self.exclusivity_msg.GenerateExclusivityManifestResponse(
        crManifest='cr manifest', crdManifest='crd manifest')

  def testMissingClusterIdentifierFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--gke-cluster | --gke-uri |'
        ' [--context : --kubeconfig]) must be specified'):
      self.RunCommand(
          ['my-cluster',
           '--service-account-key-file=' + self.serviceaccount_file])

  def testMultipleClusterIdentifierFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--gke-cluster | --gke-uri |'
        ' [--context : --kubeconfig]) must be specified'):
      self.RunCommand(
          ['my-cluster',
           '--gke-uri=my-gke-uri',
           '--gke-cluster=my-gke-cluster',
           '--service-account-key-file=' + self.serviceaccount_file])

  def testMissingContextFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'gument --kubeconfig: --context must be specified.'):
      self.RunCommand(
          ['my-cluster',
           '--kubeconfig=' + self.kubeconfig,
           '--service-account-key-file=' + self.serviceaccount_file])

  def testMissingServiceAccountKeyFileFlag(self):
    with self.AssertRaisesArgumentErrorMatches('service-account-key-file'):
      self.RunCommand(['my-cluster', '--context=test-context'])

  def testInvalidServiceAccountKeyFile(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

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
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

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

  def testGetMembershipNotFound(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    mock_get_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    # Mock CreateMembership and raise exception.
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_create_membership.side_effect = Exception('create membership')
    self.mockValidateExclusivitySucceed()

    with self.AssertRaisesExceptionMatches(Exception, 'create membership'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testGetMembershipAlreadyExistsSameDescription(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.StartObjectPatch(api_util, 'ProjectForClusterUUID', return_value=None)
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(description='my-cluster')
    mock_get_membership.return_value = membership
    with self.assertRaises(console_io.OperationCancelledError):
      self.WriteInput('N')
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testGetMembershipAlreadyExistsDifferentDescription(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership = self._MakeMembership(description='my-other-cluster')
    mock_get_membership.return_value = membership
    self.mockValidateExclusivitySucceed()

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'conflicts with'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipConfictNotAlreadyExists(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    # Mock GetMembership for two subsequent calls:
    # On first call: membership is not found.
    # On second call: membership is found.
    mock_get_membership = self.StartObjectPatch(api_util, 'GetMembership')
    membership_not_found_return_value = \
        apitools_exceptions.HttpNotFoundError(None, None, None)
    membership = self._MakeMembership(description='my-cluster')
    membership_found_return_value = membership
    mock_get_membership.side_effect = [
        membership_not_found_return_value, membership_found_return_value
    ]
    self.mockValidateExclusivitySucceed()

    # Mock CreateMembership and get a conflict.
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
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

  def testCreateMembershipAlreadyExists(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    # Setup Mock to create an existing membership.
    self.MockOutCreateMembershipAlreadyExists()
    self.mockValidateExclusivitySucceed()

    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           ''):
      self.WriteInput('N')
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipFailed(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    self.StartObjectPatch(kube_util, 'IsGKECluster', return_value=False)
    self.mockValidateExclusivitySucceed()
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    mock_deploy_connect = self.StartObjectPatch(
        agent_util, 'DeployConnectAgent', return_value=None)
    with self.assertRaises(calliope_exceptions.HttpException):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with('fake-project', 'my-cluster',
                                                   'my-cluster', None,
                                                   TEST_UID, self.track, None)
    mock_deploy_connect.assert_not_called()

  def testCreateMembershipWithClusterLink(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    self.StartObjectPatch(kube_util, 'IsGKECluster', return_value=False)
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()

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

    mock_create_membership.assert_called_once_with('fake-project', 'my-cluster',
                                                   'my-cluster',
                                                   '//container.googleapis.com/projects/project/locations/location/clusters/cluster',  # pylint: disable=line-too-long
                                                   TEST_UID, self.track, None)

  def testCreateMembershipWithExternalID(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.mockValidateExclusivitySucceed()

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()

    # This test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with('fake-project', 'my-cluster',
                                                   'my-cluster', None,
                                                   TEST_UID, self.track, None)

  def testGenerateConnectAgentManifestError(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.NamespaceExists.return_value = False
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)

    self.mockValidateExclusivitySucceed()

    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')

    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    # Mock to error in GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestError()
    with self.AssertRaisesExceptionMatches(exceptions.Error, ''):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
      ])
      mock_create_membership.assert_called_once()
      mock_delete_membership.assert_called_with(
          'projects/fake-project/locations/global/memberships/my-cluster')
      mock_delete_membership_resource.assert_called_once()

  def testGenerateConnectAgentManifestFile(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.__enter__.return_value.NamespaceExists.return_value = False
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)

    self.mockValidateExclusivitySucceed()

    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(kube_util, 'IsGKECluster', return_value=False)
    mock_delete_namespace = self.StartObjectPatch(
        kube_util, 'DeleteNamespace')
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()

    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
          '--manifest-output-file=fake-file.yaml'
      ])

    mock_create_membership.assert_called_once()
    mock_delete_namespace.assert_not_called()
    mock_delete_membership.assert_not_called()
    mock_delete_membership_resource.assert_not_called()

  def testFailedAgentDeployment(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.NamespaceExists.return_value = False
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = \
        'Error applying manifest'

    self.mockValidateExclusivitySucceed()

    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(exceptions.Error, ''):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig=' + self.kubeconfig,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
      ])
      mock_create_membership.assert_called_once()
      mock_delete_membership.assert_called_with(
          'projects/fake-project/locations/global/memberships/my-cluster')
      mock_delete_membership_resource.assert_called_once()

  def successfulMockSetup(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.NamespaceExists.return_value = False
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)
    self.mock_kubernetes_client.__enter__.return_value.Logs.return_value = (
        'Fake log', None)
    self.mock_kubernetes_client.__enter__.return_value.Delete.return_value = None
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.mock_delete_membership = self.StartObjectPatch(api_util,
                                                        'DeleteMembership')
    self.mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')

    # Mock to create a new membership.
    self.mock_create_membership = self.MockOutCreateMembershipNew()
    self.mockValidateExclusivitySucceed()

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

  def assertSuccessfulExecution(self):
    self.mock_create_membership.assert_called_once()
    self.mock_delete_membership.assert_not_called()
    self.mock_delete_membership_resource.assert_not_called()

  def testSuccessfulAgentDeployment(self):
    self.successfulMockSetup()
    # Mock the GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()
    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    self.assertSuccessfulExecution()

  def testSuccessfulAgentDeploymentWithProxy(self):
    self.successfulMockSetup()
    # Mock to GenerateConnectAgentManifest.
    mock_generate_manifest = self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--proxy=https://proxy.com:8080'
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    self.assertSuccessfulExecution()
    if self.api_version != 'v1beta1':
      mock_generate_manifest.assert_called_once_with(
          'projects/fake-project/locations/global/memberships/my-cluster',
          image_pull_secret_content=None,
          is_upgrade=False,
          namespace='gke-connect',
          proxy='https://proxy.com:8080',
          registry=None,
          version=None,
          release_track=self.track)

  def testSuccessfulAgentDeploymentWithEncodedProxy(self):
    self.successfulMockSetup()
    # Mock to GenerateConnectAgentManifest.
    mock_generate_manifest = self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--proxy=aHR0cHM6Ly8xMjM0LmNvbTo4MDgw'
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    self.assertSuccessfulExecution()
    # TODO(b/148312097): If needed, update this check when we enable alpha_api.
    if self.api_version != 'v1beta1':
      mock_generate_manifest.assert_called_once_with(
          'projects/fake-project/locations/global/memberships/my-cluster',
          image_pull_secret_content=None,
          is_upgrade=False,
          namespace='gke-connect',
          proxy='aHR0cHM6Ly8xMjM0LmNvbTo4MDgw',
          registry=None,
          version=None,
          release_track=self.track)

  def testSuccessfulAgentDeploymentWithSpecificConnectVersion(self):
    self.successfulMockSetup()
    # Mock to GenerateConnectAgentManifest.
    mock_generate_manifest = self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster', '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--version=my-connect-agent-version'
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    self.assertSuccessfulExecution()
    # TODO(b/148312097): If needed, update this check when we enable alpha_api.
    if self.api_version != 'v1beta1':
      mock_generate_manifest.assert_called_once_with(
          'projects/fake-project/locations/global/memberships/my-cluster',
          image_pull_secret_content=None,
          is_upgrade=False,
          namespace='gke-connect',
          proxy=None,
          registry=None,
          version='my-connect-agent-version',
          release_track=self.track)

  def testSuccessfulAgentDeploymentWithPrivateRegistry(self):
    self.successfulMockSetup()
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster',
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--docker-registry=myprivateregistry.com',
        '--docker-credential-file=' + self.docker_credential_file,
    ])
    # This was a successful registration; make sure we created the Membership
    # resources.
    self.assertSuccessfulExecution()

  def testSuccessfulAgentUpgradeWithProjectNumberNamespace(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)
    self.mock_kubernetes_client.__enter__.return_value.Logs.return_value = (
        'Fake log', None)
    self.mock_kubernetes_client.__enter__.return_value.Delete.return_value = None
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = [
        'gke-connect'
    ]

    # Setup Mock to create an existing membership.
    self.MockOutCreateMembershipAlreadyExists()
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.mockValidateExclusivitySucceed()
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()

    self.StartObjectPatch(p_util, 'GetProjectNumber')
    self.StartObjectPatch(kube_util, 'DeleteNamespace')

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

    # The Connect namespace should be searched for by its label.
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')

    manifest_yaml_call_arg = self.mock_kubernetes_client.__enter__.return_value.\
        Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertNotIn('namespace: gke-connect-12321', manifest_yaml_call_arg[0])
    self.assertIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithNonProjectNumberNamespace(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)
    self.mock_kubernetes_client.__enter__.return_value.Logs.return_value = (
        'Fake log', None)
    self.mock_kubernetes_client.__enter__.return_value.Delete.return_value = None
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = [
        'gke-connect'
    ]

    self.StartObjectPatch(kube_util, 'DeleteNamespace')

    # Setup Mock to create an existing membership.
    self.MockOutCreateMembershipAlreadyExists()
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.mockValidateExclusivitySucceed()
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()
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
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')

    # If the connect namespace does not have a project number, that should be
    # reflected in the generated manifest.
    manifest_yaml_call_arg = self.mock_kubernetes_client.__enter__.return_value.\
        Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])
    self.assertNotIn('namespace: gke-connect-12321\n',
                     manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithMultipleConnectNamespaces(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.GetResourceField.side_effect = _GetResourceFieldSideEffect
    self.mock_kubernetes_client.__enter__.return_value.Apply.return_value = (
        'some output', None)
    self.mock_kubernetes_client.__enter__.return_value.Logs.return_value = (
        'Fake log', None)
    self.mock_kubernetes_client.__enter__.return_value.Delete.return_value = None
    self.mock_kubernetes_client.__enter__.return_value.NamespacesWithLabelSelector.return_value = [
        'gke-connect',
        'gke-connect-2',
    ]

    # Setup Mock to create an existing membership.
    self.MockOutCreateMembershipAlreadyExists()
    mock_delete_membership = self.StartObjectPatch(api_util, 'DeleteMembership')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_delete_membership_resource = self.StartObjectPatch(
        exclusivity_util, 'DeleteMembershipResources')
    self.mockValidateExclusivitySucceed()
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()
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
    self.MockOutCreateMembershipAlreadyExists()
    mock_validate_exclusivity = self.StartObjectPatch(api_util,
                                                      'ValidateExclusivity')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    mock_validate_exclusivity.return_value = self.exclusivity_msg.ValidateExclusivityResponse(
        status=self.exclusivity_msg.GoogleRpcStatus(code=6))
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Error validating cluster'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=my-project',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateExistingMembershipOtherProject(self):
    self.StartObjectPatch(kube_util, 'GetClusterUUID', return_value=TEST_UID)

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    mock_create_membership = self.StartObjectPatch(api_util, 'CreateMembership')
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)
    self.StartObjectPatch(api_util, 'ValidateExclusivity').return_value(
        self.exclusivity_msg.ValidateExclusivityResponse(
            status=self.exclusivity_msg.GoogleRpcStatus(code=6)))

    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Error validating cluster'):
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

  def testCreateMembershipWithLocationGKEUri(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)

    # The GKE cluster selflink is passed into the membership resource that is
    # created. this test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster',
          '--gke-uri=https://container.googleapis.com/v1/projects/project/locations/location/clusters/cluster',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        '//container.googleapis.com/projects/project/locations/location/clusters/cluster',
        TEST_UID, self.track, None
    )

  def testCreateMembershipWithZonalGKEUri(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)

    # The GKE cluster selflink is passed into the membership resource that is
    # created. this test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster',
          '--gke-uri=https://container.googleapis.com/v1/projects/project/zones/zone/clusters/cluster',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        '//container.googleapis.com/projects/project/locations/location/clusters/cluster',
        TEST_UID, self.track, None
    )

  def testCreateMembershipWithRegionalGKEUri(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/regions/region/clusters/cluster'
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)

    # The GKE cluster selflink is passed into the membership resource that is
    # created. this test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster',
          '--gke-uri=https://container.googleapis.com/v1/projects/project/regions/region/clusters/cluster',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        '//container.googleapis.com/projects/project/regions/region/clusters/cluster',
        TEST_UID, self.track, None
    )

  def testCreateMembershipWithContext(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

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
        'fake-project', 'my-cluster', 'my-cluster',
        None,
        TEST_UID, self.track, None
    )

  def testCreateMembershipWithGKECluster(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)

    # The GKE cluster selflink is passed into the membership resource that is
    # created. this test is not concerned about exceptions thrown during the
    # command, only that the parameters that CreateMembership() is called with
    # are valid.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster',
          '--gke-cluster=location/cluster',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        '//container.googleapis.com/projects/project/locations/location/clusters/cluster',
        'fake-uid', self.track, None
    )

  def testExclusivityInstallation(self):
    # A new cluster without existing exclusivity artifacts.
    self.successfulMockSetup()
    self.mock_kubernetes_client.GetMembershipCRD.return_value = ''
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
    ])

    self.assertSuccessfulExecution()

  def testExclusivityUpgradeCRD(self):
    # A registered cluster with valid exclusivity in an older version.
    self.successfulMockSetup()
    self.mock_kubernetes_client.GetMembershipCRD.return_value = 'crd_manifest'
    # Mock to GenerateConnectAgentManifest.
    self.MockOutGenerateConnectAgentManifestSucceed()

    self.RunCommand([
        'my-cluster',
        '--kubeconfig=' + self.kubeconfig,
        '--context=test-context',
        '--service-account-key-file=' + self.serviceaccount_file,
    ])

    self.assertSuccessfulExecution()

  def testRegisterWithDifferentUID(self):
    # Register a cluster with the same cluster name (membership_id)
    # but different cluster UID.
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = 'another-uid'
    self.StartObjectPatch(kube_util, 'IsGKECluster', return_value=False)
    self.mockValidateExclusivitySucceed()
    self.MockOutCreateMembershipAlreadyExists()

    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=my-project',
          '--service-account-key-file=' + self.serviceaccount_file
      ])


class RegisterTestBeta(RegisterTest):
  """gcloud Beta track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class RegisterTestAlpha(RegisterTestBeta):
  """gcloud Alpha track using GKE Hub API."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testNoServiceAccountKeyFileFlagWithWI(self):
    with self.AssertRaisesArgumentErrorMatches('service-account-key-file'):
      self.RunCommand([
          'my-cluster',
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
          '--enable-workload-identity'])

  def testCreateWIMembershipContext(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_ISSUER_URL})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        )  # The linter prefers a hanging paren due to above line length.

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        None,
        TEST_UID, self.track, TEST_ISSUER_URL
    )

  def testCreateWIMembershipContextManageBucket(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_BUCKET_ISSUER_URL})
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDKeyset.return_value = json.dumps(
        {'keys': [{'alg': 'RSA256'}]})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None

    mock_create_bucket = self.StartObjectPatch(
        api_util, 'CreateWorkloadIdentityBucket')

    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
          '--manage-workload-identity-bucket',
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        )  # The linter prefers a hanging paren due to above line length.

    mock_create_bucket.assert_called_once_with(
        'fake-project', TEST_BUCKET_ISSUER_URL,
        json.dumps({'issuer': TEST_BUCKET_ISSUER_URL}),
        json.dumps({'keys': [{'alg': 'RSA256'}]}))

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        None,
        TEST_UID, self.track, TEST_BUCKET_ISSUER_URL
    )

  def testCreateWIMembershipPublicIssuer(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_ISSUER_URL})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
          '--public-issuer-url=' + TEST_ISSUER_URL
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        issuer_url=TEST_ISSUER_URL)

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        None,
        TEST_UID, self.track, TEST_ISSUER_URL
    )

  def testCreateWIMembershipGKEPublicIssuer(self):
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': TEST_ISSUER_URL})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = '//container.googleapis.com/projects/project/locations/location/clusters/cluster'
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=True)

    # The GKE cluster selflink is passed into the membership resource that is
    # created.
    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaises(Exception):
      self.RunCommand([
          'my-cluster',
          '--gke-cluster=location/cluster',
          '--enable-workload-identity',
          '--public-issuer-url=' + TEST_ISSUER_URL
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        issuer_url=TEST_ISSUER_URL)

    mock_create_membership.assert_called_once_with(
        'fake-project', 'my-cluster', 'my-cluster',
        '//container.googleapis.com/projects/project/locations/location/clusters/cluster',
        'fake-uid', self.track, TEST_ISSUER_URL
    )

  def testCreateWIMembershipContextDiscoveryException(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.side_effect = exceptions.Error(
        'Oops!')
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaisesRegex(exceptions.Error,
                                'Please double check that it is possible to '
                                'access the /.well-known/openid-configuration '
                                'endpoint on the cluster: Oops!'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        )  # The linter prefers a hanging paren due to above line length.

    mock_create_membership.assert_not_called()

  def testCreateWIMembershipPublicIssuerDiscoveryException(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.side_effect = exceptions.Error(
        'Oops!')
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    # This test is not concerned about exceptions thrown during the command,
    # only that the parameters downstream methods are called with valid args.
    with self.assertRaisesRegex(exceptions.Error,
                                'Please double check that --public-issuer-url '
                                'was set correctly: Oops!'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
          '--public-issuer-url=' + TEST_ISSUER_URL
      ])

    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.assert_called_once_with(
        issuer_url=TEST_ISSUER_URL)

    mock_create_membership.assert_not_called()

  def testCreateWIMembershipProviderConfigMissingIssuer(self):
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    with self.assertRaisesRegex(exceptions.Error,
                                'Invalid OpenID Config: missing issuer: {}'):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
      ])

    mock_create_membership.assert_not_called()

  def testCreateWIMembershipPublicIssuerMismatch(self):
    discovered_issuer = TEST_ISSUER_URL + '/foo'
    self.mock_kubernetes_client.__enter__.return_value.CheckClusterAdminPermissions.return_value = True
    self.mock_kubernetes_client.__enter__.return_value.GetNamespaceUID.return_value = TEST_UID
    self.mock_kubernetes_client.__enter__.return_value.GetOpenIDConfiguration.return_value = json.dumps(
        {'issuer': discovered_issuer})
    self.mock_kubernetes_client.__enter__.return_value.processor.gke_cluster_self_link = None
    # Mock to create a new membership.
    mock_create_membership = self.MockOutCreateMembershipNotFound()
    self.mockValidateExclusivitySucceed()
    self.StartObjectPatch(
        kube_util, 'IsGKECluster', return_value=False)

    with self.assertRaisesRegex(exceptions.Error,
                                '--public-issuer-url {} did not match issuer '
                                'returned in discovery doc: {}'.format(
                                    TEST_ISSUER_URL, discovered_issuer)):
      self.RunCommand([
          'my-cluster', '--kubeconfig=' + self.kubeconfig,
          '--context=test-context', '--project=fake-project',
          '--enable-workload-identity',
          '--public-issuer-url=' + TEST_ISSUER_URL
      ])

    mock_create_membership.assert_not_called()

if __name__ == '__main__':
  test_case.main()
