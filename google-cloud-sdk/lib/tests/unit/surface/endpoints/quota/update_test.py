# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Unit tests for endpoints quota list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.services import unit_test_base


class UpdateTestAlpha(unit_test_base.SCMUnitTestBase):
  """Unit tests for endpoints quota update command."""
  OPERATION_NAME = 'operations/123'
  OVERRIDE_ID = 'hello-override'

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testUpdate(self):
    self.ExpectUpdateQuotaOverrideCall(self.mutate_limit_name,
                                       self.mutate_metric, self.unit, 666,
                                       self.OPERATION_NAME)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('endpoints quota update --service=example.googleapis.com '
             '--consumer=projects/helloworld '
             '--metric=example.googleapis.com/mutate_requests '
             '--unit=1/min/{project} --value=666')
    self.AssertErrEquals(
        """\
Operation "operations/123" finished successfully.
""",
        normalize_space=True)

  def testUpdate_force(self):
    self.ExpectUpdateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        666,
        self.OPERATION_NAME,
        force=True)
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('endpoints quota update --service=example.googleapis.com '
             '--consumer=projects/helloworld '
             '--metric=example.googleapis.com/mutate_requests '
             '--unit=1/min/{project} '
             '--value=666 --force')
    self.AssertErrEquals(
        """\
Operation "operations/123" finished successfully.
""",
        normalize_space=True)

  def testUpdate_dimensions(self):
    self.ExpectUpdateQuotaOverrideCall(
        self.mutate_limit_name,
        self.mutate_metric,
        self.unit,
        666,
        self.OPERATION_NAME,
        dimensions=[('regions', 'us-central1'), ('zones', 'us-central1-c')])
    self.ExpectOperation(self.OPERATION_NAME, 3)

    self.Run('endpoints quota update --service=example.googleapis.com '
             '--consumer=projects/helloworld '
             '--metric=example.googleapis.com/mutate_requests '
             '--unit=1/min/{project} --value=666 '
             '--dimensions=regions=us-central1 '
             '--dimensions=zones=us-central1-c')
    self.AssertErrEquals(
        """\
Operation "operations/123" finished successfully.
""",
        normalize_space=True)
