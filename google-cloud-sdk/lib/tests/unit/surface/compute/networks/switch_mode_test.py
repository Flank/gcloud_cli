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
"""Tests for the networks switch-mode subcommand."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NetworksSwitchModeTest(test_base.BaseTest,
                             completer_test_base.CompleterBase):
  api_version = 'alpha'
  messages = apis.GetMessagesModule('compute', 'alpha')

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testSwitchToCustomMode(self):
    self._RunSwitchModeCommand(mode='custom', interactive=False)
    self._VerifyRequest(expect_switch_request=True)
    self._VerifyDeprecationWarning()

  def testSwitchToAutoMode(self):
    with self.AssertRaisesToolExceptionMatches(
        'Only switching to custom mode is supported now.'):
      self._RunSwitchModeCommand(mode='auto', interactive=False)
    self._VerifyRequest(expect_switch_request=False)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self._RunSwitchModeCommand(mode='custom', interactive=True)
    self._VerifyRequest(expect_switch_request=True)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionMatches('Operation aborted by user.'):
      self._RunSwitchModeCommand(mode='custom', interactive=True)
    self._VerifyRequest(expect_switch_request=False)

  def testSwitchModeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.NETWORKS_V1)
    self.RunCompletion('alpha compute networks switch-mode n',
                       ['network-1', 'network-2', 'network-3'])

  def _RunSwitchModeCommand(self, mode='custom', interactive=True):
    command = '%s compute networks switch-mode network-1 --mode=%s %s' % (
        self.api_version if self.api_version else '',
        mode,
        '' if interactive else '--quiet')
    self.Run(command.strip())

  def _VerifyRequest(self, expect_switch_request):
    if expect_switch_request:
      self.CheckRequests(
          [(self.compute.networks,
            'SwitchToCustomMode',
            self.messages.ComputeNetworksSwitchToCustomModeRequest(
                network='network-1',
                project='my-project'))])
    else:
      self.CheckRequests()

  def _VerifyDeprecationWarning(self):
    self.AssertErrContains(
        'WARNING: `switch-mode` is deprecated. '
        'Please use `--switch-to-custom-subnet-mode` with `gcloud compute '
        'networks update` instead.')

if __name__ == '__main__':
  test_case.main()
