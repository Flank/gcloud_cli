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
"""Unit tests for the `run routes describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import route
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import flags
from tests.lib.surface.run import base


class DescribeTestBeta(base.ServerlessSurfaceBase):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.mock_route = route.Route.New(
        self.mock_serverless_client, 'us-central1.fake-project')
    self.mock_route.name = 'simone'
    self.mock_route.metadata.creationTimestamp = '2018/01/02 00:00:00'

  def testDescribe_Succeed_Default(self):
    """Tests successful describe with default output format."""
    self.operations.GetRoute.return_value = self.mock_route
    self.Run('run routes describe simone')
    for s in ['spec', 'kind: Route', 'name: simone',
              'creationTimestamp: 2018/01/02 00:00:00']:
      self.AssertOutputMatches(s)

  def testDescribe_Fail_Missing(self):
    """Tests describe fails when route is not found."""
    self.operations.GetRoute.return_value = None
    with self.assertRaises(flags.ArgumentError) as context:
      self.Run('run routes describe kale')
    self.assertIn('Cannot find route [kale]', str(context.exception))


class DescribeTestAlpha(DescribeTestBeta):
  """Tests outputs of describe command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
