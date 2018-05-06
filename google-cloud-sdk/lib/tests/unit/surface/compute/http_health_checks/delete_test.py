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
"""Tests for the http-health-checks delete subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class HttpHealthChecksDeleteTest(test_base.BaseTest,
                                 completer_test_base.CompleterBase):

  def testWithSingleHttpHealthCheck(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute http-health-checks delete http-check-1
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-1',
              project='my-project'))],
    )

  def testWithManyHttpHealthChecks(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.Run("""
        compute http-health-checks delete http-check-1 http-check-2
          http-check-3
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-1',
              project='my-project')),

         (self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-2',
              project='my-project')),

         (self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.Run("""
        compute http-health-checks delete http-check-1 http-check-2
          http-check-3
        """)

    self.CheckRequests(
        [(self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-1',
              project='my-project')),

         (self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-2',
              project='my-project')),

         (self.compute_v1.httpHealthChecks,
          'Delete',
          messages.ComputeHttpHealthChecksDeleteRequest(
              httpHealthCheck='http-check-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.Run("""
          compute http-health-checks delete http-check-1 http-check-2
            http-check-3
          """)

    self.CheckRequests()

  def testDeleteCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute http-health-checks delete',
        arg='name',
        module_path='command_lib.compute.completers.HttpHealthChecksCompleter')

  def testDeleteCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        return_value=resource_projector.MakeSerializable(
            test_resources.HEALTH_CHECKS),
        autospec=True)
    self.RunCompletion(
        'compute http-health-checks delete h',
        [
            'health-check-http-1',
            'health-check-http-2',
            'health-check-https',
            'health-check-ssl',
            'health-check-tcp',
        ])


if __name__ == '__main__':
  test_case.main()
