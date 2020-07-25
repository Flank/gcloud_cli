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
"""Test for GKE utilities for Serverless."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import base64
import os
import socket
import ssl

from googlecloudsdk.api_lib.run import gke
from tests.lib import test_case

import mock
import six


class MonkeypatchTest(test_case.TestCase):
  """Test for monkeypatching socket.getaddrinfo."""

  def SetUp(self):
    self.stock_getaddrinfo = self.StartPatch('socket.getaddrinfo')
    self.stock_match_hostname = self.StartPatch('ssl.match_hostname')

  def testMonkeypatchGetaddrinfoRedirect(self):
    cert = mock.Mock()
    with gke.MonkeypatchAddressChecking('foo.bar', '1.1.1.1') as endpoint:
      if six.PY3:
        self.assertEquals(endpoint, '1.1.1.1')
        ssl.match_hostname(cert, '1.1.1.1')
        self.stock_match_hostname.assert_called_once_with(cert, 'foo.bar')
      else:
        self.assertEquals(endpoint, 'foo.bar')
        socket.getaddrinfo('foo.bar')
        self.stock_getaddrinfo.assert_called_once_with('1.1.1.1')
    self.assertIs(ssl.match_hostname, self.stock_match_hostname)
    self.assertIs(socket.getaddrinfo, self.stock_getaddrinfo)

  def testMonkeypatchGetaddrinfoNoRedirect(self):
    cert = mock.Mock()
    with gke.MonkeypatchAddressChecking('foo.bar', '1.1.1.1'):
      socket.getaddrinfo('foo.baz')
      ssl.match_hostname(cert, '1.1.1.2')
    self.stock_getaddrinfo.assert_called_once_with('foo.baz')
    self.stock_match_hostname.assert_called_once_with(cert, '1.1.1.2')
    self.assertIs(ssl.match_hostname, self.stock_match_hostname)
    self.assertIs(socket.getaddrinfo, self.stock_getaddrinfo)

  def testMonkeypatchGetaddrinfoNested(self):
    cert = mock.Mock()
    with gke.MonkeypatchAddressChecking('foo.bar', '1.1.1.1') as endpoint:
      with gke.MonkeypatchAddressChecking('baz.quux', '2.2.2.2'):
        if six.PY3:
          self.assertEquals(endpoint, '1.1.1.1')
          ssl.match_hostname(cert, '1.1.1.1')
          self.stock_match_hostname.assert_called_once_with(cert, 'foo.bar')
        else:
          self.assertEquals(endpoint, 'foo.bar')
          socket.getaddrinfo('foo.bar')
          self.stock_getaddrinfo.assert_called_once_with('1.1.1.1')
    self.assertIs(socket.getaddrinfo, self.stock_getaddrinfo)


class ClusterConnectionTest(test_case.TestCase):
  """Test for getting cluster connection info."""

  def testClusterConnectionInfo(self):
    new_api_adapter = self.StartPatch(
        'googlecloudsdk.api_lib.container.api_adapter.NewAPIAdapter')
    opaque_cluster_ref = object()
    gke_api = new_api_adapter.return_value
    mock_cluster = new_api_adapter.return_value.GetCluster.return_value
    ca_data = b'Lol I\'m a ca data file'
    encoded = base64.b64encode(ca_data)
    mock_cluster.mainAuth.clusterCaCertificate = encoded
    mock_cluster.endpoint = '1.1.1.1'
    with gke.ClusterConnectionInfo(opaque_cluster_ref) as (endpoint, filename):
      gke_api.GetCluster.assert_called_once_with(opaque_cluster_ref)
      with open(filename, 'rb') as f:
        contents = f.read()
      self.assertEquals(contents, ca_data)
      self.assertEquals(endpoint, '1.1.1.1')
    self.assertFalse(os.path.exists(filename))


if __name__ == '__main__':
  test_case.main()
