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
"""Unit tests for the Serverless deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import source_ref
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib.surface.run import base

import mock


class ServerlessDeployTest(base.ServerlessSurfaceBase, parameterized.TestCase):

  def SetUp(self):
    self.StartObjectPatch(os.path, 'isdir', return_value=True)
    self.source_dir = source_ref.SourceRef.MakeDirRef('/my/dir')
    self.other_dir = source_ref.SourceRef.MakeDirRef('/other/place')
    self.operations.GetServiceUrl.return_value = 'https://foo-bar.baz'
    self.app = mock.NonCallableMock()
    self.operations.Detect.return_value = self.app
    self.conf = mock.NonCallableMock()
    self.conf.status.latestReadyRevisionName = 'rev.1'
    self.operations.GetConfiguration.return_value = self.conf
    self.env_changes = mock.NonCallableMock()
    self.env_mock = self.StartObjectPatch(config_changes, 'EnvVarChanges',
                                          return_value=self.env_changes)

  def _AssertSuccessMessage(self, serv):
    self.AssertErrContains(
        'Service [{serv}] revision [{rev}] has been deployed '
        'and is serving traffic at {url}'.format(
            serv=serv,
            rev='rev.1',
            url='https://foo-bar.baz'))

  def testDeployWithSource(self):
    self.WriteInput('thing\n')
    self.Run('run deploy --source=/other/place')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.other_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('thing'), [self.app], asyn=False)
    self._AssertSuccessMessage('thing')

  def testDeployWithService(self):
    self.Run('run deploy my-service --source=/my/dir')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('my-service'), [self.app], asyn=False)
    self._AssertSuccessMessage('my-service')

  def testDeployMissingServiceCantPrompt(self):
    with self.assertRaises(handlers.ParseError):
      self.Run('run deploy --source=/my/dir -q')
    self.operations.Upload.assert_not_called()
    self.operations.ReleaseService.assert_not_called()

  def testDeployMissingNamespaceCantPrompt(self):
    properties.VALUES.run.region.Set(None)
    with self.assertRaises(flags.ArgumentError):
      self.Run('run deploy my-service --source=/my/dir -q')
    self.operations.Upload.assert_not_called()
    self.operations.ReleaseService.assert_not_called()

  def testDeployInvalidService(self):
    with self.assertRaises(flags.ArgumentError):
      self.Run('run deploy BooM --source=/my/dir')
    self.operations.Upload.assert_not_called()
    self.operations.ReleaseService.assert_not_called()

  def testDeployWithRegion(self):
    self.WriteInput('\n')
    self.Run('run deploy --region se-arboga --source=/my/dir')
    self.operations.Detect.assert_called_once_with(
        self._NamespaceRef(region='se-arboga'), self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir', 'se-arboga'), [self.app], asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithFunction(self):
    self.WriteInput('\n')
    self.Run('run deploy --function tsp_in_constant_time '
             '--source=/my/dir')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, 'tsp_in_constant_time')
    self.operations.Upload.assert_called_once_with(self.app)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app], asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithImage(self):
    self.WriteInput('\n')
    img_ref = source_ref.SourceRef.MakeImageRef('gcr.io/image')
    self.Run('run deploy --image gcr.io/image')
    self.operations.Detect.assert_called_once_with(
        self.namespace, img_ref, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('image'), [self.app], asyn=False)
    self.AssertErrContains('Deploying container')
    self._AssertSuccessMessage('image')

  def testDeployWithEnvVars(self):
    self.WriteInput('\n')
    self.Run('run deploy --source=/my/dir '
             '--update-env-vars="k1 with spaces"=v1')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.env_mock.assert_called_once_with(
        env_vars_to_update={'k1 with spaces': 'v1'})
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app, self.env_changes],
        asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithSetEnvVars(self):
    self.Run('run deploy --source=/my/dir '
             '--set-env-vars="k1 with spaces"=v1,k2="v 2"')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.env_mock.assert_called_once_with(
        env_vars_to_update={'k1 with spaces': 'v1', 'k2': 'v 2'},
        clear_others=True)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app, self.env_changes],
        asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithRemoveEnvVars(self):
    self.Run('run deploy --source=/my/dir --remove-env-vars="k 1",k2')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.env_mock.assert_called_once_with(env_vars_to_remove=['k 1', 'k2'])
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app, self.env_changes],
        asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithClearEnvVars(self):
    self.Run('run deploy --source=/my/dir --clear-env-vars')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.env_mock.assert_called_once_with(clear_others=True)
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app, self.env_changes],
        asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployWithUpdateRemoveEnvVars(self):
    self.Run('run deploy --source=/my/dir --remove-env-vars="k 1",k2 '
             '--update-env-vars=k2="v 2","k 3"=v3')
    self.operations.Detect.assert_called_once_with(
        self.namespace, self.source_dir, None)
    self.operations.Upload.assert_called_once_with(self.app)
    self.env_mock.assert_called_with(
        env_vars_to_update={'k2': 'v 2', 'k 3': 'v3'},
        env_vars_to_remove=['k 1', 'k2'])
    self.operations.ReleaseService.assert_called_once_with(
        self._ServiceRef('dir'), [self.app, self.env_changes],
        asyn=False)
    self._AssertSuccessMessage('dir')

  def testDeployToCluster(self):
    self.Run('run deploy --image gcr.io/image --namespace mynamespace '
             '--cluster=mycluster --cluster-location=mylocation')
    self.AssertErrContains('Deploying container')
    self.AssertErrContains('in namespace [mynamespace] of cluster [mycluster]')
    self._AssertSuccessMessage('image')

  @parameterized.parameters(base.INVALID_ENV_FLAG_PAIRS)
  def testDeployWithPairEnvVars(self, flag1, flag2):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('run deploy {} {}'.format(flag1, flag2))

  def testDeployWithNumericConcurrency(self):

    self.Run('run deploy my-service --source /other/place '
             '--region se-arboga --concurrency 7')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertTrue(any(
        isinstance(x, config_changes.ConcurrencyChanges)
        and x._concurrency == 7 for x in mutators))

  def testDeployWithEverything(self):

    self.Run('run deploy my-service --source /other/place '
             '--region se-arboga --function tsp_in_constant_time '
             '--update-env-vars=k1=v1 --concurrency OneTrillion')
    positional, _ = self.operations.ReleaseService.call_args
    mutators = positional[1]
    self.assertIn(self.app, mutators)
    self.assertIn(self.env_changes, mutators)
    self.assertTrue(any(
        isinstance(x, config_changes.ConcurrencyChanges)
        and x._concurrency == 'OneTrillion' for x in mutators))
