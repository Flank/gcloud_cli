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
"""Unit tests for endpoints quota list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.services import unit_test_base


class ListTestAlpha(unit_test_base.SUUnitTestBase):
  """Unit tests for services quota list command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testList(self):
    want = [self.mutate_quota_metric, self.default_quota_metric]
    self.ExpectListQuotaMetricsCall(want)

    self.Run(
        'services quota list --service=example.googleapis.com --consumer=projects/helloworld'
    )
    self.AssertOutputEquals(
        """\
---
consumerQuotaLimits:
- metric: example.googleapis.com/mutate_requests
quotaBuckets:
- defaultLimit: '120'
effectiveLimit: '120'
unit: 1/min/{project}
displayName: Mutate requests
metric: example.googleapis.com/mutate_requests
---
consumerQuotaLimits:
- metric: example.googleapis.com/default_requests
quotaBuckets:
- defaultLimit: '120'
effectiveLimit: '240'
unit: 1/min/{project}
displayName: Default requests
metric: example.googleapis.com/default_requests
""",
        normalize_space=True)
