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
"""Tests for the JSON-based Kubernetes service traffic settings wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import traffic
from tests.lib import test_case


class TrafficTest(test_case.TestCase):

  def testGetKey_latest(self):
    self.assertEqual(
        traffic.GetKey(
            traffic.TrafficTarget({
                "revisionName": "rev1",
                "latestRevision": True
            })), "LATEST")

  def testGetKey_notLatest(self):
    self.assertEqual(
        traffic.GetKey(
            traffic.TrafficTarget({
                "revisionName": "rev1",
                "latestRevision": False
            })), "rev1")


if __name__ == "__main__":
  test_case.main()
