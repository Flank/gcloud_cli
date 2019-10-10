# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Integration test for the 'functions get-logs' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case


class GetLogsIntegrationTest(e2e_base.WithServiceAuth):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testGetLogs(self):
    self.Run('functions logs read')
    for header in ['LEVEL', 'NAME', 'EXECUTION_ID', 'TIME_UTC', 'LOG']:
      self.AssertOutputContains(header)


if __name__ == '__main__':
  test_case.main()
