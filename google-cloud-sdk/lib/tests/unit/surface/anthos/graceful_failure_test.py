# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Base classes for anthos tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util.anthos import binary_operations as bin_ops
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case


class GracefulFailureTest(sdk_test_base.WithFakeAuth,
                          cli_test_base.CliTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.StartObjectPatch(
        files, 'FindExecutableOnPath', return_value=None)

  def testAuthPlugin(self):
    with self.assertRaisesRegex(bin_ops.MissingExecutableException,
                                r'Could not locate anthos auth executable '
                                r'\[kubectl-anthos\] on the system PATH.'):
      self.Run('anthos auth login  --cluster my-test-cluster '
               '--login-config my-login-config.yaml')


class GracefulFailureTestBeta(GracefulFailureTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class GracefulFailureTestAlpha(GracefulFailureTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testAnthosCliPlugin(self):
    with self.assertRaisesRegex(bin_ops.MissingExecutableException,
                                r'Could not locate anthos executable '
                                r'\[anthoscli\] on the system PATH.'):
      self.Run('anthos packages describe . ')


if __name__ == '__main__':
  test_case.main()
