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
"""Tests for the JSON-based Kubernetes service wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import service
from tests.lib import test_case


class ServiceTest(test_case.TestCase):

  def testUrl(self):
    self.assertEqual(
        service.Service({
            "status": {
                "url": "https://service.example.com"
            }
        }).url, "https://service.example.com")

  def testSpecTraffic(self):
    spec_traffic = service.Service({
        "spec": {
            "traffic": [{
                "revisionName": "rev1",
                "percent": 40,
                "latestRevision": False,
                "tag": "tag1",
                "url": "rev1.service.example.com",
            }, {
                "revisionName": "rev2",
                "percent": 60,
                "latestRevision": True,
                "tag": "tag2",
                "url": "rev2.service.example.com",
            }]
        }
    }).spec_traffic
    self.assertIsNotNone(spec_traffic)
    self.assertIn("LATEST", spec_traffic)
    self.assertIn("rev1", spec_traffic)

  def testEmptySpecTraffic(self):
    spec_traffic = service.Service({"spec": {}}).spec_traffic
    self.assertIsNotNone(spec_traffic)
    self.assertEqual(dict(), spec_traffic)

  def testStatusTraffic(self):
    status_traffic = service.Service({
        "status": {
            "traffic": [{
                "revisionName": "rev1",
                "percent": 40,
                "latestRevision": False,
                "tag": "tag1",
                "url": "rev1.service.example.com",
            }, {
                "revisionName": "rev2",
                "percent": 60,
                "latestRevision": True,
                "tag": "tag2",
                "url": "rev2.service.example.com",
            }]
        }
    }).status_traffic
    self.assertIsNotNone(status_traffic)
    self.assertIn("LATEST", status_traffic)
    self.assertIn("rev1", status_traffic)

  def testEmptyStatusTraffic(self):
    status_traffic = service.Service({"status": {}}).status_traffic
    self.assertIsNotNone(status_traffic)
    self.assertEqual(dict(), status_traffic)

  def testReadySymbolAndColor(self):
    self.assertEqual(
        service.Service({
            "status": {
                "latestCreatedRevisionName": "rev1",
                "latestReadyRevisionName": "rev2",
                "conditions": [{
                    "type": "Ready",
                    "status": "False"
                }]
            }
        }).ReadySymbolAndColor(), ("!", "yellow"))


if __name__ == "__main__":
  test_case.main()
