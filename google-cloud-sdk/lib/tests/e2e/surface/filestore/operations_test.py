# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""e2e tests for Cloud Filestore operations command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case


class OperationsTest(e2e_base.WithServiceAuth):
  """E2E tests for Cloud Filestore operations command group."""

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.location = 'us-central1-c'

  def testListAndDescribe(self):
    operations_result = self.Run(
        'filestore operations list --location {} --limit 2'.format(
            self.location))
    operations = list(operations_result)
    if operations:
      operation_name = operations[0]
      self.Run(
          'filestore operations describe {} --location {}'.format(
              operation_name, self.location))
      self.AssertOutputContains(operation_name)


class OperationsAlphaTest(OperationsTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
