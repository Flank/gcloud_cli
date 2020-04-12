# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for 'configmanagement disable' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.container.hub.features import base


class DisableTest(base.FeaturesTestBase):
  """Tests for the logic of 'configmanagement disable' command.
  """

  FEATURE_NAME = 'configmanagement'
  FEATURE_DISPLAY_NAME = 'Config Management'
  NO_FEATURE_PREFIX = True

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def _ExpectDeleteCalls(self):
    operation = self.features_api._MakeOperation()
    self.features_api.ExpectDelete(operation)
    self.features_api.ExpectOperation(operation)
    operation = self.features_api._MakeOperation(done=True)
    self.features_api.ExpectOperation(operation)

  def testRunDisable(self):
    self._ExpectDeleteCalls()
    self.RunCommand(['disable'])


if __name__ == '__main__':
  test_case.main()
