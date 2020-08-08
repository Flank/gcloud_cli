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
"""Unit tests for the `run services describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import flags
from tests.lib.surface.run import base


class DescribeTestBeta(base.ServerlessSurfaceBase):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.mock_service = service.Service.New(
        self.mock_serverless_client, 'doot')
    self.mock_service.name = 'simon'
    self.mock_service.metadata.creationTimestamp = '2018/01/02 00:00:00'
    self.mock_service.annotations[
        'serving.knative.dev/creator'] = 'me@example.com'
    self.mock_service.template.image = 'gcr.io/foo/bar:latest'
    self.mock_service.template_annotations[
        'serving.knative.dev/creator'] = 'me@example.com'
    self.mock_service.template.env_vars.literals['n1'] = 'v1'
    self.mock_service.template.env_vars.literals['n2'] = 'v2'

  def testDescribe_Succeed_Yaml(self):
    """Tests successful describe with yaml output format."""
    self.operations.GetService.return_value = self.mock_service
    self.Run('run services describe simon --format yaml')
    for s in [
        'spec', 'kind: Service', 'name: simon', 'name: n1', 'value: v1',
        'namespace: doot', 'serving.knative.dev/creator: me@example.com']:
      self.AssertOutputMatches(s)

  def testDescribe_Succeed_Export(self):
    """Tests successful describe with export output format."""
    self.operations.GetService.return_value = self.mock_service
    self.Run('run services describe simon --format export')
    for s in [
        'spec', 'kind: Service', 'name: simon', 'name: n1', 'value: v1']:
      self.AssertOutputMatches(s)
    for s in ['2018']:
      self.AssertOutputNotMatches(s)

  def testDescribe_Succeed_Default(self):
    """Tests successful describe with default output format."""
    self.operations.GetService.return_value = self.mock_service
    self.Run('run services describe simon')
    for s in [
        'Service simon in namespace doot',
        'n1\\s*v1',
        'Image:\\s*gcr.io/foo/bar:latest',
    ]:
      self.AssertOutputMatches(s)

  def testDescribe_Fail_Missing(self):
    """Tests describe fails when service is not found."""
    self.operations.GetService.return_value = None
    with self.assertRaises(flags.ArgumentError) as context:
      self.Run('run services describe salad')
    self.assertIn('Cannot find service [salad]', str(context.exception))


class DescribeTestAlpha(DescribeTestBeta):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
