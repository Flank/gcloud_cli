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
"""Tests for google3.third_party.py.tests.unit.command_lib.container.hub.kube_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.command_lib.container.hub import exclusivity_util
from googlecloudsdk.command_lib.container.hub import kube_util
from googlecloudsdk.core import exceptions
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock


class MembershipCRTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    processor_class_target = 'googlecloudsdk.command_lib.container.hub.kube_util.KubeconfigProcessor'
    with mock.patch(
        processor_class_target, autospec=True, create=True) as mock_processor:
      mock_processor.return_value.GetKubeconfigAndContext.return_value = ('',
                                                                          '')
      self.client = kube_util.KubernetesClient(None)
      self.mock_client = mock.create_autospec(
          kube_util.KubernetesClient, instance=True)
      self.mock_client.GetMembershipOwnerID.side_effect = self.client.GetMembershipOwnerID
      self.client._RunKubectl = self.mock_client._RunKubectl
      self.client.MembershipCRDExists = self.mock_client.MembershipCRDExists

  def testValidMembershipOwnerID(self):
    self.mock_client.MembershipCRDExists.return_value = True
    self.mock_client._RunKubectl.return_value = ('projects/my-project', None)
    self.assertEqual(
        exclusivity_util.GetMembershipCROwnerID(self.mock_client), 'my-project')

  def testMissingMembershipCRD(self):
    self.mock_client.MembershipCRDExists.return_value = False
    self.assertEqual(
        exclusivity_util.GetMembershipCROwnerID(self.mock_client), None)

  def testMalformedMembershipOwnerID(self):
    self.mock_client._RunKubectl.return_value = ('invalid', None)
    with self.assertRaises(exceptions.Error):
      exclusivity_util.GetMembershipCROwnerID(self.mock_client)

  def testErrorGettingOwnerID(self):
    self.mock_client._RunKubectl.return_value = (None, 'unexpected error')
    with self.assertRaises(exceptions.Error):
      exclusivity_util.GetMembershipCROwnerID(self.mock_client)

  def testMissingMembership(self):
    self.mock_client._RunKubectl.return_value = (None, 'NotFound')
    self.assertEqual(None,
                     exclusivity_util.GetMembershipCROwnerID(self.mock_client))


class GKEClusterSelfLinkTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.mock_kubernetes_client = self.StartPatch(
        'googlecloudsdk.command_lib.container.hub.kube_util.KubernetesClient')()

  def testISGKECluster(self):
    self.mock_kubernetes_client.GetResourceField.side_effect = [
        ('instance_id', None),
        ('gce://project-id/vm_zone/instance_id', None),
    ]
    self.assertTrue(kube_util.IsGKECluster(self.mock_kubernetes_client))

  def testNoInstanceID(self):
    self.mock_kubernetes_client.GetResourceField.return_value = (None, None)

    gke_cluster_self_link = kube_util.IsGKECluster(self.mock_kubernetes_client)
    self.assertFalse(gke_cluster_self_link)


class ClusterAdminRBACRoleTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @mock.patch.object(kube_util.KubernetesClient, '_RunKubectl',
                     return_value=('yes', None), autospec=True)
  @mock.patch.object(kube_util.KubeconfigProcessor, 'GetKubeconfigAndContext',
                     return_value=(None, None), autospec=True)
  @mock.patch.object(c_util, 'CheckKubectlInstalled')
  def testClusterAdminPermissions(self, unused_runkubectl, unused_kubecontext,
                                  unused_c_util):
    self.client = kube_util.KubernetesClient(None)
    raised = False
    try:
      self.client.CheckClusterAdminPermissions
    except (kube_util.RBACError, kube_util.KubectlError):
      raised = True
    self.assertFalse(raised)

  @mock.patch.object(kube_util.KubernetesClient, '_RunKubectl',
                     return_value=('no', None), autospec=True)
  @mock.patch.object(kube_util.KubeconfigProcessor, 'GetKubeconfigAndContext',
                     return_value=(None, None), autospec=True)
  @mock.patch.object(c_util, 'CheckKubectlInstalled')
  def testNoClusterAdminPermissions(self, unused_runkubectl, unused_kubecontext,
                                    unused_c_util):
    self.client = kube_util.KubernetesClient(None)
    self.assertRaises(kube_util.RBACError,
                      self.client.CheckClusterAdminPermissions)

  @mock.patch.object(kube_util.KubernetesClient, '_RunKubectl',
                     return_value=(None, 'error'), autospec=True)
  @mock.patch.object(kube_util.KubeconfigProcessor, 'GetKubeconfigAndContext',
                     return_value=(None, None), autospec=True)
  @mock.patch.object(c_util, 'CheckKubectlInstalled')
  def testClusterAdminPermissionsError(self, unused_runkubectl,
                                       unused_kubecontext, unused_c_util):
    self.client = kube_util.KubernetesClient(None)
    self.assertRaises(kube_util.KubectlError,
                      self.client.CheckClusterAdminPermissions)


class OpenIDTest(sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.StartObjectPatch(c_util, 'CheckKubectlInstalled')
    self.StartObjectPatch(
        kube_util.KubeconfigProcessor, 'GetKubeconfigAndContext',
        return_value=('kubeconfig', 'context'), autospec=True)
    self.StartObjectPatch(
        kube_util.KubeconfigProcessor, 'GetClientConfig',
        return_value={
            'server': 'https://cluster.example.com/',
            'cluster_ca_cert': '',
            'client_cert': '',
            'client_key': '',
            'insecure': False,
        }, autospec=True)
    self.StartObjectPatch(
        kube_util.KubernetesClient, '_RunKubectl', return_value=('yes', None),
        autospec=True)

    # Set autospec=False here, because True causes call assertions to expect the
    # implicit "self" argument.
    self.web_request = self.StartObjectPatch(
        kube_util.KubernetesClient, '_WebRequest',
        return_value='{}', autospec=False)
    self.cluster_request = self.StartObjectPatch(
        kube_util.KubernetesClient, '_ClusterRequest',
        return_value='{}', autospec=False)

    parser = argparse.ArgumentParser()
    parser.add_argument('--enable-workload-identity', action='store_true')
    parser.add_argument('--gke-uri')
    parser.add_argument('--gke-cluster')
    args = parser.parse_args(['--enable-workload-identity'])
    self.client = kube_util.KubernetesClient(args)

  def testGetClusterOpenIDConfiguration(self):
    self.client.GetOpenIDConfiguration()
    # Should have used the cluster client, not the web client, because we
    # did not explicitly specify a URL.
    self.web_request.assert_not_called()
    self.cluster_request.assert_called_once_with(
        'GET', 'https://cluster.example.com/.well-known/openid-configuration',
        headers={
            'Content-Type': 'application/json',
        })

  def testGetWebOpenIDConfiguration(self):
    self.client.GetOpenIDConfiguration(
        'https://other.example.com/foo')
    # Should have used the web client, not the cluster client, because we
    # explicitly specify a URL.
    self.cluster_request.assert_not_called()
    self.web_request.assert_called_once_with(
        'GET', 'https://other.example.com/foo/.well-known/openid-configuration',
        headers={
            'Content-Type': 'application/json',
        })

  def testGetClusterOpenIDKeyset(self):
    self.client.GetOpenIDKeyset()
    # Should have used the cluster client, not the web client, because we
    # did not explicitly specify a URL.
    self.web_request.assert_not_called()
    self.cluster_request.assert_called_once_with(
        'GET', 'https://cluster.example.com/openid/v1/jwks',
        headers={
            'Content-Type': 'application/jwk-set+json',
        })

  def testGetWebOpenIDKeyset(self):
    self.client.GetOpenIDKeyset(
        'https://other.example.com/foo/jwks')
    # Should have used the web client, not the cluster client, because we
    # explicitly specify a URL.
    self.cluster_request.assert_not_called()
    self.web_request.assert_called_once_with(
        'GET', 'https://other.example.com/foo/jwks',
        headers={
            'Content-Type': 'application/jwk-set+json',
        })


class ClientConfigTest(sdk_test_base.SdkBase, parameterized.TestCase):

  @mock.patch.object(c_util, 'CheckKubectlInstalled')
  @mock.patch.object(
      kconfig.Kubeconfig,
      'LoadFromFile',
      return_value=kconfig.Kubeconfig(
          {
              'clusters': [
                  {
                      'name': 'ca-data',
                      'cluster': {
                          'server':
                              'https://cluster.example.com/',
                          'certificate-authority-data':
                              'certificate-authority-data',
                      },
                  },
                  {
                      'name': 'ca',
                      'cluster': {
                          'server':
                              'https://cluster.example.com/',
                          'certificate-authority':
                              'certificate-authority',
                      },
                  },
                  {
                      'name': 'insecure',
                      'cluster': {
                          'server': 'https://cluster.example.com/',
                          'insecure-skip-tls-verify': True,
                      },
                  },
                  {
                      'name': 'ca-data-and-insecure',
                      'cluster': {
                          'server':
                              'https://cluster.example.com/',
                          'certificate-authority-data':
                              'certificate-authority-data',
                          'insecure-skip-tls-verify':
                              True,
                      },
                  },
                  {
                      'name': 'cluster-missing-server',
                      'cluster': {
                          'certificate-authority-data':
                              'certificate-authority-data',
                      },
                  },
                  {
                      'name': 'cluster-missing-cluster',
                  },
              ],
              'users': [
                  {
                      'name': 'cert-data',
                      'user': {
                          'client-certificate-data': 'client-certificate-data',
                          'client-key-data': 'client-key-data',
                      },
                  },
                  {
                      'name': 'cert',
                      'user': {
                          'client-certificate': 'client-certificate',
                          'client-key-data': 'client-key-data',
                      },
                  },
                  {
                      'name': 'key',
                      'user': {
                          'client-certificate-data': 'client-certificate-data',
                          'client-key': 'client-key',
                      },
                  },
                  {
                      'name': 'missing-cert',
                      'user': {
                          'client-key-data': 'client-key-data',
                      },
                  },
                  {
                      'name': 'missing-key',
                      'user': {
                          'client-certificate-data': 'client-certificate-data',
                      },
                  },
                  {
                      'name': 'auth-provider',
                      'user': {
                          'auth-provider': {
                              'config': {}
                          },
                      },
                  },
                  {
                      'name': 'user-missing-user',
                  },
              ],
              'contexts': [
                  {
                      'name': 'cert-data_ca-data',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'cert-data_insecure',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'insecure',
                      },
                  },
                  {
                      'name': 'cert-data_ca-data-and-insecure',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'ca-data-and-insecure',
                      },
                  },
                  {
                      'name': 'auth-provider_ca-data',
                      'context': {
                          'user': 'auth-provider',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'cert-data_ca',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'ca',
                      },
                  },
                  {
                      'name': 'cert_ca-data',
                      'context': {
                          'user': 'cert',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'key_ca-data',
                      'context': {
                          'user': 'key',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'missing-cert_ca-data',
                      'context': {
                          'user': 'missing-cert',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'missing-key_ca-data',
                      'context': {
                          'user': 'missing-key',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'context-missing-cluster',
                      'context': {
                          'user': 'auth-provider',
                      },
                  },
                  {
                      'name': 'context-missing-user',
                      'context': {
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'cluster-missing-server',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'cluster-missing-server',
                      },
                  },
                  {
                      'name': 'context-missing-context',
                  },
                  {
                      'name': 'user-missing-user',
                      'context': {
                          'user': 'user-missing-user',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'cluster-missing-cluster',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'cluster-missing-cluster',
                      },
                  },
                  {
                      'name': 'missing-user',
                      'context': {
                          'user': 'missing-user',
                          'cluster': 'ca-data',
                      },
                  },
                  {
                      'name': 'missing-cluster',
                      'context': {
                          'user': 'cert-data',
                          'cluster': 'missing-cluster',
                      },
                  },
              ],
          }, ''),
      autospec=False)
  def testGetClientConfig(self, u2, u1):
    # Client cert auth with tls verification
    expect = {
        'server': 'https://cluster.example.com/',
        'cluster_ca_cert': 'certificate-authority-data',
        'client_cert': 'client-certificate-data',
        'client_key': 'client-key-data',
        'insecure': None,
    }
    client_config = kube_util.KubeconfigProcessor().GetClientConfig(
        'kubeconfig', 'cert-data_ca-data')
    self.assertEqual(client_config, expect)

    # Client cert auth with no tls verification
    expect = {
        'server': 'https://cluster.example.com/',
        'cluster_ca_cert': None,
        'client_cert': 'client-certificate-data',
        'client_key': 'client-key-data',
        'insecure': True,
    }
    client_config = kube_util.KubeconfigProcessor().GetClientConfig(
        'kubeconfig', 'cert-data_insecure')
    self.assertEqual(client_config, expect)

    # Cannot specify both CA data and insecure
    with self.assertRaisesRegex(exceptions.Error,
                                'Cluster cannot specify both '
                                'certificate-authority-data and '
                                'insecure-skip-tls-verify'):
      kube_util.KubeconfigProcessor().GetClientConfig(
          'kubeconfig', 'cert-data_ca-data-and-insecure')

    # auth-provider is not supported by our temporary client (b/150317368)
    with self.assertRaisesRegex(exceptions.Error,
                                'auth-provider is not yet supported, '
                                'user: auth-provider'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'auth-provider_ca-data')

    # certificate-authority is not supported by our temp client (b/150317368)
    with self.assertRaisesRegex(exceptions.Error,
                                'certificate-authority not yet supported. '
                                'Please use certificate-authority-data '
                                'instead.'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'cert-data_ca')

    # client-certificate is not supported by our temp client (b/150317368)
    with self.assertRaisesRegex(exceptions.Error,
                                'client-certificate not yet supported. '
                                'Please use client-certificate-data instead.'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'cert_ca-data')

    # client-key is not supported by our temp client (b/150317368)
    with self.assertRaisesRegex(exceptions.Error,
                                'client-key not yet supported. '
                                'Please use client-key-data instead.'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'key_ca-data')

    # missing cert in user
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing auth info for user: missing-cert'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'missing-cert_ca-data')

    # missing key in user
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing auth info for user: missing-key'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'missing-key_ca-data')

    # missing cluster in context
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig cluster or user in '
                                'context: context-missing-cluster'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'context-missing-cluster')

    # missing user in context
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig cluster or user in '
                                'context: context-missing-user'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'context-missing-user')

    # missing server in cluster
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing server entry for cluster: '
                                'cluster-missing-server'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'cluster-missing-server')

    # missing context in context
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig context: '
                                'context-missing-context'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'context-missing-context')

    # missing user in user
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig entries for cluster: '
                                'ca-data and/or user: user-missing-user '
                                'in context: user-missing-user'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'user-missing-user')

    # missing cluster in cluster
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig entries for cluster: '
                                'cluster-missing-cluster and/or user: '
                                'cert-data in context: '
                                'cluster-missing-cluster'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'cluster-missing-cluster')

    # entirely missing context
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig context: '
                                'missing-context'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'missing-context')

    # entirely missing user
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig entries for cluster: '
                                'ca-data and/or user: missing-user '
                                'in context: missing-user'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'missing-user')

    # entirely missing cluster
    with self.assertRaisesRegex(exceptions.Error,
                                'Missing kubeconfig entries for cluster: '
                                'missing-cluster and/or user: cert-data '
                                'in context: missing-cluster'):
      kube_util.KubeconfigProcessor().GetClientConfig('kubeconfig',
                                                      'missing-cluster')


# TODO(b/152240680): Refactor KubernetesClient so it doesn't rely on a flags
# argument.
# Workload Identity flags are only available on the Alpha release track.
# This test ensures that the client can still be constructed on all tracks.
# Note that, though some other flags are specified in the test for backwards-
# compatibility, this is only designed to test that WI flag access is
# appropriately guarded with hasattr(), and must be manually updated as WI flags
# are graduated, added, or removed.
class KubernetesClientWIReleaseTracksTest(
    sdk_test_base.SdkBase, parameterized.TestCase):

  def SetUp(self):
    self.StartObjectPatch(c_util, 'CheckKubectlInstalled')
    self.mock_get_kubeconfig_and_context = self.StartObjectPatch(
        kube_util.KubeconfigProcessor, 'GetKubeconfigAndContext',
        return_value=(None, None), autospec=True)

    self.parser = argparse.ArgumentParser()
    self.parser.add_argument('--gke-uri')
    self.parser.add_argument('--gke-cluster')

  def testEnableWorkloadIdentityAlpha(self):
    # --enable-workload-identity is only available on the Alpha track
    self.parser.add_argument(
        '--enable-workload-identity', action='store_true')
    args = self.parser.parse_args(['--enable-workload-identity'])

    # This is the exact exception we expect when the alpha flags have been
    # read correctly, based on the (None, None) mocked return value of
    # GetKubeconfigAndContext.
    with self.assertRaisesRegex(
        exceptions.Error,
        'Workload Identity feature does not support '
        'constructing a client from in-cluster config'):
      kube_util.KubernetesClient(args)

  def testManageWorkloadIdentityBucketAlpha(self):
    # --manage-workload-identity-bucket is only available on the Alpha track
    self.parser.add_argument(
        '--manage-workload-identity-bucket', action='store_true')
    args = self.parser.parse_args(['--manage-workload-identity-bucket'])

    # This is the exact exception we expect when the alpha flags have been
    # read correctly, based on the (None, None) mocked return value of
    # GetKubeconfigAndContext.
    with self.assertRaisesRegex(
        exceptions.Error,
        'Workload Identity feature does not support '
        'constructing a client from in-cluster config'):
      kube_util.KubernetesClient(args)

  def testPublicIssuerUrlAlpha(self):
    # Set up a situation where we'd get an exception from constructing a
    # cluster client. We should not try to construct a cluster client
    # when --public-issuer-url is set.
    self.mock_get_kubeconfig_and_context.return_value = (
        'kubeconfig', 'context')
    self.StartObjectPatch(
        kube_util.KubeconfigProcessor, 'GetClientConfig',
        exception=exceptions.Error(''), autospec=True)

    # --public-issuer-url is only available on the Alpha track
    self.parser.add_argument(
        '--enable-workload-identity', action='store_true')
    self.parser.add_argument('--public-issuer-url')
    args = self.parser.parse_args([
        '--enable-workload-identity',
        '--public-issuer-url', 'https://issuer.example.com/foo',
    ])

    kube_util.KubernetesClient(args)

  def testBeta(self):
    args = self.parser.parse_args([])
    kube_util.KubernetesClient(args)

  def testGA(self):
    args = self.parser.parse_args([])
    kube_util.KubernetesClient(args)

if __name__ == '__main__':
  test_case.main()


