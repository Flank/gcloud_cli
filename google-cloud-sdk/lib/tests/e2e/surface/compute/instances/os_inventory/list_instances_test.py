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
"""Integration tests for for listing instances with specific OS inventory data values."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import e2e_test_base


# Setup instructions for the required static resource is at
# go/os-inventory-cloud-sdk-test-resource-setup.
class ListInstancesTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testListInstancesWithInventoryFilter(self):
    # Hostname should contain "os-inventory"
    self.Run('compute instances os-inventory list-instances '
             '--inventory-filter="Hostname:os-inventory"')
    self.AssertNewOutputContains(
        'do-not-delete-compute-instances-os-inventory-test')

  def testListInstancesWithNoInventoryFilterArg(self):
    self.Run('compute instances os-inventory list-instances')
    self.AssertNewOutputContains(
        'do-not-delete-compute-instances-os-inventory-test')

  def testListInstancesWithOsShortnameFilter(self):
    # ShortName should equal "debian"
    self.Run('compute instances os-inventory list-instances '
             '--os-shortname="debian"')
    self.AssertNewOutputContains(
        'do-not-delete-compute-instances-os-inventory-test')


if __name__ == '__main__':
  e2e_test_base.main()
