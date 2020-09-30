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
"""Unit tests for the Serverless deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib.surface.run import base

import mock


class ServerlessDeployTest(base.ServerlessSurfaceBase, parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.StartObjectPatch(os.path, 'isdir', return_value=True)
    self.service = service.Service.New(self.mock_serverless_client,
                                       self.Project())
    self.service.domain = 'https://foo-bar.baz'
    self.service.status.latestReadyRevisionName = 'rev.1'
    self.service.status_traffic.SetPercent('rev.1', 100)
    self.service.spec_traffic.SetPercent('rev.1', 100)
    self.operations.GetService.return_value = self.service
    self.operations.ReleaseService.return_value = self.service
    self.app = mock.NonCallableMock()
    self.StartObjectPatch(config_changes, 'ImageChange', return_value=self.app)
    self.env_changes = mock.NonCallableMock()
    self.env_mock = self.StartObjectPatch(
        config_changes, 'EnvVarLiteralChanges', return_value=self.env_changes)
    self.launch_stage_changes = mock.NonCallableMock()
    self.StartObjectPatch(
        config_changes,
        'SetLaunchStageAnnotationChange',
        return_value=self.launch_stage_changes)

  def _SetServiceName(self, name):
    self.service.name = name

  def _AssertSuccessMessage(self, serv):
    self.AssertErrContains('to Cloud Run')
    self.AssertErrContains(
        'Service [{serv}] revision [{rev}] has been deployed '
        'and is serving 100 percent of traffic.\nService URL: {url}'.format(
            serv=serv, rev='rev.1', url='https://foo-bar.baz'))

  def testDeployWithService(self):
    self._SetServiceName('my-service')
    self.Run('run deploy my-service --image=gcr.io/thing/stuff')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    args, _ = self.operations.ReleaseService.call_args
    tracker = args[2]
    self.assertNotIn('RoutesReady', tracker)
    self._AssertSuccessMessage('my-service')

  def testDeployWithFormat(self):
    self._SetServiceName('my-service')
    serv = self.Run(
        'run deploy my-service --image=gcr.io/thing/stuff --format=yaml')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    args, _ = self.operations.ReleaseService.call_args
    tracker = args[2]
    self.assertNotIn('RoutesReady', tracker)
    self._AssertSuccessMessage('my-service')
    self.assertIsNotNone(serv)
    self.AssertOutputContains('apiVersion: serving.knative.dev/v1')
    self.AssertOutputContains('kind: Service')
    self.AssertOutputContains('url: https://foo-bar.baz')

  def testDeployWithZeroPercentTrafficTarget(self):
    self._SetServiceName('my-service')
    self.service.status_traffic['rev.1'] = [
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=100),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', tag='latest')
    ]
    self.service.spec_traffic['rev.1'] = [
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', percent=100),
        self.serverless_messages.TrafficTarget(
            revisionName='rev.1', tag='latest')
    ]
    self.Run('run deploy my-service --image=gcr.io/thing/stuff')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    args, _ = self.operations.ReleaseService.call_args
    tracker = args[2]
    self.assertNotIn('RoutesReady', tracker)
    self._AssertSuccessMessage('my-service')

  def testDeployWithServiceLatest(self):
    self._SetServiceName('my-service')
    del self.service.status_traffic['rev.1']
    self.service.status_traffic.SetPercent(traffic.LATEST_REVISION_KEY, 100)
    del self.service.spec_traffic['rev.1']
    self.service.spec_traffic.SetPercent(traffic.LATEST_REVISION_KEY, 100)
    self.Run('run deploy my-service --image=gcr.io/thing/stuff')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    args, _ = self.operations.ReleaseService.call_args
    tracker = args[2]
    self.assertIn('RoutesReady', tracker)
    self._AssertSuccessMessage('my-service')

  def testDeployMissingServiceCantPrompt(self):
    with self.assertRaises(handlers.ParseError):
      self.Run('run deploy --image=gcr.io/thing/stuff -q')
    self.operations.ReleaseService.assert_not_called()

  def testDeployMissingNamespaceCantPrompt(self):
    properties.VALUES.run.region.Set(None)
    with self.assertRaises(flags.ArgumentError):
      self.Run('run deploy my-service --image=gcr.io/thing/stuff -q')
    self.operations.ReleaseService.assert_not_called()

  def testDeployInvalidService(self):
    with self.assertRaises(flags.ArgumentError):
      self.Run('run deploy BooM --image=gcr.io/thing/stuff')
    self.operations.ReleaseService.assert_not_called()

  def testDeployWithRegion(self):
    self._SetServiceName('stuff')
    self.WriteInput('\n')
    self.Run('run deploy --region se-arboga --image=gcr.io/thing/stuff')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff', 'se-arboga'),
        [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployWithImage(self):
    self._SetServiceName('image')
    self.WriteInput('\n')
    self.Run('run deploy --image gcr.io/image')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self.AssertErrContains('Deploying container')
    self._AssertSuccessMessage('image')

  def testDeployAsync(self):
    self._SetServiceName('image')
    self.WriteInput('\n')
    self.Run('run deploy --image gcr.io/image --async')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=True,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self.AssertErrContains('Deploying container')
    self.AssertErrContains('Service [image] is deploying asynchronously')

  def testDeployWithEnvVars(self):
    self._SetServiceName('stuff')
    self.WriteInput('\n')
    self.Run('run deploy --image=gcr.io/thing/stuff '
             '--update-env-vars="k1 with spaces"=v1')
    self.env_mock.assert_called_once_with(
        env_vars_to_update={'k1 with spaces': 'v1'})
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff'),
        [self.app, self.env_changes, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployWithSetEnvVars(self):
    self._SetServiceName('stuff')
    self.Run('run deploy --image=gcr.io/thing/stuff '
             '--set-env-vars="k1 with spaces"=v1,k2="v 2"')
    self.env_mock.assert_called_once_with(
        env_vars_to_update={
            'k1 with spaces': 'v1',
            'k2': 'v 2'
        },
        clear_others=True)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff'),
        [self.app, self.env_changes, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployWithRemoveEnvVars(self):
    self._SetServiceName('stuff')
    self.Run('run deploy --image=gcr.io/thing/stuff --remove-env-vars="k 1",k2')
    self.env_mock.assert_called_once_with(env_vars_to_remove=['k 1', 'k2'])
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff'),
        [self.app, self.env_changes, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployWithClearEnvVars(self):
    self._SetServiceName('stuff')
    self.Run('run deploy --image=gcr.io/thing/stuff --clear-env-vars')
    self.env_mock.assert_called_once_with(clear_others=True)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff'),
        [self.app, self.env_changes, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployWithUpdateRemoveEnvVars(self):
    self._SetServiceName('stuff')
    self.Run('run deploy --image=gcr.io/thing/stuff --remove-env-vars="k 1",k2 '
             '--update-env-vars=k2="v 2","k 3"=v3')
    self.env_mock.assert_called_with(
        env_vars_to_update={
            'k2': 'v 2',
            'k 3': 'v3'
        },
        env_vars_to_remove=['k 1', 'k2'])
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('stuff'),
        [self.app, self.env_changes, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)
    self._AssertSuccessMessage('stuff')

  def testDeployToCluster(self):
    self._SetServiceName('image')
    self.Run('run deploy --image gcr.io/image --namespace mynamespace '
             '--cluster=mycluster --cluster-location=mylocation --platform gke')
    self.AssertErrContains('Deploying container')
    self.AssertErrContains('in namespace [mynamespace] of cluster [mycluster]')
    self._AssertSuccessMessage('image')

  def testDeployToClusterFailsWithWrongPlatform(self):
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run('run deploy --image gcr.io/image --namespace mynamespace '
               '--cluster=mycluster --cluster-location=mylocation')

  @parameterized.parameters(base.INVALID_ENV_FLAG_PAIRS)
  def testDeployWithPairEnvVars(self, flag1, flag2):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('run deploy {} {}'.format(flag1, flag2))

  def testDeployWithNumericConcurrency(self):

    self.Run('run deploy my-service --image=gcr.io/thing/stuff '
             '--region se-arboga --concurrency 7')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertTrue(
        any(
            isinstance(x, config_changes.ConcurrencyChanges) and
            x._concurrency == 7 for x in mutators))

  def testDeployWithIAMServiceAccount(self):
    self.Run('run deploy my-service --image=gcr.io/thing/stuff '
             '--region se-arboga --service-account thing@stuff.org')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertTrue(
        any(
            isinstance(x, config_changes.ServiceAccountChanges) and
            x._service_account == 'thing@stuff.org' for x in mutators))

  def testDeployWithEverything(self):
    self.Run('run deploy my-service --image=gcr.io/thing/stuff '
             '--region se-arboga --function tsp_in_constant_time '
             '--update-env-vars=k1=v1 --concurrency 2000')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertIn(self.app, mutators)
    self.assertIn(self.env_changes, mutators)
    self.assertIn(self.launch_stage_changes, mutators)

  @parameterized.named_parameters(('private', '--connectivity=internal'),
                                  ('public', '--connectivity=external'))
  def testDeployConnectivityVisibility(self, visibility_flag):
    """Test the connectivity visibility flags succeed when deploying to a cluster."""
    self._SetServiceName('image')
    self.Run('run deploy --image gcr.io/image --namespace mynamespace '
             '--cluster=mycluster --cluster-location=mylocation '
             '--platform=gke {}'.format(visibility_flag))
    self.AssertErrContains('Deploying container')
    self.AssertErrContains('in namespace [mynamespace] of cluster [mycluster]')
    self._AssertSuccessMessage('image')

  @parameterized.named_parameters(('private', '--connectivity=internal'),
                                  ('public', '--connectivity=external'))
  def testDeployConnectivityVisibilityNoCluster(self, visibility_flag):
    """Test that the connectivity visibility flags raises if not using a cluster."""
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run('run deploy --image gcr.io/image {}'.format(visibility_flag))

  def testDeployConnectivityOtherValue(self):
    """Test that --connectivity must take the value internal or external."""
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('run deploy --image gcr.io/image ' '--connectivity semivisible')

  def testDeployWithAllowUnauthenticated(self):
    """Test the --allow-unauthenticated flag."""
    self.Run('run deploy --image gcr.io/image --allow-unauthenticated')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=True,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)

  def testDeployWithNoAllowUnauthenticated(self):
    """Test the --no-allow-unauthenticated flag."""
    self.Run('run deploy --image gcr.io/image --no-allow-unauthenticated')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=False,
        prefetch=self.service,
        build_log_url=None,
        build_op_ref=None)

  def testAllowUnauthenticatedFailsWithCluster(self):
    """Test that --allow-unauthenticated fails when operating on GKE."""
    with self.assertRaises(serverless_exceptions.ConfigurationError):
      self.Run('run deploy --image gcr.io/image --namespace mynamespace '
               '--cluster=mycluster --cluster-location=mylocation '
               '--platform=gke --allow-unauthenticated')

  def testPromptAllowUnauthYes(self):
    """Test that user is prompted to allow unauth access and says yes."""
    self._SetServiceName('image')
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.operations.CanSetIamPolicyBinding.return_value = True
    self.operations.GetService.side_effect = [None, self.service]
    self.WriteInput('\ny\n')
    self.Run('run deploy --image gcr.io/image')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=True,
        prefetch=None,
        build_log_url=None,
        build_op_ref=None)
    self.AssertErrContains('Allow unauthenticated invocations to [image]')

  def testPromptAllowUnauthNo(self):
    """Test that user is prompted to allow unauth access and says no."""
    self._SetServiceName('image')
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    self.operations.CanSetIamPolicyBinding.return_value = True
    self.operations.GetService.side_effect = [None, self.service]
    self.WriteInput('\nn\n')
    self.Run('run deploy --image gcr.io/image')
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app, self.launch_stage_changes],
        mock.ANY,
        asyn=False,
        allow_unauthenticated=None,
        prefetch=None,
        build_log_url=None,
        build_op_ref=None)
    self.AssertErrContains('Allow unauthenticated invocations to [image]')


class ServerlessDeployTestBeta(ServerlessDeployTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ServerlessDeployTestAlpha(ServerlessDeployTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testDeployWithKubernetesServiceAccount(self):
    self.Run('run deploy my-service --image=gcr.io/thing/stuff '
             '--platform=gke --cluster=mycluster --cluster-location=mylocation '
             '--service-account thing')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertTrue(
        any(
            isinstance(x, config_changes.ServiceAccountChanges) and
            x._service_account == 'thing' for x in mutators))
