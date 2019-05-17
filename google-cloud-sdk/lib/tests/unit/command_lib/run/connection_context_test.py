# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

from googlecloudsdk.api_lib.run import gke
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.core import properties

from tests.lib import test_case

import mock
import six


class ConnectionContextTest(test_case.TestCase):

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

  def testConnectToCluster(self):
    cluster_ref = mock.Mock()
    with connection_context._GKEConnectionContext(cluster_ref):
      if six.PY3:
        self.assertEquals(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://1.1.1.2/')
      else:
        self.assertEquals(
            properties.VALUES.api_endpoint_overrides.run.Get(),
            'https://kubernetes.default/')

  def testConnectToRegion(self):
    with connection_context._RegionalConnectionContext('us-central1'):
      self.assertEquals(
          properties.VALUES.api_endpoint_overrides.run.Get(),
          'https://us-central1-run.googleapis.com/')


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
