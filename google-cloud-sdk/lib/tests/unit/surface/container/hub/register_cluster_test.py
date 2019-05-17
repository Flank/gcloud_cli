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

import os

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


def TestDataFile(*args):
  """Returns an SdkBase.Resource for a file from the test data directory.

  Args:
    *args: A list of path components to append to the base test data directory.

  Returns:
    An SdkBase.Resource for the file.
  """
  return sdk_test_base.SdkBase.Resource('tests', 'unit', 'surface', 'container',
                                        'hub', 'testdata', *args)


class RegisterClusterTest(cli_test_base.CliTestBase,
                          sdk_test_base.WithFakeAuth):
  """Tests the logic in the RegisterCluster class.

  These tests are not meant to test the business logic in
  command_lib/container/hub/util.py, but only that the RegisterCluster logic is
  correctly interacting with it.
  """

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.kubeconfig_file = TestDataFile('kubeconfig')
    self.serviceaccount_file = TestDataFile('service_account.json')
    self.mock_kubernetes_client = self.MockOutKubernetesClient()

  def RunCommand(self, params):
    """Runs the 'register-cluster' command with the provided params.

    Args:
      params: A list of parameters to pass to the 'register-cluster' command.

    Returns:
      The results of self.Run() with the provided params.

    Raises:
      Any exception raised by self.Run()
    """
    prefix = ['container', 'hub', 'register-cluster']
    return self.Run(prefix + params)

  def MockOutKubernetesClient(self):
    return self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.util.KubernetesClient')()

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

    with self.AssertRaisesExceptionMatches(Exception,
                                           'service-account-key-file'):
      self.RunCommand([
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context', '--service-account-key-file=bad'
      ])

  def testInvalidDockerServiceAccountKeyFile(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    with self.AssertRaisesExceptionMatches(Exception, 'docker-credential-file'):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file,
          '--docker-credential-file=bad',
      ])

  def testEmptyProjectFlag(self):
    self.MockOutKubernetesClient()
    with self.AssertRaisesExceptionMatches(Exception, 'project'):
      self.RunCommand([
          'my-cluster', '--context=test-context', '--project=',
          '--service-account-key-file=bad'
      ])

  def testCreateMembershipNotFound(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_create_membership.side_effect = apitools_exceptions.HttpNotFoundError(
        None, None, None)

    with self.AssertRaisesExceptionMatches(Exception, 'Could not access'):
      self.RunCommand([
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipConfictNotAlreadyExists(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'CONFLICT'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)

    with self.AssertRaisesExceptionMatches(calliope_exceptions.HttpException,
                                           'CONFLICT'):
      self.RunCommand([
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipAlreadyExistsWithDifferentName(self):
    self.mock_kubernetes_client = self.MockOutKubernetesClient()
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

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
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testCreateMembershipAlreadyExistsWithSameName(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'

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
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

  def testGenerateManfiestFile(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = []

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    manifest_path = os.path.join(self.temp_path, 'manifest.yaml')
    self.RunCommand([
        'my-cluster',
        '--kubeconfig-file=' + self.kubeconfig_file,
        '--context=test-context',
        '--docker-image=gcr.io/test/test',
        '--service-account-key-file=' + self.serviceaccount_file,
        '--manifest-output-file=' + manifest_path,
    ])

    # This is not a full-scale validation of the manifest: it's a sanity check
    # that verifies that parameters have been passed into the manifest
    # generator.
    self.AssertFileExists(manifest_path)
    self.AssertFileContains('namespace: gke-connect-12321', manifest_path)
    self.AssertFileContains('membership_name: "my-cluster"', manifest_path)
    self.AssertFileContains('project_id: "fake-project"', manifest_path)
    self.AssertFileContains('image: gcr.io/test/test', manifest_path)

  def testNamespaceExistenceVerificationOnNonUpdate(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespaceExists.return_value = True
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           ''):
      self.WriteInput('N')
      self.RunCommand([
          'my-cluster',
          '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--docker-image=gcr.io/test/test',
          '--service-account-key-file=' + self.serviceaccount_file,
      ])
      self.AssertOutputContains('Namespace [gke-connect-12321] already exists')
      mock_delete_membership.assert_called_with(
          'projects/fake-project/locations/global/memberships/fake-uid')

  def testFailedAgentDeployment(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.Apply.return_value = 'Error applying manifest'

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(exceptions.Error, ''):
      self.RunCommand([
          'my-cluster',
          '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context',
          '--docker-image=gcr.io/test/test',
          '--service-account-key-file=' + self.serviceaccount_file,
      ])
      mock_delete_membership.assert_called_with(
          'projects/fake-project/locations/global/memberships/fake-uid')

  def testSuccessfulAgentDeployment(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.NamespaceExists.return_value = False
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = []
    self.mock_kubernetes_client.GetPodField.return_value = ('Succeeded', None)
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_create_membership.return_value = messages.Membership(
        name='projects/fake-project/locations/global/memberships/fake-uid',
        description='my-cluster')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    self.RunCommand([
        'my-cluster',
        '--kubeconfig-file=' + self.kubeconfig_file,
        '--context=test-context',
        '--docker-image=gcr.io/test/test',
        '--service-account-key-file=' + self.serviceaccount_file,
    ])
    mock_delete_membership.assert_not_called()

  def testSuccessfulAgentUpgradeWithProjectNumberNamespace(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetPodField.return_value = ('Succeeded', None)
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect-12321'
    ]

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')

    self.StartObjectPatch(p_util, 'GetProjectNumber')

    # The prompt is for membership deletion.
    self.WriteInput('Y')
    self.RunCommand([
        'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
        '--context=test-context', '--docker-image=gcr.io/test/test',
        '--service-account-key-file=' + self.serviceaccount_file
    ])
    # DeleteMembership should only be called for cancellations/failures if
    # this invocation caused a membership to be created.
    mock_delete_membership.assert_not_called()

    # If the membership already exists, then the existence of the namespace
    # should not be verified.
    self.mock_kubernetes_client.NamespaceExists.assert_not_called()

    # The Connect namespace should be searched for by its label.
    self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')
    self.mock_kubernetes_client.NamespaceExists.assert_not_called()

    manifest_yaml_call_arg = self.mock_kubernetes_client.Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertIn('namespace: gke-connect-12321', manifest_yaml_call_arg[0])
    self.assertNotIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithNonProjectNumberNamespace(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetPodField.return_value = ('Succeeded', None)
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect'
    ]

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    self.WriteInput('Y')
    self.RunCommand([
        'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
        '--context=test-context', '--docker-image=gcr.io/test/test',
        '--service-account-key-file=' + self.serviceaccount_file
    ])
    # DeleteMembership should only be called for cancellations/failures if
    # this invocation caused a membership to be created.
    mock_delete_membership.assert_not_called()

    # If the membership already exists, then the existence of the namespace
    # should not be verified.
    self.mock_kubernetes_client.NamespaceExists.assert_not_called()

    # The Connect namespace should be searched for by its label.
    self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
        'hub.gke.io/project=fake-project')

    # If the connect namespace does not have a project number, that should be
    # reflected in the generated manifest.
    manifest_yaml_call_arg = self.mock_kubernetes_client.Apply.call_args[0]
    self.assertTrue(manifest_yaml_call_arg)
    self.assertIn('namespace: gke-connect\n', manifest_yaml_call_arg[0])
    self.assertNotIn('namespace: gke-connect-12321\n',
                     manifest_yaml_call_arg[0])

  def testSuccessfulAgentUpgradeWithMultipleConnectNamespaces(self):
    self.mock_kubernetes_client.GetNamespaceUID.return_value = 'fake-uid'
    self.mock_kubernetes_client.GetPodField.return_value = ('Succeeded', None)
    self.mock_kubernetes_client.Apply.return_value = None
    self.mock_kubernetes_client.Logs.return_value = ('Fake log', None)
    self.mock_kubernetes_client.Delete.return_value = None
    self.mock_kubernetes_client.NamespacesWithLabelSelector.return_value = [
        'gke-connect',
        'gke-connect-2',
    ]

    mock_create_membership = self.StartObjectPatch(util, 'CreateMembership')
    response = {'reason': 'ALREADY_EXISTS'}
    mock_create_membership.side_effect = apitools_exceptions.HttpConflictError(
        response, None, None)
    mock_get_membership = self.StartObjectPatch(util, 'GetMembership')
    messages = core_apis.GetMessagesModule('gkehub', 'v1beta1')
    mock_get_membership.return_value = messages.Membership(
        description='my-cluster')
    mock_delete_membership = self.StartObjectPatch(util, 'DeleteMembership')

    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)

    with self.AssertRaisesExceptionMatches(exceptions.Error, 'Multiple'):
      self.WriteInput('Y')
      self.RunCommand([
          'my-cluster', '--kubeconfig-file=' + self.kubeconfig_file,
          '--context=test-context', '--docker-image=gcr.io/test/test',
          '--service-account-key-file=' + self.serviceaccount_file
      ])

      mock_delete_membership.assert_called_once()

      # If the membership already exists, then the existence of the namespace
      # should not be verified.
      self.mock_kubernetes_client.NamespaceExists.assert_not_called()

      # The Connect namespace should be searched for by its label.
      self.mock_kubernetes_client.NamespacesWithLabelSelector.assert_called_once_with(
          'hub.gke.io/project=fake-project')


if __name__ == '__main__':
  test_case.main()
