# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the health-checks delete subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.health_checks import test_resources


class HealthChecksDeleteTest(test_base.BaseTest,
                             completer_test_base.CompleterBase):

  def RunDelete(self, command):
    self.Run('compute health-checks delete %s' % command)

  def testWithSingleHealthCheck(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('my-health-check-1')

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='my-health-check-1',
              project='my-project'))],
    )

  def testWithManyHealthChecks(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-1',
              project='my-project')),

         (self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-2',
              project='my-project')),

         (self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-3',
              project='my-project'))],
    )

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests(
        [(self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-1',
              project='my-project')),

         (self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-2',
              project='my-project')),

         (self.compute.healthChecks,
          'Delete',
          self.messages.ComputeHealthChecksDeleteRequest(
              healthCheck='check-3',
              project='my-project'))],
    )

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests()

  def testDeleteCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute health-checks delete',
        arg='name',
        module_path='command_lib.compute.completers.HealthChecksCompleter')

  def testDeleteCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        return_value=resource_projector.MakeSerializable(
            test_resources.HEALTH_CHECKS),
        autospec=True)
    self.RunCompletion('compute health-checks delete h', [
        'health-check-http-2',
        'health-check-http-1',
        'health-check-tcp',
        'health-check-ssl',
        'health-check-https',
        'health-check-http2',
        'health-check-grpc',
    ])


class HealthChecksDeleteBetaTest(HealthChecksDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)


class HealthChecksDeleteAlphaTest(HealthChecksDeleteBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


class RegionHealthChecksDeleteTest(HealthChecksDeleteTest):

  def RunDelete(self, command):
    self.Run('compute health-checks delete --region us-west-1 %s' % command)

  def testWithSingleHealthCheck(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('my-health-check-1')

    self.CheckRequests([(self.compute.regionHealthChecks, 'Delete',
                         self.messages.ComputeRegionHealthChecksDeleteRequest(
                             healthCheck='my-health-check-1',
                             project='my-project',
                             region='us-west-1'))],)

  def testWithManyHealthChecks(self):
    properties.VALUES.core.disable_prompts.Set(True)
    self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests([
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-1', project='my-project', region='us-west-1')),
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-2', project='my-project', region='us-west-1')),
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-3', project='my-project', region='us-west-1'))
    ],)

  def testPromptingWithYes(self):
    self.WriteInput('y\n')
    self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests([
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-1', project='my-project', region='us-west-1')),
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-2', project='my-project', region='us-west-1')),
        (self.compute.regionHealthChecks, 'Delete',
         self.messages.ComputeRegionHealthChecksDeleteRequest(
             healthCheck='check-3', project='my-project', region='us-west-1'))
    ],)

  def testPromptingWithNo(self):
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Deletion aborted by user.'):
      self.RunDelete('check-1 check-2 check-3')

    self.CheckRequests()

  def testDeleteCompleter(self):
    self.AssertCommandArgCompleter(
        command='compute health-checks delete',
        arg='name',
        module_path='command_lib.compute.completers.HealthChecksCompleter')

  def testDeleteCompletion(self):
    self.StartPatch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson',
        return_value=resource_projector.MakeSerializable(
            test_resources.HEALTH_CHECKS),
        autospec=True)
    self.RunCompletion('compute health-checks delete h', [
        'health-check-http-2',
        'health-check-http-1',
        'health-check-tcp',
        'health-check-ssl',
        'health-check-https',
        'health-check-http2',
        'health-check-grpc',
    ])


class RegionHealthChecksDeleteBetaTest(RegionHealthChecksDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)


class RegionHealthChecksDeleteAlphaTest(RegionHealthChecksDeleteBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)


if __name__ == '__main__':
  test_case.main()
