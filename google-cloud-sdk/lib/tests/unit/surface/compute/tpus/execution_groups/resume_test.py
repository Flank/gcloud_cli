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


class ResumeTest(base.TpuUnitTestBase):

  _NAME = 'fake-exec-group'
  _TPU_OP_NAME = 'projects/fake-project/locations/central2-a/operations/fake-operation'
  _INSTANCE_OP_NAME = u'fake-operation-random-guid'

  def PreSetUp(self):
    self._SetTrack(calliope_base.ReleaseTrack.ALPHA)
    self._SetApiVersion('v1alpha1')
    self.compute_api_version = 'alpha'

  def SetUp(self):
    self.StartObjectPatch(p_util, 'GetProjectNumber', return_value=12321)
    properties.VALUES.core.user_output_enabled.Set(True)

  def testResumeCommand(self):
    self.ExpectTPUCreateCall(self._NAME, 'fake-accel', 'fake-tf-version', False)
    self.ExpectInstanceStartCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectOperation(self.mock_tpu_client.projects_locations_operations,
                         self._TPU_OP_NAME,
                         self.mock_tpu_client.projects_locations_nodes,
                         self._TPU_OP_NAME)
    self.ExpectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectInstanceGetCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups resume {} --zone=central2-a \
      --tf-version='fake-tf-version' --accelerator-type='fake-accel'
    """.format(self._NAME))

  def testResumeCommandVMOnly(self):
    self.ExpectInstanceStartCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectInstanceOperationCall(self._NAME, self._INSTANCE_OP_NAME)
    self.ExpectInstanceGetCall(self._NAME, self._INSTANCE_OP_NAME)
    self.Run("""
      compute tpus execution-groups resume {} --zone=central2-a \
      --vm-only
      """.format(self._NAME))

  def testResumeCommandWithTPUCreateConflictError(self):
    self.ExpectTPUCreateCallWithConflictError(
        self._NAME, 'fake-accel', 'fake-tf-version', False)
    self.Run("""
      compute tpus execution-groups resume {} --zone=central2-a \
      --tf-version='fake-tf-version' --accelerator-type='fake-accel'
    """.format(self._NAME))

  def testResumeCommandWithInstanceNotFoundError(self):
    self.ExpectTPUCreateCall(self._NAME, 'fake-accel', 'fake-tf-version', False)
    self.ExpectInstanceStartCallWithHTTPNotFoundError(self._NAME)
    self.Run("""
      compute tpus execution-groups resume {} --zone=central2-a \
      --tf-version='fake-tf-version' --accelerator-type='fake-accel'
    """.format(self._NAME))
