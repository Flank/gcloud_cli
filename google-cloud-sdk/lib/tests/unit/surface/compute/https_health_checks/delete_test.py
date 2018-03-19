# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the https-health-checks delete subcommand."""

from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class HttpsHealthChecksDeleteTest(test_base.BaseTest,
                                  completer_test_base.CompleterBase):

  def testWithSingleHttpsHealthCheck(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute https-health-checks delete https-check-1
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-1',
              project='my-project'))],
    )

  def testWithManyHttpsHealthChecks(self):
    messages = self.messages
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute https-health-checks delete https-check-1 https-check-2
          https-check-3
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-1',
              project='my-project')),

         (self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-2',
              project='my-project')),

         (self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    messages = self.messages
    self.WriteInput('y\n')
    self.Run("""
        compute https-health-checks delete https-check-1 https-check-2
          https-check-3
        """)

    self.CheckRequests(
        [(self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-1',
              project='my-project')),

         (self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-2',
              project='my-project')),

         (self.compute.httpsHealthChecks,
          'Delete',
          messages.ComputeHttpsHealthChecksDeleteRequest(
              httpsHealthCheck='https-check-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp(
        'Deletion aborted by user.'):
      self.Run("""
          compute https-health-checks delete https-check-1 https-check-2
            https-check-3
          """)

    self.CheckRequests()

  def testDeleteCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute https-health-checks delete',
        arg='name',
        module_path='command_lib.compute.completers.HttpsHealthChecksCompleter')

  def testDeleteCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            test_resources.HTTPS_HEALTH_CHECKS_V1),
        autospec=True)
    self.RunCompletion(
        'compute https-health-checks delete h',
        [
            'https-health-check-1',
            'https-health-check-2',
        ])


if __name__ == '__main__':
  test_case.main()
