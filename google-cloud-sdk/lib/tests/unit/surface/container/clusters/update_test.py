# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
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
    self.ExpectSetLoggingService(
        name,
        logging_service,
        self._MakeOperation(status=self.op_pending))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1} {2}'.
        format(name, '--logging-service', logging_service))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def testUpdateLoggingGoogle(self):
    name = 'tosetloggingservice'
    logging_service = 'logging.googleapis.com'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetLoggingService(
        name,
        logging_service,
        self._MakeOperation(status=self.op_pending))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1} {2}'.
        format(name, '--logging-service', logging_service))
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
          self.clusters_command_base.format(self.ZONE) + ' update {0} {1} {2}'.
          format(name, '--logging-service', logging_service))
    self.AssertErrContains('message=bad request')

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
                httpLoadBalancing=self.msgs.HttpLoadBalancing(
                    disabled=False),
                horizontalPodAutoscaling=self.msgs.HorizontalPodAutoscaling(
                    disabled=True))),
        flags='--update-addons '
        'HttpLoadBalancing=ENABLED,HorizontalPodAutoscaling=DISABLED')
    self._TestUpdate(
        self.msgs.ClusterUpdate(
            desiredAddonsConfig=self.msgs.AddonsConfig(
                httpLoadBalancing=self.msgs.HttpLoadBalancing(
                    disabled=False))),
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
        ],)
    self._TestUpdate(
        self.msgs.ClusterUpdate(desiredMasterAuthorizedNetworksConfig=desired),
        flags='--enable-master-authorized-networks '
        '--master-authorized-networks=10.0.0.1/32,10.0.0.2/32 ')

  def testEnableMasterAuthorizedNetworksWithMaxSourceRanges(self):
    cidr_blocks = []
    msgs_cidr_blocks = []
    for i in range(1, api_adapter.MAX_AUTHORIZED_NETWORKS_CIDRS + 1):
      cidr = '10.0.0.%d/32' % i
      cidr_blocks.append(cidr)
      msgs_cidr_blocks.append(self.msgs.CidrBlock(cidrBlock=cidr))
    desired = self.msgs.MasterAuthorizedNetworksConfig(
        enabled=True,
        cidrBlocks=msgs_cidr_blocks)

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

  def testInvalidMasterAuthorizedNetworksTooManyCIDRs(self):
    cidr_blocks = []
    for i in range(1, api_adapter.MAX_AUTHORIZED_NETWORKS_CIDRS + 2):
      cidr_blocks.append('10.0.0.%d/32' % i)
    with self.AssertRaisesArgumentErrorRegexp('too many args'):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update clustername '
          '--master-authorized-networks=' + ','.join(cidr_blocks))

  def testEnableLegacyAbac(self):
    self._TestLegacyAbac(
        enabled=True,
        flags='--enable-legacy-authorization ')

  def testNoEnableLegacyAbac(self):
    self._TestLegacyAbac(
        enabled=False,
        flags='--no-enable-legacy-authorization ')

  def _TestLegacyAbac(self, enabled, flags):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectLegacyAbac(
        cluster_name=name,
        enabled=enabled,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, flags))
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
    self.assertTrue(c_config.server == 'https://' + updated_ip)
    self.assertTrue(c_config.ca_data == updated_ca)

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
    self.assertTrue(c_config.server == 'https://' + updated_ip)
    self.assertTrue(c_config.ca_data == updated_ca)

  def testStartIpRotationAborted(self):
    """Correctly handle a user aborting the command at the prompt."""

    self._TestIpRotationAborted(flag='--start-ip-rotation')

  def testStartIpRotationPersistEnvVarError(self):
    """Correctly handle environment variable errors persisting config."""

    name = 'tobeupdated'
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.StartDictPatch('os.environ',
                        {'HOME': '', 'HOMEDRIVE': '', 'HOMEPATH': '',
                         'USERPROFILE': ''})
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
        exception=http_error.MakeHttpError(409, 'The cluster has an IP rotation'
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
    self.assertTrue(c_config.ca_data == updated_ca)

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
    self.assertTrue(c_config.ca_data == updated_ca)

  def testCompleteIpRotationAborted(self):
    """Correctly handle a user aborting the command at the prompt."""

    self._TestIpRotationAborted(flag='--complete-ip-rotation')

  def testCompleteIpRotationPersistEnvVarError(self):
    """Correctly handle environment variable errors persisting config."""

    name = 'tobeupdated'
    self.assertEqual(self.tmp_home.path, os.environ['HOME'])
    self.StartDictPatch('os.environ',
                        {'HOME': '', 'HOMEDRIVE': '', 'HOMEPATH': '',
                         'USERPROFILE': ''})
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
        exception=http_error.MakeHttpError(400, 'The cluster does not have an'
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

  def _TestIpRotationSuccess(self, name, flag, after=None,
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
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, flag))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestIpRotationAborted(self, flag):
    """This runs an ip rotation command, but then aborts at the prompt.

    Args:
      flag: Either '--start-ip-rotation' or '--complete-ip-rotation',
        depending on which operation is being tested.
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
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, flags))
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
    self.Run(self.clusters_command_base.format(self.ZONE) +
             ' update {0} {1} --async'.format(name, flags))

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
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))

  def _TestUpdateAdditionalZonesRemove(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredLocations=[self.ZONE]),
        flags='--additional-zones=""')

  def _TestUpdateAdditionalZonesAdd(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(desiredLocations=sorted(
            [self.ZONE, 'us-central1-a', 'moon-north3-z'])),
        flags='--additional-zones=us-central1-a,moon-north3-z')

  def _TestUpdateLabels(self, location):
    desired = self.msgs.SetLabelsRequest.ResourceLabelsValue(
        additionalProperties=[
            self.msgs.SetLabelsRequest.ResourceLabelsValue.
            AdditionalProperty(key='k', value='v')
        ],)
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name), zone=location)
    self.ExpectGetCluster(self._RunningCluster(name=name), zone=location)
    self.ExpectSetLabels(
        cluster_name=name,
        resource_labels=desired,
        fingerprint=None,
        response=self._MakeOperation(operationType=self.op_set_labels,
                                     zone=location),
        zone=location)
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done,
                                                zone=location))
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
            self.msgs.SetLabelsRequest.ResourceLabelsValue.
            AdditionalProperty(key='k', value='v')
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
            self.msgs.SetLabelsRequest.ResourceLabelsValue.
            AdditionalProperty(key='k', value='v')
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
            self.msgs.SetLabelsRequest.ResourceLabelsValue.
            AdditionalProperty(key='k', value='v'),
            self.msgs.SetLabelsRequest.ResourceLabelsValue.
            AdditionalProperty(key='k2', value='v2')
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
      self.AssertErrContains('Cluster \'{0}\' has no labels to remove.'
                             .format(name))

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
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--enable-network-policy'))
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

  def testSetMaintenancePolicy(self):
    """Correctly handle the success case."""
    name = 'tosetmaintenancewindow'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    self.ExpectSetMaintenanceWindow(
        cluster_name=name,
        policy=self.msgs.MaintenancePolicy(
            window=self.msgs.MaintenanceWindow(
                dailyMaintenanceWindow=self.msgs.DailyMaintenanceWindow(
                    startTime='11:43'))),
        response=self._MakeOperation(
            operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--maintenance-window=11:43'))
    self.AssertErrContains('Updating {0}'.format(name))

  def testRemoveMaintenancePolicy(self):
    m = self.msgs
    name = 'mw-cluster'
    cluster_kwargs = {
        'name': name,
        'maintenancePolicy': m.MaintenancePolicy(
            window=m.MaintenanceWindow(
                dailyMaintenanceWindow=m.DailyMaintenanceWindow(
                    startTime='11:43'))),
    }
    self.ExpectGetCluster(self._RunningCluster(**cluster_kwargs))
    self.ExpectSetMaintenanceWindow(
        cluster_name=name,
        response=self._MakeOperation(
            operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, '--maintenance-window=None'))
    self.AssertErrContains('Updating {0}'.format(name))

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
        cluster, exception=
        apitools_exceptions.HttpForbiddenError(
            {'status': 403, 'reason': 'missing update permission'},
            'forbidden', 'foo.com/bar'))
    self.ExpectUpdateCluster(
        cluster_name=name,
        update=update,
        response=self._MakeOperation(operationType=self.op_update_cluster))
    self.ExpectGetOperation(self._MakeOperation(status=self.op_done))
    self.Run(
        self.clusters_command_base.format(self.ZONE) + ' update {0} {1}'.format(
            name, flags))
    self.AssertErrContains('Updating {cluster}'.format(cluster=name))
    self.AssertErrContains(
        ('go to: https://console.cloud.google.com/kubernetes/'
         'workload_/gcloud/{zone}/{cluster}?project={project}').format(
             cluster=name, zone=self.ZONE, project=self.PROJECT_ID))


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

  def testUpdateAddons(self):
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
    self._TestEnableBinaryAuthorization(
        enabled=True,
        flags='--enable-binauthz')

  def _TestEnableBinaryAuthorization(self, enabled, flags):
    binauthz = self.msgs.BinaryAuthorization(enabled=enabled)
    update = self.msgs.ClusterUpdate(desiredBinaryAuthorization=binauthz)
    self._TestUpdate(update=update, flags=flags)

  def testUpdateMonitoringAndLogging(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='some.monitoring.service',
            desiredLoggingService='some.logging.service'),
        flags='--monitoring-service=some.monitoring.service '
        '--logging-service=some.logging.service')

  def testUpdateMonitoring(self):
    self._TestUpdate(
        update=self.msgs.ClusterUpdate(
            desiredMonitoringService='some.monitoring.service'),
        flags='--monitoring-service=some.monitoring.service ')

  def testEnableAutoprovisioning(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        resource_limits=[
            self.msgs.ResourceLimit(
                resourceType='cpu',
                maximum=100,
                minimum=8),
            self.msgs.ResourceLimit(
                resourceType='memory',
                maximum=128)],
        flags='--enable-autoprovisioning --max-memory 128 '
              '--max-cpu 100 --min-cpu 8')

  def testEnableAutoprovisioningWithAcceleratorMaxLimit(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        resource_limits=[
            self.msgs.ResourceLimit(
                resourceType='cpu',
                maximum=100,
                minimum=8),
            self.msgs.ResourceLimit(
                resourceType='memory',
                maximum=128),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-k80',
                minimum=0,
                maximum=2)],
        flags='--enable-autoprovisioning --max-memory 128 '
              '--max-cpu 100 --min-cpu 8 '
              '--max-accelerator type=nvidia-tesla-k80,count=2')

  def testEnableAutoprovisioningWithAcceleratorLimits(self):
    self._TestUpdateAutoprovisioning(
        enabled=True,
        resource_limits=[
            self.msgs.ResourceLimit(
                resourceType='cpu',
                maximum=100,
                minimum=8),
            self.msgs.ResourceLimit(
                resourceType='memory',
                maximum=128),
            self.msgs.ResourceLimit(
                resourceType='nvidia-tesla-k80',
                minimum=1,
                maximum=2)],
        flags='--enable-autoprovisioning --max-memory 128 '
              '--max-cpu 100 --min-cpu 8 '
              '--max-accelerator type=nvidia-tesla-k80,count=2 '
              '--min-accelerator type=nvidia-tesla-k80,count=1')

  def testDisableAutoprovisioning(self):
    self._TestUpdateAutoprovisioning(
        enabled=False,
        resource_limits=[],
        flags='--no-enable-autoprovisioning')

  def _TestUpdateAutoprovisioning(self, enabled, resource_limits, flags):
    autoscaling = self.msgs.ClusterAutoscaling(
        enableNodeAutoprovisioning=enabled, resourceLimits=resource_limits)
    update = self.msgs.ClusterUpdate(desiredClusterAutoscaling=autoscaling)
    self._TestUpdate(update=update, flags=flags)

  def testEnableAutoprovisioningNoLimitsInvalid(self):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update ' + name +
          ' --enable-autoprovisioning')
    self.AssertErrContains('Must specify both --max-cpu and --max-memory'
                           ' to enable autoprovisioning.')

  def testEnableAutoprovisioningAcceleratorTypeMismatch(self):
    name = 'tobeupdated'
    self.ExpectGetCluster(self._RunningCluster(name=name))
    with self.assertRaises(c_util.Error):
      self.Run(
          self.clusters_command_base.format(self.ZONE) + ' update ' + name +
          ' --enable-autoprovisioning --max-cpu 10 --max-memory 64'
          ' --max-accelerator type=nvidia-tesla-p100,count=2'
          ' --min-accelerator type=nvidia-tesla-k80,count=1')
    self.AssertErrContains('Maximum and minimum accelerator limits must be set'
                           ' on the same accelerator type.')

  def testEnableVerticalPodAutoscaling(self):
    update = self.msgs.ClusterUpdate(
        desiredVerticalPodAutoscaling=self.msgs.VerticalPodAutoscaling(
            enabled=True))
    self._TestUpdate(update=update, flags='--enable-vertical-pod-autoscaling')


# Mixin class must come in first to have the correct multi-inheritance behavior.
class UpdateTestAlpha(base.AlphaTestBase, UpdateTestBeta):
  """gcloud Alpha track using container v1alpha1 API."""

  def testEnableBinaryAuthorization(self):
    self._TestEnableBinaryAuthorization(
        enabled=True,
        flags='--enable-binauthz')

  def _TestEnableBinaryAuthorization(self, enabled, flags):
    binauthz = self.msgs.BinaryAuthorization(enabled=enabled)
    update = self.msgs.ClusterUpdate(desiredBinaryAuthorization=binauthz)
    self._TestUpdate(update=update, flags=flags)

  def testUpdateResourceUsageBigqueryDataset(self):
    dataset_id = 'dataset_id'
    bigquery_destination = self.msgs.BigQueryDestination(
        datasetId=dataset_id)
    export_config = self.msgs.ResourceUsageExportConfig(
        bigqueryDestination=bigquery_destination)
    update = self.msgs.ClusterUpdate(
        desiredResourceUsageExportConfig=export_config)
    flags = '--resource-usage-bigquery-dataset={dataset_id}'.format(
        dataset_id=dataset_id)
    self._TestUpdate(update=update, flags=flags)

  def testClearResourceUsageBigqueryDataset(self):
    export_config = self.msgs.ResourceUsageExportConfig()
    update = self.msgs.ClusterUpdate(
        desiredResourceUsageExportConfig=export_config)
    self._TestUpdate(update=update,
                     flags='--clear-resource-usage-bigquery-dataset')

if __name__ == '__main__':
  test_case.main()
