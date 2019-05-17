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
"""Integration tests for importing instances from OVF."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute.daisy_utils import FailedBuildException
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_instances_test_base
from tests.lib.surface.compute import e2e_test_base


class InstancesImportTestAlpha(e2e_instances_test_base.InstancesTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testInstanceImportFromOVA(self):
    with self.AssertRaisesExceptionRegexp(
        FailedBuildException,
        re.compile('build .* completed with status "FAILURE', re.S), None):

      self.Run((
          'compute instances import {0} --source-uri {1} --os {2} --zone {3} '
          '--timeout 60s --quiet'
      ).format(
          'ovf-import-instances-import-dummy',
          'gs://dummy-bucket-for-ovf-import-that-doesnt-exit-19231g32/va.ova ',
          'ubuntu-1604', self.zone))

    self.AssertNewErrContainsAll(
        [('WARNING: Importing OVF. This may take 40 minutes for smaller OVFs '
          'and up to a couple of hours for larger OVFs.')])

    self.AssertNewOutputMatchesAll([
        r'starting build ".*"',
        r'\[import-ovf\] .* Starting OVF import workflow\.',
        (r'\[import-ovf\] .* Extracting gs://dummy-bucket-for-ovf-import-that-'
         r'doesnt-exit-19231g32/va\.ova OVA archive to gs://cloud-sdk-'
         r'integration-testing-ovf-import-bkt-us-central1/.*/ovf'),
        (r'\[import-ovf\] .* error while opening archive gs://dummy-bucket-'
         r'for-ovf-import-that-doesnt-exit-19231g32/va.ova: storage: object '
         r'doesn\'t exist')
    ])


if __name__ == '__main__':
  e2e_test_base.main()
