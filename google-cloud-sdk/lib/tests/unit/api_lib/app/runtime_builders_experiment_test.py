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
"""Integration test between runtime builders experiment parser and config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.app import runtime_builders
from tests.lib import sdk_test_base
from tests.lib import test_case


class ExperimentsTest(sdk_test_base.WithFakeAuth):

  # this test depends on a file in google3/third-party outside of cloudsdk,
  # execute it only on TAP presubmit
  @test_case.Filters.DoNotRunInDebPackage
  @test_case.Filters.DoNotRunInRpmPackage
  @test_case.Filters.DoNotRunInKokoro
  def testLoadManifest(self):
    builder_root = 'file://%s' % os.path.dirname(
        os.path.join(os.getcwd(),
                     'third_party/runtimes_common/config/experiments.yaml'))
    experiments = runtime_builders.Experiments.LoadFromURI(builder_root)
    self.assertIsNotNone(experiments)


if __name__ == '__main__':
  test_case.main()
