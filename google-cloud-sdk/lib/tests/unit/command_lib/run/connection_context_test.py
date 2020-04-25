# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for connection_context."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import ssl

from googlecloudsdk.api_lib.container import kubeconfig
from googlecloudsdk.api_lib.run import gke
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.core import properties

from tests.lib import parameterized
from tests.lib import test_case

import mock
import six


class ConnectionContextTest(test_case.TestCase, parameterized.TestCase):

  def SetUp(self):
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    self.cluster_connection_info = self.StartObjectPatch(
        gke, 'ClusterConnectionInfo')
    self.cluster_connection_info.return_value.__enter__.return_value = (
        '1.1.1.2', '/some/temp/file')
    self.operations_ctor = self.StartObjectPatch(
        serverless_operations, 'ServerlessOperations')
    self.get_client_instance = self.StartObjectPatch(apis, 'GetClientInstance')
    self.get_client_instance_internal = self.StartObjectPatch(
        apis_internal, '_GetClientInstance')
    self.args = mock.Mock()

  @parameterized.parameters(
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.BETA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.GA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, 'v1alpha1', 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.BETA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.GA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, 'v1', 'v1'),
  )
  def testGetConnectionContextGke(self, product, release_track,
                                  version_override, expected_api_version):
    properties.VALUES.run.platform.Set('gke')
    cluster_ref = mock.Mock()
    self.args.CONCEPTS.cluster.Parse.return_value = cluster_ref
    gke_context = self.StartObjectPatch(connection_context,
                                        '_GKEConnectionContext')

    connection_context.GetConnectionContext(self.args, product, release_track,
                                            version_override)

    gke_context.assert_called_once_with(cluster_ref, expected_api_version)

  @parameterized.parameters(
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.BETA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.GA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, 'v1alpha1', 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.BETA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.GA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, 'v1', 'v1'),
  )
  def testGetConnectionContextKubernetes(self, product, release_track,
                                         version_override,
                                         expected_api_version):
    properties.VALUES.run.platform.Set('kubernetes')
    kubeconfig_obj = kubeconfig.Kubeconfig.Default()
    self.StartObjectPatch(flags, 'GetKubeconfig', return_value=kubeconfig_obj)
    self.args.context = 'context'
    kubernetes_context = self.StartObjectPatch(connection_context,
                                               '_KubeconfigConnectionContext')

    connection_context.GetConnectionContext(self.args, product, release_track,
                                            version_override)

    kubernetes_context.assert_called_once_with(kubeconfig_obj,
                                               expected_api_version, 'context')

  @parameterized.parameters(
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.BETA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.GA, None, 'v1'),
      (flags.Product.RUN, base.ReleaseTrack.ALPHA, 'v1alpha1', 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.BETA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.GA, None, 'v1alpha1'),
      (flags.Product.EVENTS, base.ReleaseTrack.ALPHA, 'v1', 'v1'),
  )
  def testGetConnectionContextManaged(self, product, release_track,
                                      version_override, expected_api_version):
    properties.VALUES.run.platform.Set('managed')
    self.StartObjectPatch(flags, 'GetRegion', return_value='us-central1')
    regional_context = self.StartObjectPatch(connection_context,
                                             '_RegionalConnectionContext')

    connection_context.GetConnectionContext(self.args, product, release_track,
                                            version_override)

    regional_context.assert_called_once_with('us-central1',
                                             expected_api_version)

  @parameterized.parameters('v1', 'v1alpha1')
  def testConnectToGKECluster(self, version):
    cluster_ref = mock.Mock()
    with connection_context._GKEConnectionContext(cluster_ref, version):
      if six.PY3:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://1.1.1.2/')
      else:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://kubernetes.default/')

  @parameterized.parameters('v1', 'v1alpha1')
  def testConnectToRegion(self, version):
    with connection_context._RegionalConnectionContext(
        'us-central1', version):
      self.assertEqual(
          properties.VALUES.api_endpoint_overrides.run.Get(),
          'https://us-central1-run.googleapis.com/')

  @parameterized.parameters('v1', 'v1alpha1')
  def testConnectToKubeconfigClusterWithCurrentContext(self, version):
    config = kubeconfig.Kubeconfig.Default()
    cluster = kubeconfig.Cluster(
        'cluster1', 'https://2.2.2.2:443', ca_data='=')
    user = kubeconfig.User('user', cert_data='aGF0',
                           key_data='c2FsYWQ=')
    context = kubeconfig.Context('context', 'cluster1', 'user')
    config.clusters['cluster1'] = cluster
    config.users['user'] = user
    config.contexts['context'] = context
    config.SetCurrentContext('context')
    with connection_context._KubeconfigConnectionContext(config, version):
      if six.PY3:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://2.2.2.2/')
      else:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://kubernetes.default/')

  @parameterized.parameters('v1', 'v1alpha1')
  def testConnectToKubeconfigClusterWithSpecifiedContext(self, version):
    config = kubeconfig.Kubeconfig.Default()
    cluster = kubeconfig.Cluster(
        'cluster1', 'https://2.2.2.2', ca_data='=')
    user = kubeconfig.User('user', cert_data='aGF0',
                           key_data='c2FsYWQ=')
    context = kubeconfig.Context('context', 'cluster1', 'user')
    config.clusters['cluster1'] = cluster
    config.users['user'] = user
    config.contexts['context'] = context
    config.SetCurrentContext('some_other_context')
    with connection_context._KubeconfigConnectionContext(
        config, version, 'context'):
      if six.PY3:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://2.2.2.2/')
      else:
        self.assertEqual(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://kubernetes.default/')


class TLSSupportCheckTest(test_case.TestCase):
  """Tests the method _CheckTLSSupport()."""

  def SetUp(self):
    if hasattr(ssl, 'PROTOCOL_TLS'):
      self.protocol_tls = ssl.PROTOCOL_TLS
    if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
      self.protocol_tlsv1_2 = ssl.PROTOCOL_TLSv1_2

  def TearDown(self):
    if hasattr(self, 'protocol_tls'):
      ssl.PROTOCOL_TLS = self.protocol_tls
    if hasattr(self, 'protocol_tlsv1_2'):
      ssl.PROTOCOL_TLSv1_2 = self.protocol_tlsv1_2

  def testSucceed(self):
    ssl.PROTOCOL_TLS = 2
    connection_context._CheckTLSSupport()

  def testFailBadSSL(self):
    self.StartObjectPatch(ssl, 'OPENSSL_VERSION', new='OpenSSL 0.9.8zh')
    # Make sure we ask for SSL >1.0
    with self.assertRaisesRegex(serverless_exceptions.NoTLSError, '>1\\.0'):
      connection_context._CheckTLSSupport()

  def testFail(self):
    if hasattr(ssl, 'PROTOCOL_TLS'):
      del ssl.PROTOCOL_TLS
    if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
      del ssl.PROTOCOL_TLSv1_2
    with self.assertRaises(serverless_exceptions.NoTLSError):
      connection_context._CheckTLSSupport()
