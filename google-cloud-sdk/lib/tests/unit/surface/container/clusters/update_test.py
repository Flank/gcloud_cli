# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Test of the 'clusters' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.container import base
from six.moves import range


class UpdateTestGA(parameterized.TestCase, base.GATestBase,
                   base.ClustersTestBase, test_case.WithInput):
  """gcloud GA track using container v1 API."""

  def testUpdateMonitoringNone(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredMonitoringService='none'),
        flags='--monitoring-service=none')

  def testUpdateMonitoringGoogle(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='monitoring.googleapis.com'),
        flags='--monitoring-service=monitoring.googleapis.com')

  def testUpdateLoggingNone(self):
    name = 'tosetloggingservice'
    logging_service = 'none'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetLoggingService(name, logging_service,
                                 self._MakeOperation(status=self.op_pending))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1} {2}'.format(name, '--logging-service', logging_service)
    )
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def testUpdateLoggingGoogle(self):
    name = 'tosetloggingservice'
    logging_service = 'logging.googleapis.com'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetLoggingService(name, logging_service,
                                 self._MakeOperation(status=self.op_pending))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1} {2}'.format(name, '--logging-service', logging_service)
    )
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def testUpdateLoggingInvalid(self):
    name = 'tosetloggingservice'
    logging_service = 'fancyloggingservice.net'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetLoggingService(
        name,
        logging_service,
        exception=http_error.MakeHttpError(400, 'bad request'))
    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1} {2}'.format(name, '--logging-service',
                                       logging_service))
    self.AssertErrContains('message=bad request')

  def testEnableStackdriverKubernetesOnly(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='monitoring.googleapis.com/kubernetes',
            desiredLoggingService='logging.googleapis.com/kubernetes'),
        flags='--enable-stackdriver-kubernetes')

  def testEnableIntraNodeVisibility(self):
    update = self.msgs.ClusterUpdate(
        desiredIntraNodeVisibilityConfig=self.msgs.IntraNodeVisibilityConfig(
            enabled=True))
    self._TestUpdate(update=update, flags='--enable-intra-node-visibility')

  def testInvalidEnableStackdriverKubernetesTogetherWithLegacyFlags(self):
    with self.AssertRaisesArgumentErrorRegexp('Exactly one of '):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update clustername '
          '--monitoring-service=some.monitoring.service '
          '--logging-service=some.logging.service '
          '--enable-stackdriver-kubernetes')

  def testNoUpdate(self):
    with self.AssertRaisesArgumentErrorRegexp('^Exactly one of '):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update clustername')

  def testOnlyOneUpdateType(self):
    with self.AssertRaisesArgumentErrorRegexp(
        'argument (--update-addons|--monitoring-service): Exactly one of '):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update clustername '
          '--monitoring-service=monitoring.googleapis.com '
          '--update-addons=HttpLoadBalancing=ENABLED')

  def testInvalidAddonUpdate(self):
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update clustername --update-addons=HttpLoadBalancing=true')
    self.AssertErrContains('must be ENABLED or DISABLED')

  def testUpdateAddons(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=True),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=False))),
        flags='--update-addons '
        'HttpLoadBalancing=DISABLED,HorizontalPodAutoscaling=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True))),
        flags='--update-addons '
        'HttpLoadBalancing=ENABLED,HorizontalPodAutoscaling=DISABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(disabled=False))),
        flags='--update-addons HttpLoadBalancing=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True))),
        flags='--update-addons HorizontalPodAutoscaling=DISABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=False))),
        flags='--update-addons KubernetesDashboard=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kubernetesDashboard=self.msgs.KubernetesDashboard(
                    disabled=True))),
        flags='--update-addons KubernetesDashboard=DISABLED')

  def testUpdateAddonsCloudRun(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=False))),
        flags='--update-addons CloudRun=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=True))),
        flags='--update-addons CloudRun=DISABLED')

  def testUpdateAddonsConfigConnector(self):
    # test disabling ConfigConnector
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                configConnectorConfig=self.msgs.ConfigConnectorConfig(
                    enabled=False))),
        flags='--update-addons ConfigConnector=DISABLED')
    # test enabling ConfigConnector
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                configConnectorConfig=self.msgs.ConfigConnectorConfig(
                    enabled=True))),
        flags='--update-addons ConfigConnector=ENABLED')

  def testUpdateAddonsNodeLocalDNS(self):
    self.WriteInput('y')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=False))),
        flags='--update-addons NodeLocalDNS=DISABLED')

    self.WriteInput('y')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True))),
        flags='--update-addons NodeLocalDNS=ENABLED')

    self._TestUpdateAbort(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=False))),
        flags='--update-addons NodeLocalDNS=DISABLED')

    self._TestUpdateAbort(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True))),
        flags='--update-addons NodeLocalDNS=ENABLED')

  def testEnableClusterAutoscaler(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
                enabled=True, minNodeCount=11, maxNodeCount=22)),
        flags='--enable-autoscaling '
        '--max-nodes=22 '
        '--min-nodes=11 ')

  def testEnableClusterAutoscalerForPool(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredNodePoolId='mynodepool',
            desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
                enabled=True, minNodeCount=11, maxNodeCount=22)),
        flags='--enable-autoscaling '
        '--max-nodes=22 '
        '--min-nodes=11 '
        '--node-pool=mynodepool ')

  def testDisableClusterAutoscaler(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredNodePoolAutoscaling=self.msgs.NodePoolAutoscaling(
                enabled=False)),
        flags='--no-enable-autoscaling '
        '--max-nodes=1 ')

  def testEnableMasterAuthorizedNetworks(self):
    desired = self.msgs.MasterAuthorizedNetworksConfig(enabled=True)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMasterAuthorizedNetworksConfig=desired),
        flags='--enable-master-authorized-networks ')

  def testEnableMasterAuthorizedNetworksWithSourceRanges(self):
    desired = self.msgs.MasterAuthorizedNetworksConfig(
        enabled=True,
        cidrBlocks=[
            self.msgs.CidrBlock(cidrBlock='10.0.0.1/32'),
            self.msgs.CidrBlock(cidrBlock='10.0.0.2/32'),
        ],
    )
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMasterAuthorizedNetworksConfig=desired),
        flags='--enable-master-authorized-networks '
        '--master-authorized-networks=10.0.0.1/32,10.0.0.2/32 ')

  def testEnableMasterAuthorizedNetworksWithMaxSourceRanges(self):
    cidr_blocks = []
    msgs_cidr_blocks = []
    for i in range(1, api_adapter.MAX_AUTHORIZED_NETWORKS_CIDRS_PUBLIC + 1):
      cidr = '10.0.0.%d/32' % i
      cidr_blocks.append(cidr)
      msgs_cidr_blocks.append(self.msgs.CidrBlock(cidrBlock=cidr))
    desired = self.msgs.MasterAuthorizedNetworksConfig(
        enabled=True, cidrBlocks=msgs_cidr_blocks)

    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMasterAuthorizedNetworksConfig=desired),
        flags='--enable-master-authorized-networks '
        '--master-authorized-networks=' + ','.join(cidr_blocks))

  def testDisableMasterAuthorizedNetworks(self):
    desired = self.msgs.MasterAuthorizedNetworksConfig(enabled=False)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMasterAuthorizedNetworksConfig=desired),
        flags='--no-enable-master-authorized-networks ')

  def testInvalidMasterAuthorizedNetworksWithoutEnable(self):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update {0} '
          '--no-enable-master-authorized-networks '
          '--master-authorized-networks=10.0.0.1/32,10.0.0.2/32 '.format(name))
      self.AssertErrContains('Cannot use --master-authorized-networks')

  def testInvalidMasterAuthorizedNetworksAlone(self):
    with self.AssertRaisesArgumentErrorRegexp('^Exactly one of '):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update clustername '
          '--master-authorized-networks=10.0.0.1/32,10.0.0.2/32 ')

  def testEnableLegacyAbac(self):
    self._TestLegacyAbac(enabled=True, flags='--enable-legacy-authorization ')

  def testNoEnableLegacyAbac(self):
    self._TestLegacyAbac(
        enabled=False, flags='--no-enable-legacy-authorization ')

  def _TestLegacyAbac(self, enabled, flags):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectLegacyAbac(
        cluster_name=name,
        enabled=enabled,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def testStartIpRotation(self):
    """Correctly handle the success case, and persist the updated config."""

    name = 'tobeupdated'
    original_ip = '123.45.67.89'
    updated_ip = '98.76.54.32'
    original_ca = 'CA1'
    updated_ca = 'CA1.CA2'
    self._TestIpRotation(
        response='y',
        before=self._RunningCluster(
            name=name, endpoint=original_ip, ca_data=original_ca))
    self.ExpectStartIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(
        name=name,
        flag='--start-ip-rotation',
        after=self._RunningCluster(
            name=name, endpoint=updated_ip, ca_data=updated_ca))
    c_config = c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID)
    self.assertEqual(c_config.server, 'https://' + updated_ip)
    self.assertEqual(c_config.ca_data, updated_ca)

  def testStartCredentialRotation(self):
    """Correctly handle the success case, and persist the updated config."""

    name = 'tobeupdated'
    original_ip = '123.45.67.89'
    updated_ip = '98.76.54.32'
    original_ca = 'CA1'
    updated_ca = 'CA1.CA2'
    self._TestIpRotation(
        response='y',
        before=self._RunningCluster(
            name=name, endpoint=original_ip, ca_data=original_ca))
    self.ExpectStartIpRotation(
        cluster_name=name,
        rotate_credentials=True,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(
        name=name,
        flag='--start-credential-rotation',
        after=self._RunningCluster(
            name=name, endpoint=updated_ip, ca_data=updated_ca))
    c_config = c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID)
    self.assertEqual(c_config.server, 'https://' + updated_ip)
    self.assertEqual(c_config.ca_data, updated_ca)

  def testStartIpRotationAborted(self):
    """Correctly handle a user aborting the command at the prompt."""

    self._TestIpRotationAborted(flag='--start-ip-rotation')

  def testStartIpRotationPersistEnvVarError(self):
    """Correctly handle environment variable errors persisting config."""

    name = 'tobeupdated'
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.StartDictPatch('os.environ', {
        'HOME': '',
        'HOMEDRIVE': '',
        'HOMEPATH': '',
        'USERPROFILE': ''
    })
    self._TestIpRotation(response='y')
    self.ExpectStartIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(name=name, flag='--start-ip-rotation')
    self.AssertErrContains('KUBECONFIG must be set')

  def testStartIpRotationPersistHttpError(self):
    """Correctly handle HTTP errors retrieving the cluster to persist config."""

    name = 'tobeupdated'
    self._TestIpRotation(response='y')
    self.ExpectStartIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))

    with self.assertRaises(exceptions.HttpException):
      self._TestIpRotationSuccess(
          name=name,
          flag='--start-ip-rotation',
          after_exception=http_error.MakeHttpError(500, 'internal error'))
    self.AssertErrContains('message=internal error')

  def testStartIpRotationError(self):
    """Correctly handle errors from the GKE API."""

    name = 'tobeupdated'
    self._TestIpRotation(response='y')
    self.ExpectStartIpRotation(
        cluster_name=name,
        exception=http_error.MakeHttpError(
            409, 'The cluster has an IP rotation'
            ' in progress.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} --start-ip-rotation'.format(name))
    self.AssertErrContains('code=409, message=The cluster has an IP rotation in'
                           ' progress')

  def testCompleteIpRotation(self):
    """Correctly handle the success case, and persist the updated config."""

    name = 'tobeupdated'
    original_ca = 'CA1.CA2'
    updated_ca = 'CA2'
    self._TestIpRotation(
        response='y',
        before=self._RunningCluster(name=name, ca_data=original_ca))
    self.ExpectCompleteIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(
        name=name,
        flag='--complete-ip-rotation',
        after=self._RunningCluster(name=name, ca_data=updated_ca))
    c_config = c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID)
    self.assertEqual(c_config.ca_data, updated_ca)

  def testCompleteCredentialRotation(self):
    """Correctly handle the success case, and persist the updated config."""

    name = 'tobeupdated'
    original_ca = 'CA1.CA2'
    updated_ca = 'CA2'
    self._TestIpRotation(
        response='y',
        before=self._RunningCluster(name=name, ca_data=original_ca))
    self.ExpectCompleteIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(
        name=name,
        flag='--complete-credential-rotation',
        after=self._RunningCluster(name=name, ca_data=updated_ca))
    c_config = c_util.ClusterConfig.Load(name, self.ZONE, self.PROJECT_ID)
    self.assertEqual(c_config.ca_data, updated_ca)

  def testCompleteIpRotationAborted(self):
    """Correctly handle a user aborting the command at the prompt."""

    self._TestIpRotationAborted(flag='--complete-ip-rotation')

  def testCompleteIpRotationPersistEnvVarError(self):
    """Correctly handle environment variable errors persisting config."""

    name = 'tobeupdated'
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.StartDictPatch('os.environ', {
        'HOME': '',
        'HOMEDRIVE': '',
        'HOMEPATH': '',
        'USERPROFILE': ''
    })
    self._TestIpRotation(response='y')
    self.ExpectCompleteIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self._TestIpRotationSuccess(name=name, flag='--complete-ip-rotation')
    self.AssertErrContains('KUBECONFIG must be set')

  def testCompleteIpRotationPersistHttpError(self):
    """Correctly handle HTTP errors retrieving the cluster to persist config."""
    name = 'tobeupdated'

    self._TestIpRotation(response='y')
    self.ExpectCompleteIpRotation(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_update_cluster))

    with self.assertRaises(exceptions.HttpException):
      self._TestIpRotationSuccess(
          name=name,
          flag='--complete-ip-rotation',
          after_exception=http_error.MakeHttpError(500, 'internal error'))
    self.AssertErrContains('message=internal error')

  def testCompleteIpRotationError(self):
    """Correctly handle errors from the GKE API."""
    name = 'tobeupdated'
    self._TestIpRotation(response='y')
    self.ExpectCompleteIpRotation(
        cluster_name=name,
        exception=http_error.MakeHttpError(
            400, 'The cluster does not have an'
            ' IP rotation in progress.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} --complete-ip-rotation'.format(name))
    self.AssertErrContains('code=400, message=The cluster does not have an IP'
                           ' rotation in progress')

  def _TestIpRotation(self, response, before=None):
    """This sets up the IP Rotation tests.

    Args:
      response: Either 'y' or 'n', for what gets passed into the prompt.
      before: The cluster to return on the first GetCluster call.
    """
    properties.VALUES.core.disable_prompts.Set(False)
    self.WriteInput(response)
    if not before:
      before = self._RunningCluster(name='tobeupdated')
    self.ExpectGetCluster(before)

  def _TestIpRotationSuccess(self,
                             name,
                             flag,
                             after=None,
                             after_exception=None):
    """This runs an ip rotation command and confirms that it succeeded.

    Args:
      name: The name of the cluster being updated.
      flag: One of '--start-ip-rotation', '--complete-ip-rotation',
        '--start-credential-rotation', or '--complete-credential-rotation',
        depending on which operation is being tested.
      after: The cluster to return after the rotation operation.
      after_exception: The error to throw on the GetCluster call after the
        rotation operation.
    """
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    if not after:
      after = self._RunningCluster(name='tobeupdated')
    self.ExpectGetCluster(after, after_exception)
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flag))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestIpRotationAborted(self, flag):
    """This runs an ip rotation command, but then aborts at the prompt.

    Args:
      flag: Either '--start-ip-rotation' or '--complete-ip-rotation', depending
        on which operation is being tested.
    """
    name = 'tobeupdated'
    self._TestIpRotation(response='n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {name} {flag}'.format(name=name, flag=flag))
    self.AssertErrContains('Aborted by user.')

  def testSetPassword(self):
    action = self.action_set_password
    password = '1234567890abcdef'
    flags = '--password=' + password
    auth = self.msgs.MasterAuth(password=password)
    self._TestUpdateMasterAuth(action, auth, password, flags=flags)

  def testSetPasswordPrompt(self):
    action = self.action_set_password
    password = '1234567890abcdef'
    auth = self.msgs.MasterAuth(password=password)
    self._TestUpdateMasterAuth(action, auth, password, flags='--set-password ')

  def testSetPasswordError(self):
    """Correctly handle errors from the GKE API."""

    name = 'tobeupdated'
    password = '1234567890abcdef'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetMasterAuth(
        cluster_name=name,
        action=self.action_set_password,
        update=self.msgs.MasterAuth(password=password),
        exception=http_error.MakeHttpError(500, 'internal error'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update {0} '
          '--password='.format(name) + password)
    self.AssertErrContains('code=500, message=internal error')

  def testGeneratePassword(self):
    action = self.action_generate_password
    password = ''
    auth = self.msgs.MasterAuth(password=password)
    self._TestUpdateMasterAuth(
        action, auth, password, flags='--generate-password ')

  def testGeneratePasswordError(self):
    """Correctly handle errors from the GKE API."""

    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetMasterAuth(
        cluster_name=name,
        action=self.action_generate_password,
        update=self.msgs.MasterAuth(password=''),
        exception=http_error.MakeHttpError(500, 'internal error'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update {0} '
          '--generate-password'.format(name))
    self.AssertErrContains('code=500, message=internal error')

  # This is also the process for changing username on a cluster that already has
  # basic auth enabled.
  @parameterized.parameters('--username=admin', '--enable-basic-auth')
  def testEnableBasicAuth(self, flags):
    action = self.action_set_username
    password = ''
    auth = self.msgs.MasterAuth(username='admin')
    self._TestUpdateMasterAuth(action, auth, password, flags=flags)

  @parameterized.parameters(
      '--username=admin --password=ahoy',
      '--enable-basic-auth --password=ahoy',
  )
  def testEnableBasicAuthWithPassword(self, flags):
    action = self.action_set_username
    password = ''
    auth = self.msgs.MasterAuth(username='admin', password='ahoy')
    self._TestUpdateMasterAuth(action, auth, password, flags=flags)

  @parameterized.parameters('--username=""', '--no-enable-basic-auth')
  def testDisableBasicAuth(self, flags):
    action = self.action_set_username
    password = ''
    auth = self.msgs.MasterAuth(username='')
    self._TestUpdateMasterAuth(action, auth, password, flags=flags)

  @parameterized.parameters(
      '--username="" --password=asdf',
      '--no-enable-basic-auth --password=asdf',
      '--username="" --password=""',
      '--no-enable-basic-auth --password=""',
  )
  def testDisableBasicAuthWithPassword(self, flags):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1} '.format(name, flags))
    self.AssertErrContains(constants.USERNAME_PASSWORD_ERROR_MSG)

  @parameterized.parameters(
      '--username="admin" --enable-basic-auth ',
      '--username="" --no-enable-basic-auth ',
      '--username="admin" --no-enable-basic-auth ',
      '--username="" --enable-basic-auth ',
  )
  def testUsernameEnableBasicAuthMutex(self, flags):
    with self.AssertRaisesArgumentErrorRegexp('At most one of '):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update clustername {0} '.format(flags))

  def testSetUsernameError(self):
    """Correctly handle errors from the GKE API."""

    name = 'tobeupdated'
    username = 'person'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetMasterAuth(
        cluster_name=name,
        action=self.action_set_username,
        update=self.msgs.MasterAuth(username=username),
        exception=http_error.MakeHttpError(500, 'internal error'))

    with self.assertRaises(exceptions.HttpException):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update {0} '
          '--username='.format(name) + username)
    self.AssertErrContains('code=500, message=internal error')

  def testEnableVerticalPodAutoscaling(self):
    update = self.msgs.ClusterUpdate(
        desiredVerticalPodAutoscaling=self.msgs.VerticalPodAutoscaling(
            enabled=True))
    self._TestUpdate(update=update, flags='--enable-vertical-pod-autoscaling')

  def _TestUpdate(self, update, flags):
    self._TestUpdateNoAsync(update, flags)
    self._TestUpdateAsync(update, flags)

  def _TestUpdateNoAsync(self, update, flags):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))
    self.AssertErrContains(
        ('go to: https://console.cloud.google.com/kubernetes/'
         'workload_/gcloud/{zone}/{cluster}?project={project}').format(
             cluster=name, zone=self.ZONE, project=self.PROJECT_ID))

  def _TestUpdateAsync(self, update, flags):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    if 'NodeLocalDNS' in flags:
      self.WriteInput('y')
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1} --async'.format(name, flags))

  def _TestUpdateAbort(self, update, flags):
    name = 'tobeaborted'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.WriteInput('n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Aborted by user.')
    self.AssertErrContains(
        'Enabling/Disabling NodeLocal DNSCache causes '
        'a re-creation of all cluster nodes at versions 1.15 or above.'
        ' This operation is long-running and will block other '
        'operations on the cluster (including delete) until it has run'
        ' to completion.')

  def _TestUpdateMasterAuth(self, action, update, password, flags):
    name = 'tosetmasterauth'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetMasterAuth(
        cluster_name=name,
        action=action,
        update=update,
        response=self._MakeOperation(operationType=self.op_set_master_auth))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.WriteInput(password + '\n')
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestUpdateAdditionalZonesRemove(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredLocations=[self.ZONE]),
        flags='--additional-zones=""')

  def _TestUpdateAdditionalZonesAdd(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredLocations=sorted(
                [self.ZONE, 'us-central1-a', 'moon-north3-z'])),
        flags='--additional-zones=us-central1-a,moon-north3-z')

  def _TestUpdateLabels(self, location):
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue(
        additionalProperties=[
            self.msgs.SetLabelsRequest.ResourceLabelsValue.AdditionalProperty(
                key='k', value='v')
        ],)
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name), zone=location)
    self.ExpectGetCluster(self._RunningCluster(name=name), zone=location)
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(
            operationType=self.op_set_labels, zone=location),
        zone=location)
    self.ExpectGetOperation(
        self._MakeOperation(status=self.op_done, zone=location))
    if location == self.REGION:
      self.Run(
          self.regional_clusters_command_base.format(self.REGION) +
          ' update {0} --update-labels=k=v'.format(name))
    else:
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} --update-labels=k=v'.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestUpdateLabelsToSame(self):
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue(
        additionalProperties=[
            self.msgs.SetLabelsRequest.ResourceLabelsValue.AdditionalProperty(
                key='k', value='v')
        ],)
    name = 'tobeupdatedsame'
    cluster_kwargs = {
        'name':
            name,
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                ],),
    }
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} --update-labels=k=v'.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestUpdateLabelsToEmpty(self):
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue()
    name = 'tobeupdatedempty'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} --update-labels='.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestRemoveLabels(self):
    name = 'toberemoved'
    cluster_kwargs = {
        'name':
            name,
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k2', value='v2'),
                ],),
    }
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue(
        additionalProperties=[
            self.msgs.SetLabelsRequest.ResourceLabelsValue.AdditionalProperty(
                key='k', value='v')
        ],)
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} --remove-labels=k2'.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestRemoveAllLabels(self):
    name = 'alltoberemoved'
    cluster_kwargs = {
        'name':
            name,
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k2', value='v2'),
                ],),
    }
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue()
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} --remove-labels=k,k2'.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestRemoveNoLabels(self):
    name = 'nonetoberemoved'
    cluster_kwargs = {
        'name':
            name,
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k2', value='v2'),
                ],),
    }
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue(
        additionalProperties=[
            self.msgs.SetLabelsRequest.ResourceLabelsValue.AdditionalProperty(
                key='k', value='v'),
            self.msgs.SetLabelsRequest.ResourceLabelsValue.AdditionalProperty(
                key='k2', value='v2')
        ],)
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} --remove-labels='.format(name))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestRemoveFromClusterWithNoLabels(self):
    name = 'toberemovednolabels'
    cluster_kwargs = {'name': name}
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} --remove-labels=k'.format(name))
      self.AssertErrContains(
          'Cluster \'{0}\' has no labels to remove.'.format(name))

  def _TestRemoveNonExistentLabel(self):
    name = 'toberemovednonexistentlabel'
    cluster_kwargs = {
        'name':
            name,
        'labels':
            self.msgs.Cluster.ResourceLabelsValue(
                additionalProperties=[
                    self.msgs.Cluster.ResourceLabelsValue.AdditionalProperty(
                        key='k', value='v'),
                ],),
    }
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} --remove-labels=k2'.format(name))
      self.AssertErrContains('No label named \'k2\' found on cluster')

  def testSetNetworkPolicySuccess(self):
    """Correctly handle the success case."""
    name = 'tosetnetworkpolicy'
    self.WriteInput('y')
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetNetworkPolicy(
        cluster_name=name,
        response=self._MakeOperation(operationType=self.op_set_master_auth))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--enable-network-policy'))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def testSetNetworkPolicyAbort(self):
    """Correctly handle the success case."""
    name = 'tosetnetworkpolicy'
    self.WriteInput('n')
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(name, '--enable-network-policy'))
    self.AssertErrContains('Aborted by user.')

  def _MP(self, resource_version=None, window=None, exclusions=None):
    """Creates a maintenance policy for ease of tests."""
    mp = self.msgs.MaintenancePolicy(
        window=self.msgs.MaintenanceWindow(), resourceVersion=resource_version)

    if isinstance(window, self.msgs.RecurringTimeWindow):
      mp.window.recurringWindow = window
    elif isinstance(window, self.msgs.DailyMaintenanceWindow):
      mp.window.dailyMaintenanceWindow = window
    elif window is not None:
      self.fail('Bad window: {0}'.format(window))

    if exclusions is not None:
      exclusions_val = self.msgs.MaintenanceWindow.MaintenanceExclusionsValue()
      exclusions_val.additionalProperties = exclusions
      mp.window.maintenanceExclusions = exclusions_val

    return mp

  def _DailyWindow(self, start_time):
    return self.msgs.DailyMaintenanceWindow(startTime=start_time)

  def _RecurringWindow(self, start, end, recur):
    return self.msgs.RecurringTimeWindow(
        window=self.msgs.TimeWindow(startTime=start, endTime=end),
        recurrence=recur)

  def _Exclusion(self, start, end, name):
    exclusions_value = self.msgs.MaintenanceWindow.MaintenanceExclusionsValue
    return exclusions_value.AdditionalProperty(
        key=name, value=self.msgs.TimeWindow(startTime=start, endTime=end))

  def _TestExpectedMaintenancePolicyRequests(self, cluster, policy):
    self.ExpectGetCluster(cluster)
    self.ExpectSetMaintenancePolicy(
        cluster_name=cluster.name,
        policy=policy,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))

  def testSetMaintenanceWindow(self):
    name = 'testSetMaintenanceWindow'
    cluster = self._RunningCluster(name=name)
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            resource_version='emptyRV', window=self._DailyWindow('11:43')))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--maintenance-window=11:43'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetMaintenanceWindowNone(self):
    name = 'setMaintenanceWindowNone'
    self._TestExpectedMaintenancePolicyRequests(
        cluster=self._RunningCluster(
            name=name,
            maintenancePolicy=self._MP(
                resource_version='1143RV', window=self._DailyWindow('11:43'))),
        policy=self._MP(resource_version='1143RV'))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--maintenance-window=None'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetMaintenancePolicyWhenNoExistingPolicy(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(name=name)
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'emptyRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY')))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--maintenance-window-start=2000-01-01T09:00:00Z '
            '--maintenance-window-end=2000-01-01T17:00:00Z '
            '--maintenance-window-recurrence=FREQ=DAILY'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetRecurringMaintenancePolicyWhenExistingDailyPolicy(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP('1143RV', window=self._DailyWindow('11:43')))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            '1143RV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY')))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--maintenance-window-start=2000-01-01T09:00:00Z '
            '--maintenance-window-end=2000-01-01T17:00:00Z '
            '--maintenance-window-recurrence=FREQ=DAILY'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetDailyMaintenancePolicyWhenExistingRecurringPolicy(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY')))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP('someRV', window=self._DailyWindow('11:43')))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--maintenance-window=11:43'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetDailyMaintenancePolicyWithExistingExclusions(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--maintenance-window-start=2000-01-01T09:00:00Z '
            '--maintenance-window-end=2000-01-01T17:00:00Z '
            '--maintenance-window-recurrence=FREQ=DAILY'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetRecurringMaintenancePolicyWithExistingExclusions(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            '1143RV',
            window=self._DailyWindow('11:43'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            '1143RV',
            window=self._DailyWindow('11:43'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--maintenance-window=11:43'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testSetMaintenancePolicyBadTimes(self):
    with self.AssertRaisesArgumentErrorMatches('Failed to parse date/time'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(
              'emwCluster', '--maintenance-window-start=2000-00-01T09:00:00Z '
              '--maintenance-window-end=2000-13-01T17:00:00Z '
              '--maintenance-window-recurrence=FREQ=DAILY'))

  @parameterized.parameters(
      ('--maintenance-window-start=2000-01-01T09:00:00Z '
       '--maintenance-window-recurrence=FREQ=DAILY',
       '--maintenance-window-end'),
      ('--maintenance-window-end=2000-01-01T17:00:00Z '
       '--maintenance-window-recurrence=FREQ=DAILY',
       '--maintenance-window-start'),
      ('--maintenance-window-start=2000-01-01T09:00:00Z '
       '--maintenance-window-end=2000-01-01T17:00:00Z',
       '--maintenance-window-recurrence'),
  )
  def testSetMaintenancePolicyMissingFields(self, flags, error_flag):
    name = 'emwCluster'
    with self.AssertRaisesArgumentErrorMatches(
        'argument {0}: Must be specified.'.format(error_flag)):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(name, flags))

  def testRemoveMaintenanceWindow(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'someRV',
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, '--clear-maintenance-window'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testRemoveMaintenanceWindowWhenNoWindow(self):
    name = 'emwCluster'
    self.ExpectGetCluster(
        self._RunningCluster(
            name=name,
            maintenancePolicy=self._MP(
                'someRV',
                exclusions=[
                    self._Exclusion('2000-01-01T00:00:00+00:00',
                                    '2000-01-07T00:00:00+00:00', 'first-week')
                ])))
    with self.AssertRaisesExceptionMatches(
        c_util.Error, api_adapter.NOTHING_TO_UPDATE_ERROR_MSG):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(name, '--clear-maintenance-window'))

  def testAddMaintenanceExclusionWhenNoExistingPolicy(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(name=name)
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'emptyRV',
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week')
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--add-maintenance-exclusion-start=2000-01-01T00:00:00Z '
            '--add-maintenance-exclusion-end=2000-01-07T00:00:00Z '
            '--add-maintenance-exclusion-name=first-week'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testAddMaintenanceExclusionWhenExistingPolicy(self):
    name = 'emwCluster'
    self._TestExpectedMaintenancePolicyRequests(
        cluster=self._RunningCluster(
            name=name,
            maintenancePolicy=self._MP(
                'someRV',
                window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                             '2000-01-01T17:00:00+00:00',
                                             'FREQ=DAILY'))),
        policy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week'),
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--add-maintenance-exclusion-start=2000-01-01T00:00:00Z '
            '--add-maintenance-exclusion-end=2000-01-07T00:00:00Z '
            '--add-maintenance-exclusion-name=first-week'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testAddMaintenanceExclusionWhenExistingExclusions(self):
    name = 'emwCluster'
    self._TestExpectedMaintenancePolicyRequests(
        cluster=self._RunningCluster(
            name=name,
            maintenancePolicy=self._MP(
                'someRV',
                window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                             '2000-01-01T17:00:00+00:00',
                                             'FREQ=DAILY'),
                exclusions=[
                    self._Exclusion('2000-01-01T00:00:00+00:00',
                                    '2000-01-07T00:00:00+00:00', 'first-week'),
                ])),
        policy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week'),
                self._Exclusion('2000-01-07T00:00:00+00:00',
                                '2000-01-14T00:00:00+00:00', 'second-week'),
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--add-maintenance-exclusion-start=2000-01-07T00:00:00Z '
            '--add-maintenance-exclusion-end=2000-01-14T00:00:00Z '
            '--add-maintenance-exclusion-name=second-week'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testAddMaintenanceExclusionWithMinimalInfo(self):
    self.StartObjectPatch(
        times,
        'Now',
        return_value=times.ParseDateTime('2000-01-01T09:00:00-04:00'))

    name = 'emwCluster'
    cluster = self._RunningCluster(name=name)
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'emptyRV',
            exclusions=[
                self._Exclusion(
                    '2000-01-01T09:00:00-04:00', '2000-01-10T12:00:00-04:00',
                    'generated-exclusion-2000-01-01T09:00:00-04:00')
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--add-maintenance-exclusion-end=2000-01-10T12:00:00-04:00'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testRemoveMaintenanceExclusion(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week'),
                self._Exclusion('2000-01-07T00:00:00+00:00',
                                '2000-01-14T00:00:00+00:00', 'second-week'),
                self._Exclusion('2000-01-14T00:00:00+00:00',
                                '2000-01-21T00:00:00+00:00', 'third-week'),
            ]))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster,
        policy=self._MP(
            'someRV',
            window=self._RecurringWindow('2000-01-01T09:00:00+00:00',
                                         '2000-01-01T17:00:00+00:00',
                                         'FREQ=DAILY'),
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week'),
                self._Exclusion('2000-01-14T00:00:00+00:00',
                                '2000-01-21T00:00:00+00:00', 'third-week'),
            ]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--remove-maintenance-exclusion=second-week'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testRemoveOnlyMaintenanceExclusion(self):
    name = 'emwCluster'
    cluster = self._RunningCluster(
        name=name,
        maintenancePolicy=self._MP(
            'someRV',
            exclusions=[
                self._Exclusion('2000-01-01T00:00:00+00:00',
                                '2000-01-07T00:00:00+00:00', 'first-week'),
            ]))
    self._TestExpectedMaintenancePolicyRequests(
        cluster=cluster, policy=self._MP('someRV', exclusions=[]))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--remove-maintenance-exclusion=first-week'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testRemoveMaintenanceExclusionNonExisting(self):
    name = 'emwCluster'
    self.ExpectGetCluster(
        self._RunningCluster(
            name=name,
            maintenancePolicy=self._MP(
                'someRV',
                exclusions=[
                    self._Exclusion('2000-01-01T00:00:00+00:00',
                                    '2000-01-07T00:00:00+00:00', 'first-week'),
                    self._Exclusion('2000-01-14T00:00:00+00:00',
                                    '2000-01-21T00:00:00+00:00', 'third-week'),
                ])))
    with self.AssertRaisesExceptionMatches(
        c_util.Error,
        'No maintenance exclusion with name second-week exists. Existing '
        'exclusions: first-week, third-week'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(
              name, '--remove-maintenance-exclusion=second-week'))

  def testRemoveMaintenanceExclusionNoPolicy(self):
    name = 'emwCluster'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.AssertRaisesExceptionMatches(
        c_util.Error, 'No maintenance exclusion with name first-week exists.'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update {0} {1}'.format(name,
                                   '--remove-maintenance-exclusion=first-week'))

  def testUpdateLabels(self):
    self._TestUpdateLabels(self.ZONE)

  def testUpdateLabelsToSame(self):
    self._TestUpdateLabelsToSame()

  def testUpdateLabelsToEmpty(self):
    self._TestUpdateLabelsToEmpty()

  def testRemoveLabels(self):
    self._TestRemoveLabels()

  def testRemoveNoLabels(self):
    self._TestRemoveNoLabels()

  def testRemoveAllLabels(self):
    self._TestRemoveAllLabels()

  def testRemoveNonExistentLabel(self):
    self._TestRemoveNonExistentLabel()

  def testRemoveFromClusterWithNoLabels(self):
    self._TestRemoveFromClusterWithNoLabels()

  def testCanUpdateAfterFailedGet(self):
    # Updating monitoring as example.
    update = self.msgs.ClusterUpdate(desiredMonitoringService='none')
    flags = '--monitoring-service=none'
    name = 'tobeupdated'
    cluster = self._RunningCluster(name=name)
    self.ExpectGetCluster(
        cluster,
        exception=apitools_exceptions.HttpForbiddenError(
            {
                'status': 403,
                'reason': 'missing update permission'
            }, 'forbidden', 'foo.com/bar'))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))
    self.AssertErrContains(
        ('go to: https://console.cloud.google.com/kubernetes/'
         'workload_/gcloud/{zone}/{cluster}?project={project}').format(
             cluster=name, zone=self.ZONE, project=self.PROJECT_ID))

  def testResourceUsageExportConfig(self):
    self._TestUpdateResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=updated_dataset_id',
        self.msgs.ResourceUsageExportConfig(
            bigqueryDestination=self.msgs.BigQueryDestination(
                datasetId='updated_dataset_id'),
            consumptionMeteringConfig=None))
    self._TestUpdateResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=updated_dataset_id '
        '--enable-network-egress-metering',
        self.msgs.ResourceUsageExportConfig(
            bigqueryDestination=self.msgs.BigQueryDestination(
                datasetId='updated_dataset_id'),
            enableNetworkEgressMetering=True,
            consumptionMeteringConfig=None))
    self._TestUpdateResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=updated_dataset_id '
        '--no-enable-network-egress-metering',
        self.msgs.ResourceUsageExportConfig(
            bigqueryDestination=self.msgs.BigQueryDestination(
                datasetId='updated_dataset_id'),
            consumptionMeteringConfig=None))
    self._TestUpdateResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=updated_dataset_id '
        '--enable-resource-consumption-metering',
        self.msgs.ResourceUsageExportConfig(
            bigqueryDestination=self.msgs.BigQueryDestination(
                datasetId='updated_dataset_id'),
            consumptionMeteringConfig=self.msgs.ConsumptionMeteringConfig(
                enabled=True)))
    self._TestUpdateResourceUsageExportConfig(
        '--resource-usage-bigquery-dataset=updated_dataset_id '
        '--no-enable-resource-consumption-metering',
        self.msgs.ResourceUsageExportConfig(
            bigqueryDestination=self.msgs.BigQueryDestination(
                datasetId='updated_dataset_id'),
            consumptionMeteringConfig=self.msgs.ConsumptionMeteringConfig(
                enabled=False)))

  def _TestUpdateResourceUsageExportConfig(self, flags, export_config):
    update = self.msgs.ClusterUpdate(
        desiredResourceUsageExportConfig=export_config)
    self._TestUpdate(update=update, flags=flags)

  def testResourceUsageExportConfigInvalid(self):
    with self.AssertRaisesExceptionMatches(
        c_util.Error, api_adapter.ENABLE_NETWORK_EGRESS_METERING_ERROR_MSG):
      self.ExpectGetCluster(self._RunningCluster(name=self.CLUSTER_NAME))
      self.Run('{base} update {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags='--enable-network-egress-metering'))
    with self.AssertRaisesExceptionMatches(
        c_util.Error,
        api_adapter.ENABLE_RESOURCE_CONSUMPTION_METERING_ERROR_MSG):
      self.ExpectGetCluster(self._RunningCluster(name=self.CLUSTER_NAME))
      self.Run('{base} update {name} --quiet {flags}'.format(
          base=self.clusters_command_base.format(self.ZONE),
          name=self.CLUSTER_NAME,
          flags='--enable-resource-consumption-metering'))

  def testClearResourceUsageBigqueryDataset(self):
    export_config = self.msgs.ResourceUsageExportConfig()
    update = self.msgs.ClusterUpdate(
        desiredResourceUsageExportConfig=export_config)
    self._TestUpdate(
        update=update, flags='--clear-resource-usage-bigquery-dataset')

  def testEnableDatabaseEncryption(self):
    update = self.msgs.ClusterUpdate(
        desiredDatabaseEncryption=self.msgs.DatabaseEncryption(
            keyName='projects/p/locations/l/keyRings/kr/cryptoKeys/k',
            state=self.msgs.DatabaseEncryption.StateValueValuesEnum.ENCRYPTED))
    self._TestUpdate(
        update=update,
        flags='--database-encryption-key=projects/p/locations/l/keyRings/kr/cryptoKeys/k '
    )

  def testDisableDatabaseEncryption(self):
    update = self.msgs.ClusterUpdate(
        desiredDatabaseEncryption=self.msgs.DatabaseEncryption(
            state=self.msgs.DatabaseEncryption.StateValueValuesEnum.DECRYPTED))
    self._TestUpdate(update=update, flags='--disable-database-encryption ')

  def testEnableAutoprovisioning(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8')

  def testEnableAutoprovisioningWithAcceleratorMaxLimit(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-k80', minimum=0, maximum=2)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--max-accelerator type=nvidia-tesla-k80,count=2')

  def testEnableAutoprovisioningWithUpgradeSettings(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-max-surge-upgrade=1 '
        '--autoprovisioning-max-unavailable-upgrade=2 ')

  def testEnableAutoprovisioningWithNodeManagement(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade')

  def testEnableAutoprovisioningWithNodeManagementAndUpgradeSettings(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-max-surge-upgrade=1 '
        '--autoprovisioning-max-unavailable-upgrade=2 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade ')

  def testEnableAutoprovisioningWithManagementFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
  autoUpgrade: true
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithUpgradeSettingsFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
  maxUnavailableUpgrade: 2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithAcceleratorLimits(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-k80', minimum=1, maximum=2)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--max-accelerator type=nvidia-tesla-k80,count=2 '
        '--min-accelerator type=nvidia-tesla-k80,count=1')

  def testDisableAutoprovisioning(self):
    self._TestUpdateAutoprovisioning(
        enabled=False,
        resource_limits=[],
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[]),
        autoprovisioning_locations=[],
        flags='--no-enable-autoprovisioning')

  def _TestUpdateAutoprovisioning(self, enabled, resource_limits,
                                  autoprovisioning_defaults,
                                  autoprovisioning_locations, flags):
    autoscaling = self.msgs.ClusterAutoscaling(
        enableNodeAutoprovisioning=enabled,
        resourceLimits=resource_limits,
        autoprovisioningNodePoolDefaults=autoprovisioning_defaults,
        autoprovisioningLocations=autoprovisioning_locations)
    update = self.msgs.ClusterUpdate(desiredClusterAutoscaling=autoscaling)
    self._TestUpdate(update=update, flags=flags)

  def testEnableAutoprovisioningWithServiceAccount(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            serviceAccount='sa1',
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-service-account=sa1')

  def testEnableAutoprovisioningWithScopes(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            oauthScopes=['scope1', 'scope2'],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-scopes=scope1,scope2')

  def testEnableAutoprovisioningWithScopesAndServiceAccount(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            serviceAccount='sa',
            oauthScopes=['scope1', 'scope2'],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-scopes=scope1,scope2 '
        '--autoprovisioning-service-account=sa')

  def testEnableAutoprovisioningWithScopesFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
scopes:
  - scope1
  - scope2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            oauthScopes=['scope1', 'scope2'],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithServiceAccountFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
serviceAccount: sa1
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            serviceAccount='sa1',
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithLocations(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=['us-central1-a', 'us-central1-b'],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-locations=us-central1-a,us-central1-b ')

  def testEnableAutoprovisioningNoLimits(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[],
        autoprovisioning_locations=['us-central1-a', 'us-central1-b'],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-locations=us-central1-a,us-central1-b ')

  def testEnableAutoprovisioningWithLocationsFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
autoprovisioningLocations:
  - us-central1-a
  - us-central1-b
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=['us-central1-a', 'us-central1-b'],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningAcceleratorTypeMismatch(self):
    flags = (' --enable-autoprovisioning --max-cpu 10 --max-memory 64'
             ' --max-accelerator type=nvidia-tesla-p100,count=2'
             ' --min-accelerator type=nvidia-tesla-k80,count=1')
    error_message = ('Maximum and minimum accelerator limits must be set'
                     ' on the same accelerator type.')
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaisesRegex(c_util.Error, error_message):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update ' + name +
          flags)

  def testEnableAutoprovisioningWithMultipleAcceleratorLimits(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
  - resourceType: 'nvidia-tesla-k80'
    minimum: 1
    maximum: 2
  - resourceType: 'nvidia-tesla-p100'
    minimum: 0
    maximum: 1
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.messages
        .AutoprovisioningNodePoolDefaults(oauthScopes=[],),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-k80', minimum=1, maximum=2),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-p100', minimum=0, maximum=1)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testDisableWorkloadIdentity(self):
    update = self.msgs.ClusterUpdate(
        desiredWorkloadIdentityConfig=self.msgs.WorkloadIdentityConfig(
            workloadPool=''))
    self._TestUpdate(update=update, flags='--disable-workload-identity ')

  def testUpdateWorkloadIdentity(self):
    update = self.msgs.ClusterUpdate(
        desiredWorkloadIdentityConfig=self.msgs.WorkloadIdentityConfig(
            workloadPool='foobar.svc.id.goog'))
    self._TestUpdate(update=update, flags='--workload-pool=foobar.svc.id.goog ')

  @parameterized.parameters(
      ('--no-enable-shielded-nodes', False),
      ('--enable-shielded-nodes', True),
  )
  def testEnableShieldedNodes(self, flags, enabled):
    cluster_name = 'abc'
    update = self.msgs.ClusterUpdate(
        desiredShieldedNodes=self.msgs.ShieldedNodes(enabled=enabled))
    self.ExpectGetCluster(self._RunningCluster(name=cluster_name))
    self.ExpectUpdateCluster(
        cluster_name=cluster_name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(cluster_name, flags))

  def testUpdateMonitoringAndLogging(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='some.monitoring.service',
            desiredLoggingService='some.logging.service'),
        flags='--monitoring-service=some.monitoring.service '
        '--logging-service=some.logging.service')

  @parameterized.parameters('rapid', 'regular', 'stable', 'None')
  def testUpdateReleaseChannel(self, channel):
    channels = {
        'rapid': self.messages.ReleaseChannel.ChannelValueValuesEnum.RAPID,
        'regular': self.messages.ReleaseChannel.ChannelValueValuesEnum.REGULAR,
        'stable': self.messages.ReleaseChannel.ChannelValueValuesEnum.STABLE,
        'None': self.messages.ReleaseChannel.ChannelValueValuesEnum.UNSPECIFIED,
    }
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredReleaseChannel=self.messages.ReleaseChannel(
                channel=channels[channel])),
        flags='--release-channel={rc}'.format(rc=channel))

  @parameterized.parameters('invalid', 'Rapid', 'RAPID', 'Regular', 'REGULAR',
                            'Stable', 'STABLE', 'none', 'NONE')
  def testUpdateReleaseChannelInvalidChannelError(self, channel_name):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'Invalid choice'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update test-cluster --release-channel={0}'.format(channel_name))

  @parameterized.parameters(
      ('--enable-master-global-access ', True),
      ('--no-enable-master-global-access ', False),
  )
  def testMasterGlobalAccess(self, flags, enabled):
    master_global_access_config = self.msgs.PrivateClusterMasterGlobalAccessConfig(
        enabled=enabled)
    desired = self.msgs.PrivateClusterConfig(
        masterGlobalAccessConfig=master_global_access_config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredPrivateClusterConfig=desired),
        flags=flags)


# TODO(b/64575339): switch to use parameterized testing.
# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestBeta(base.BetaTestBase, UpdateTestGA):
  """gcloud Beta track using container v1beta1 API."""

  def testUpdateAdditionalZonesRemove(self):
    self._TestUpdateAdditionalZonesRemove()

  def testUpdateAdditionalZonesAdd(self):
    self._TestUpdateAdditionalZonesAdd()

  def testRegionalUpdateLabels(self):
    self._TestUpdateLabels(self.REGION)

  def testUpdateAddonsNetworkPolicy(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=False))),
        flags='--update-addons NetworkPolicy=ENABLED')

    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                networkPolicyConfig=self.msgs.NetworkPolicyConfig(
                    disabled=True))),
        flags='--update-addons NetworkPolicy=DISABLED')

  def testUpdateAddonsNodeLocalDNS(self):
    self.WriteInput('y')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=False))),
        flags='--update-addons NodeLocalDNS=DISABLED')

    self.WriteInput('y')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True))),
        flags='--update-addons NodeLocalDNS=ENABLED')

    self._TestUpdateAbort(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=False))),
        flags='--update-addons NodeLocalDNS=DISABLED')

    self._TestUpdateAbort(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                dnsCacheConfig=self.msgs.DnsCacheConfig(enabled=True))),
        flags='--update-addons NodeLocalDNS=ENABLED')

  def testUpdateAddonsGcePersistentDiskCsiDriver(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                gcePersistentDiskCsiDriverConfig=self.msgs
                .GcePersistentDiskCsiDriverConfig(enabled=True))),
        flags='--update-addons GcePersistentDiskCsiDriver=ENABLED')

    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                gcePersistentDiskCsiDriverConfig=self.msgs
                .GcePersistentDiskCsiDriverConfig(enabled=False))),
        flags='--update-addons GcePersistentDiskCsiDriver=DISABLED')

  def testUpdateLocations(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredLocations=sorted(['us-central1-a', 'moon-north3-z'])),
        flags='--node-locations=us-central1-a,moon-north3-z')

  def testUpdateEnablePodSecurityPolicy(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredPodSecurityPolicyConfig=self.msgs.PodSecurityPolicyConfig(
                enabled=True)),
        flags='--enable-pod-security-policy')

  def testEnableBinaryAuthorization(self):
    self._TestEnableBinaryAuthorization(enabled=True, flags='--enable-binauthz')

  def _TestEnableBinaryAuthorization(self, enabled, flags):
    binauthz = self.msgs.BinaryAuthorization(enabled=enabled)
    update = self.msgs.ClusterUpdate(desiredBinaryAuthorization=binauthz)
    self._TestUpdate(update=update, flags=flags)

  def testEnableAutoprovisioningWithUpgradeSettings(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-max-surge-upgrade=1 '
        '--autoprovisioning-max-unavailable-upgrade=2 ')

  def testEnableAutoprovisioningWithNodeManagement(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade')

  def testEnableAutoprovisioningWithNodeManagementAndUpgradeSettings(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-max-surge-upgrade=1 '
        '--autoprovisioning-max-unavailable-upgrade=2 '
        '--no-enable-autoprovisioning-autorepair '
        '--enable-autoprovisioning-autoupgrade ')

  def testEnableAutoprovisioningWithManagementFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
management:
  autoRepair: false
  autoUpgrade: true
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            management=self.msgs.NodeManagement(
                autoRepair=False, autoUpgrade=True),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithUpgradeSettingsFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
upgradeSettings:
  maxSurgeUpgrade: 1
  maxUnavailableUpgrade: 2
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            upgradeSettings=self.msgs.UpgradeSettings(
                maxSurge=1, maxUnavailable=2),
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithMinCpuPlatformFromFile(self):
    autoprovisioning_config_file = self.Touch(
        self.temp_path,
        'autoprovisioning-config',
        contents="""
minCpuPlatform: 'Skylake'
resourceLimits:
  - resourceType: 'cpu'
    minimum: 8
    maximum: 100
  - resourceType: 'memory'
    maximum: 20
        """)
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            minCpuPlatform='Skylake',
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=20)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning '
        '--autoprovisioning-config-file {}'.format(
            autoprovisioning_config_file))

  def testEnableAutoprovisioningWithMinCpuPlatform(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        autoprovisioning_defaults=self.msgs.AutoprovisioningNodePoolDefaults(
            minCpuPlatform='Skylake',
            oauthScopes=[],
        ),
        resource_limits=[
            self.msgs.ResourceLimit(resourceType='cpu', maximum=100, minimum=8),
            self.msgs.ResourceLimit(resourceType='memory', maximum=128)
        ],
        autoprovisioning_locations=[],
        flags='--enable-autoprovisioning --max-memory 128 '
        '--max-cpu 100 --min-cpu 8 '
        '--autoprovisioning-min-cpu-platform Skylake ')

  def testUpdateAutoscalingProfile(self):
    autoscaling = self.msgs.ClusterAutoscaling(
        autoscalingProfile=(
            self.messages.ClusterAutoscaling.AutoscalingProfileValueValuesEnum
            .OPTIMIZE_UTILIZATION))
    self._TestUpdateClusterAutoscaling(
        autoscaling, '--autoscaling-profile optimize-utilization')

  def testUpdateAutoscalingProfileInvalid(self):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update ' + name +
          ' --autoscaling-profile invalid-profile')

  def _TestUpdateClusterAutoscaling(self, autoscaling, flags):
    name = 'tobeupdated'
    update = self.msgs.ClusterUpdate(desiredClusterAutoscaling=autoscaling)
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))

    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))

    self.AssertErrContains('Updating {cluster}'.format(cluster=name))
    self.AssertErrContains(
        ('go to: https://console.cloud.google.com/kubernetes/'
         'workload_/gcloud/{zone}/{cluster}?project={project}').format(
             cluster=name, zone=self.ZONE, project=self.PROJECT_ID))

  def _TestUpdateAutoprovisioning(self, enabled, resource_limits,
                                  autoprovisioning_defaults,
                                  autoprovisioning_locations, flags):
    autoscaling = self.msgs.ClusterAutoscaling(
        enableNodeAutoprovisioning=enabled,
        autoprovisioningNodePoolDefaults=autoprovisioning_defaults,
        resourceLimits=resource_limits,
        autoprovisioningLocations=autoprovisioning_locations)
    self._TestUpdateClusterAutoscaling(autoscaling, flags)

  def testEnableAutoprovisioningAcceleratorTypeMismatch(self):
    flags = (' --enable-autoprovisioning --max-cpu 10 --max-memory 64'
             ' --max-accelerator type=nvidia-tesla-p100,count=2'
             ' --min-accelerator type=nvidia-tesla-k80,count=1')
    error_message = ('Maximum and minimum accelerator limits must be set'
                     ' on the same accelerator type.')
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaisesRegex(c_util.Error, error_message):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update ' + name +
          flags)

  def testUpdateMonitoring(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='some.monitoring.service'),
        flags='--monitoring-service=some.monitoring.service ')

  def testEnableVerticalPodAutoscaling(self):
    update = self.msgs.ClusterUpdate(
        desiredVerticalPodAutoscaling=self.msgs.VerticalPodAutoscaling(
            enabled=True))
    self._TestUpdate(update=update, flags='--enable-vertical-pod-autoscaling')

  def testEnableIntraNodeVisibility(self):
    update = self.msgs.ClusterUpdate(
        desiredIntraNodeVisibilityConfig=self.msgs.IntraNodeVisibilityConfig(
            enabled=True))
    self._TestUpdate(update=update, flags='--enable-intra-node-visibility')

  def testUpdateAddonsIstio(self):
    auth_none = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_NONE
    auth_mtls = self.messages.IstioConfig.AuthValueValuesEnum.AUTH_MUTUAL_TLS
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                istioConfig=self.msgs.IstioConfig(
                    disabled=True, auth=auth_none))),
        flags='--update-addons Istio=DISABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                istioConfig=self.msgs.IstioConfig(
                    disabled=False, auth=auth_none))),
        flags='--update-addons Istio=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                istioConfig=self.msgs.IstioConfig(
                    disabled=False, auth=auth_none))),
        flags='--update-addons Istio=ENABLED '
        '--istio-config auth='
        'MTLS_PERMISSIVE')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                istioConfig=self.msgs.IstioConfig(
                    disabled=False, auth=auth_mtls))),
        flags='--update-addons Istio=ENABLED --istio-config auth=MTLS_STRICT')

  def testUpdateAddonsValidateDep(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.ExpectGetCluster(self._RunningCluster(name='clustername'))
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update clustername --update-addons=Istio=DISABLED '
          '--istio-config auth=MTLS_STRICT')
    self.AssertErrContains('update-addons=Istio=ENABLED must be specified')

  def testUpdateAddonsValidateOpt(self):
    with self.assertRaises(exceptions.InvalidArgumentException):
      self.ExpectGetCluster(self._RunningCluster(name='clustername'))
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update clustername --update-addons=Istio=ENABLED '
          '--istio-config auth=MUUAL_TLS')
    self.AssertErrContains('auth must be one of MTLS_PERMISSIVE or '
                           'MTLS_STRICT')

  def testUpdateWorkloadIdentityConfigIdentityProvider(self):
    update = self.msgs.ClusterUpdate(
        desiredWorkloadIdentityConfig=self.msgs.WorkloadIdentityConfig(
            identityProvider='https://gkehub.googleapis.com/projects/test/locations/global/memberships/new-test'
        ))
    self._TestUpdate(
        update=update,
        flags='--identity-provider=https://gkehub.googleapis.com/projects/test/locations/global/memberships/new-test '
    )

  def testEnableDatabaseEncryption(self):
    update = self.msgs.ClusterUpdate(
        desiredDatabaseEncryption=self.msgs.DatabaseEncryption(
            keyName='projects/p/locations/l/keyRings/kr/cryptoKeys/k',
            state=self.msgs.DatabaseEncryption.StateValueValuesEnum.ENCRYPTED))
    self._TestUpdate(
        update=update,
        flags='--database-encryption-key=projects/p/locations/l/keyRings/kr/cryptoKeys/k '
    )

  def testDisableDatabaseEncryption(self):
    update = self.msgs.ClusterUpdate(
        desiredDatabaseEncryption=self.msgs.DatabaseEncryption(
            state=self.msgs.DatabaseEncryption.StateValueValuesEnum.DECRYPTED))
    self._TestUpdate(update=update, flags='--disable-database-encryption ')

  def testUpdateAddonsApplicationManager(self):
    # test disabling ApplicationManager
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kalmConfig=self.msgs.KalmConfig(enabled=False))),
        flags='--update-addons ApplicationManager=DISABLED')
    # test enabling ApplicationManager
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kalmConfig=self.msgs.KalmConfig(enabled=True))),
        flags='--update-addons ApplicationManager=ENABLED')

  @parameterized.parameters(True, False)
  def testTpuUpdate(self, enabled):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredTpuConfig=self.msgs.TpuConfig(enabled=enabled)),
        flags='--enable-tpu' if enabled else '--no-enable-tpu')

  @parameterized.parameters('', '/20')
  def testTpuEnableWithIpv4Cidr(self, tpu_ipv4_cidr):
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredTpuConfig=self.msgs.TpuConfig(
                enabled=True, ipv4CidrBlock=tpu_ipv4_cidr)),
        flags='--enable-tpu --tpu-ipv4-cidr=' + tpu_ipv4_cidr)

  def testEnableStackdriverKubernetesOnly(self):
    desired = self.msgs.ClusterTelemetry(
        type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.ENABLED)
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredClusterTelemetry=desired),
        flags='--enable-stackdriver-kubernetes')

  def testEnableLoggingMonitoringSystemOnly(self):
    desired = self.msgs.ClusterTelemetry(
        type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.SYSTEM_ONLY)
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredClusterTelemetry=desired),
        flags='--enable-logging-monitoring-system-only')

  def testDisableClusterTelemetry(self):
    desired = self.msgs.ClusterTelemetry(
        type=self.msgs.ClusterTelemetry.TypeValueValuesEnum.DISABLED)
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredClusterTelemetry=desired),
        flags='--no-enable-stackdriver-kubernetes')

  def testEnableGvnic(self):
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredEnableGvnic=True),
        flags='--enable-gvnic')

  def testApiserverLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.APISERVER,
    ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master),
        flags='--master-logs APISERVER')

  def testSchedulerLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.SCHEDULER,
    ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master),
        flags='--master-logs SCHEDULER')

  def testControllerManagerLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.CONTROLLER_MANAGER,
    ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master),
        flags='--master-logs CONTROLLER_MANAGER')

  def testAddonManagerLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.ADDON_MANAGER,
    ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master),
        flags='--master-logs ADDON_MANAGER')

  def testAllMasterLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.APISERVER,
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.SCHEDULER,
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.CONTROLLER_MANAGER,
        self.msgs.MasterSignalsConfig
        .LogEnabledComponentsValueListEntryValuesEnum.ADDON_MANAGER,
    ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master),
        flags='--master-logs APISERVER,CONTROLLER_MANAGER,SCHEDULER,ADDON_MANAGER'
    )

  def testDisableMasterLogs(self):
    config = self.msgs.MasterSignalsConfig(logEnabledComponents=[])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMaster=master), flags='--no-master-logs')

  @parameterized.parameters(
      ('--enable-master-metrics', True),
      ('--no-enable-master-metrics', False),
  )
  def testEnableMasterMetrics(self, flags, enabled):
    config = self.msgs.MasterSignalsConfig(
        enableMetrics=enabled,
        logEnabledComponents=[
            self.msgs.MasterSignalsConfig
            .LogEnabledComponentsValueListEntryValuesEnum.COMPONENT_UNSPECIFIED,
        ])
    master = self.msgs.Master(signalsConfig=config)
    self._TestUpdate(self.msgs.ClusterUpdate(desiredMaster=master), flags=flags)

  def testSendingKubernetesObjectsSnapshots(self):
    config = self.msgs.KubernetesObjectsExportConfig(
        kubernetesObjectsSnapshotsTarget='CLOUD_LOGGING')
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredKubernetesObjectsExportConfig=config),
        flags='--kubernetes-objects-snapshots-target CLOUD_LOGGING')

  def testSendingKubernetesObjectsChanges(self):
    config = self.msgs.KubernetesObjectsExportConfig(
        kubernetesObjectsChangesTarget='CLOUD_LOGGING')
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredKubernetesObjectsExportConfig=config),
        flags='--kubernetes-objects-changes-target CLOUD_LOGGING')

  def testSendingKubernetesObjectsSnapshotAndChanges(self):
    config = self.msgs.KubernetesObjectsExportConfig(
        kubernetesObjectsChangesTarget='CLOUD_LOGGING',
        kubernetesObjectsSnapshotsTarget='CLOUD_LOGGING')
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredKubernetesObjectsExportConfig=config),
        flags='--kubernetes-objects-changes-target CLOUD_LOGGING --kubernetes-objects-snapshots-target CLOUD_LOGGING'
    )

  def testDisableSendingKubernetesObjectsChanges(self):
    config = self.msgs.KubernetesObjectsExportConfig(
        kubernetesObjectsChangesTarget='')
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredKubernetesObjectsExportConfig=config),
        flags='--kubernetes-objects-changes-target NONE')

  def testDisableSendingKubernetesObjectsSnapshots(self):
    config = self.msgs.KubernetesObjectsExportConfig(
        kubernetesObjectsSnapshotsTarget='')
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredKubernetesObjectsExportConfig=config),
        flags='--kubernetes-objects-snapshots-target NONE')

  @parameterized.parameters('rapid', 'regular', 'stable', 'None')
  def testUpdateReleaseChannel(self, channel):
    channels = {
        'rapid': self.messages.ReleaseChannel.ChannelValueValuesEnum.RAPID,
        'regular': self.messages.ReleaseChannel.ChannelValueValuesEnum.REGULAR,
        'stable': self.messages.ReleaseChannel.ChannelValueValuesEnum.STABLE,
        'None': self.messages.ReleaseChannel.ChannelValueValuesEnum.UNSPECIFIED,
    }
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredReleaseChannel=self.messages.ReleaseChannel(
                channel=channels[channel])),
        flags='--release-channel={rc}'.format(rc=channel))

  @parameterized.parameters('invalid', 'Rapid', 'RAPID', 'Regular', 'REGULAR',
                            'Stable', 'STABLE', 'none', 'NONE')
  def testUpdateReleaseChannelInvalidChannelError(self, channel_name):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'Invalid choice'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update test-cluster --release-channel={0}'.format(channel_name))

  @parameterized.parameters(('ENABLED', 'topic'), ('DISABLED', 'topic'),
                            ('DISABLED', None))
  def testUpdateNotificationConfig(self, pubsub, topic):
    enable = pubsub == 'ENABLED'
    pubsub_msg = self.msgs.PubSub(enabled=enable, topic=topic)
    nc = self._MakeNotificationConfigFlagDict(pubsub, topic)
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredNotificationConfig=self.msgs.NotificationConfig(
                pubsub=pubsub_msg)),
        flags='--notification-config={nc} '.format(nc=nc))

  @parameterized.parameters(
      ('foo', 'topic', exceptions.InvalidArgumentException,
       r'invalid \[pubsub\] value'),
      ('ENABLED', None, exceptions.InvalidArgumentException,
       r'when \[pubsub\] is ENABLED, \[pubsub-topic\] must not be empty'),
      (None, 'topic', cli_test_base.MockArgumentError,
       r'Key \[pubsub\] required'))
  def testUpdateInvalidNotificationConfig(self, pubsub, topic, want_excp,
                                          want_err):
    nc = self._MakeNotificationConfigFlagDict(pubsub, topic)
    if pubsub is not None:
      self.ExpectGetCluster(self._RunningCluster(name=self.CLUSTER_NAME))
    with self.assertRaisesRegex(want_excp, want_err):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update {name}'
          ' --notification-config={nc}'.format(name=self.CLUSTER_NAME, nc=nc))


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestAlpha(base.AlphaTestBase, UpdateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""

  def testEnableBinaryAuthorization(self):
    self._TestEnableBinaryAuthorization(enabled=True, flags='--enable-binauthz')

  def _TestEnableBinaryAuthorization(self, enabled, flags):
    binauthz = self.msgs.BinaryAuthorization(enabled=enabled)
    update = self.msgs.ClusterUpdate(desiredBinaryAuthorization=binauthz)
    self._TestUpdate(update=update, flags=flags)

  def testUpdateSecurityProfile(self):
    profile = self.msgs.SecurityProfile(name='test-profile-1')
    update = self.msgs.ClusterUpdate(securityProfile=profile)
    self._TestUpdate(update=update, flags='--security-profile=test-profile-1')

  def _TestUpdateAutoprovisioning(self, enabled, resource_limits,
                                  autoprovisioning_defaults,
                                  autoprovisioning_locations, flags):
    autoscaling = self.msgs.ClusterAutoscaling(
        enableNodeAutoprovisioning=enabled,
        autoprovisioningNodePoolDefaults=autoprovisioning_defaults,
        resourceLimits=resource_limits,
        autoprovisioningLocations=autoprovisioning_locations)
    self._TestUpdateClusterAutoscaling(autoscaling, flags)

  def _TestUpdateClusterAutoscaling(self, autoscaling, flags):
    name = 'tobeupdated'
    update = self.msgs.ClusterUpdate(desiredClusterAutoscaling=autoscaling)
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) +
        ' update {0} {1}'.format(name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))
    self.AssertErrContains(
        ('go to: https://console.cloud.google.com/kubernetes/'
         'workload_/gcloud/{zone}/{cluster}?project={project}').format(
             cluster=name, zone=self.ZONE, project=self.PROJECT_ID))

  @parameterized.parameters(
      ('--no-disable-default-snat ', False),
      ('--disable-default-snat ', True),
  )
  def testEnableSnat(self, flags, disabled):
    update = self.msgs.ClusterUpdate(
        desiredDefaultSnatStatus=self.msgs.DefaultSnatStatus(disabled=disabled))
    self._TestUpdate(update=update, flags=flags)

  @parameterized.parameters(
      ('--no-enable-cost-management', False),
      ('--enable-cost-management', True),
  )
  def testUpdateCostManagementConfig(self, flags, enabled):
    update = self.msgs.ClusterUpdate(
        desiredCostManagementConfig=self.msgs.CostManagementConfig(
            enabled=enabled))
    self._TestUpdate(update=update, flags=flags)

  def testUpdateAddonsCloudRun(self):
    internal = self.messages.CloudRunConfig.LoadBalancerTypeValueValuesEnum.LOAD_BALANCER_TYPE_INTERNAL
    external = self.messages.CloudRunConfig.LoadBalancerTypeValueValuesEnum.LOAD_BALANCER_TYPE_EXTERNAL
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=False))),
        flags='--update-addons CloudRun=ENABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(disabled=True))),
        flags='--update-addons CloudRun=DISABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(
                    disabled=False, loadBalancerType=internal))),
        flags='--update-addons CloudRun=ENABLED '
        '--cloud-run-config load-balancer-type='
        'INTERNAL')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudRunConfig=self.msgs.CloudRunConfig(
                    disabled=False, loadBalancerType=external))),
        flags='--update-addons CloudRun=ENABLED --cloud-run-config load-balancer-type=EXTERNAL'
    )

  def testUpdateAddonsApplicationManager(self):
    # test disabling ApplicationManager
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kalmConfig=self.msgs.KalmConfig(enabled=False))),
        flags='--update-addons ApplicationManager=DISABLED')
    # test enabling ApplicationManager
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                kalmConfig=self.msgs.KalmConfig(enabled=True))),
        flags='--update-addons ApplicationManager=ENABLED')

  def testUpdateAddonsCloudBuild(self):
    # test disabling CloudBuild
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudBuildConfig=self.msgs.CloudBuildConfig(enabled=False))),
        flags='--update-addons CloudBuild=DISABLED')
    # test enabling CloudBuild
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                cloudBuildConfig=self.msgs.CloudBuildConfig(enabled=True))),
        flags='--update-addons CloudBuild=ENABLED')

  @parameterized.parameters('rapid', 'regular', 'stable', 'None')
  def testUpdateReleaseChannel(self, channel):
    channels = {
        'rapid': self.messages.ReleaseChannel.ChannelValueValuesEnum.RAPID,
        'regular': self.messages.ReleaseChannel.ChannelValueValuesEnum.REGULAR,
        'stable': self.messages.ReleaseChannel.ChannelValueValuesEnum.STABLE,
        'None': self.messages.ReleaseChannel.ChannelValueValuesEnum.UNSPECIFIED,
    }
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredReleaseChannel=self.messages.ReleaseChannel(
                channel=channels[channel])),
        flags='--release-channel={rc}'.format(rc=channel))

  @parameterized.parameters('invalid', 'Rapid', 'RAPID', 'Regular', 'REGULAR',
                            'Stable', 'STABLE', 'none', 'NONE')
  def testUpdateReleaseChannelInvalidChannelError(self, channel_name):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'Invalid choice'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) +
          ' update test-cluster --release-channel={0}'.format(channel_name))

  @parameterized.parameters('disabled', 'outbound-only', 'bidirectional')
  def testUpdatePrivateIPv6AccessType(self, access_type):
    types = {
        'disabled':
            self.messages.ClusterUpdate
            .DesiredPrivateIpv6GoogleAccessValueValuesEnum
            .PRIVATE_IPV6_GOOGLE_ACCESS_DISABLED,
        'outbound-only':
            self.messages.ClusterUpdate
            .DesiredPrivateIpv6GoogleAccessValueValuesEnum
            .PRIVATE_IPV6_GOOGLE_ACCESS_TO_GOOGLE,
        'bidirectional':
            self.messages.ClusterUpdate
            .DesiredPrivateIpv6GoogleAccessValueValuesEnum
            .PRIVATE_IPV6_GOOGLE_ACCESS_BIDIRECTIONAL
    }
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredPrivateIpv6GoogleAccess=types[access_type]),
        flags='--private-ipv6-google-access-type={0}'.format(access_type))


if __name__ == '__main__':
  test_case.main()
