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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.core import properties
from tests.lib.surface.compute.tpus.execution_groups import base


class SuspendTest(base.TpuUnitTestBase):

  _NAME = 'tpu-to-be-deleted'
  _TPU_OP_NAME = 'projects/fake-project/locations/central2-a/operations/fake-operation'
  _INSTANCE_OP_NAME = u'fake-operation-random-guid'

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    properties.VALUES.core.user_output_enabled.Set(True)

  def testSuspendCommand(self):
    self.ExpectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceStopCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectTPUOperationNoResource(self._TPU_OP_NAME)
    self.ExpectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups suspend {} --zone=central2-a
    """.format(self._NAME))

  def testSuspendCommandHTTPNotFoundOnInstance(self):
    self.ExpectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceStopCallWithHTTPNotFound(
        self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectTPUOperationNoResource(self._TPU_OP_NAME)
    self.Run("""
      compute tpus execution-groups suspend {} --zone=central2-a
    """.format(self._NAME))

  def testSuspendCommandHTTPNotFoundOnInstanceOp(self):
    self.ExpectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceStopCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectTPUOperationNoResource(self._TPU_OP_NAME)
    self.ExpectInstanceOperationCallWithHTTPNotFound(
        self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups suspend {} --zone=central2-a
    """.format(self._NAME))

  def testSuspendCommandHTTPNotFoundOnNode(self):
    self.ExpectTPUDeleteCallWithHTTPNotFound(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceStopCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups suspend {} --zone=central2-a
    """.format(self._NAME))

  def testSuspendCommandHTTPNotFoundOnPollNodeOp(self):
    self.ExpectTPUDeleteCall(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceStopCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectTPUOperationCallWithHTTPNotFound(self._NAME, self._TPU_OP_NAME)
    self.ExpectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups suspend {} --zone=central2-a
    """.format(self._NAME))

