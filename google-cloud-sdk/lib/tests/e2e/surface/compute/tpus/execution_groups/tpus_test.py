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
"""e2e tests for compute tpus execution-groups command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case


class TpusTests(e2e_base.WithServiceAuth):
  """E2E tests for compute tpus command group."""

  def SetUp(self):
    self.zone = 'us-central1-c'
    self.exec_group_name = 'do-not-delete-tpu-execution-group'
    self.track = calliope_base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def DescribeExecGroup(self):
    command = (
        'compute tpus execution-groups describe '
        '{name} --zone {zone}'
        .format(zone=self.zone, name=self.exec_group_name))

    self.Run(command)
    self.AssertOutputContains(
        'TPU Accelerator Type: v2-8', normalize_space=True)
    self.AssertOutputContains(
        'TPU State: READY', normalize_space=True)
    self.AssertOutputContains(
        'TPU TF Version: testConfig-NoTpu-FakeTF', normalize_space=True)
    self.AssertOutputContains(
        'Compute Engine Created: 2020-07-28T14:21:53.163-07:00',
        normalize_space=True)

  @contextlib.contextmanager
  def ListExecGroup(self):
    command = (
        'compute tpus execution-groups list '
        '--zone {zone}'
        .format(zone=self.zone))

    self.Run(command)
    self.AssertOutputContains(
        '{name} Running'.format(name=self.exec_group_name),
        normalize_space=True)

  def testListAndDescribe(self):
    self.ListExecGroup()
    self.DescribeExecGroup()

if __name__ == '__main__':
  test_case.main()
