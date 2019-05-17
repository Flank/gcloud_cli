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

from googlecloudsdk.command_lib.container.hub import util
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import exceptions
from tests.lib import sdk_test_base
from tests.lib import test_case


class FakeKubernetesClient(util.KubernetesClient):
  """A test fake for the util.KubernetesClient class."""

  def __init__(self, labelled_namespaces):
    self.labelled_namespaces = labelled_namespaces

  def NamespacesWithLabelSelector(self, label):
    return self.labelled_namespaces


class UtilTest(sdk_test_base.SdkBase):

  def testGKEConnectNamespaceNeitherNamespaceLabelled(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=123)
    client = FakeKubernetesClient([])
    self.assertEqual('gke-connect-123',
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


if __name__ == '__main__':
  test_case.main()
