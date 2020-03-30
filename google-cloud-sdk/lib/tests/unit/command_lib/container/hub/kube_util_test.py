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


if __name__ == '__main__':
  test_case.main()


