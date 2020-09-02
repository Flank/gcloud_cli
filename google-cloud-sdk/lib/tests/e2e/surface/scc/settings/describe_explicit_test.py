# Lint as: python3
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
"""Integration tests for the 'gcloud scc settings describe-explicit' commands."""

from tests.lib import test_case
from tests.lib.surface.scc import base


class DescribeExplicitTest(base.SecurityCenterSettingsE2ETestBase):

  def test_describe_explicit(self):
    # TODO(b/146082827) Set up new org after bug closed.
    self.RunSccSettings(
        'settings', 'describe-explicit', '--organization',
        '702114178617')  # This org is from scc notifications e2e testing.
    self.AssertOutputContains('securityCenterSettings')


if __name__ == '__main__':
  test_case.main()
