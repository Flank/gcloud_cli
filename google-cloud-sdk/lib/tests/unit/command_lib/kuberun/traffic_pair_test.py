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
"""Tests for the traffic printer helper methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import traffic
from googlecloudsdk.command_lib.kuberun import traffic_pair
from tests.lib import test_case


class TrafficPairTest(test_case.TestCase):

  def testSortKeyFromTarget(self):
    rev1 = traffic.TrafficTarget({
        "revisionName": "rev1",
        "latestRevision": True})
    rev2 = traffic.TrafficTarget({
        "revisionName": "rev2",
        "latestRevision": False})

    self.assertGreater(
        traffic_pair.SortKeyFromTarget(rev1),
        traffic_pair.SortKeyFromTarget(rev2))

  def testSpecPercent_noSpecTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).specPercent, "-")

  def testSpecPercent_withSpecTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"percent": 15}),
            traffic.TrafficTarget({"percent": 15})
        ], [], "rev1", False).specPercent, "30")

  def testStatusPercent_noStatusTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).statusPercent,
        "-")

  def testStatusPercent_withStatusTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [
            traffic.TrafficTarget({"percent": 15}),
            traffic.TrafficTarget({"percent": 15})
        ], "rev1", False).statusPercent, "30")

  def testSpecTags_noSpecTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).specTags, "-")

  def testSpecTags_withSpecTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"tag": "tag1"}),
            traffic.TrafficTarget({"tag": "tag2"})
        ], [], "rev1", False).specTags, "tag1, tag2")

  def testStatusTags_noStatusTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).statusTags, "-")

  def testStatusTags_withStatusTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [
            traffic.TrafficTarget({"tag": "tag1"}),
            traffic.TrafficTarget({"tag": "tag2"})
        ], "rev1", False).statusTags, "tag1, tag2")

  def testUrls_empty(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).urls, [])

  def testUrls_withTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair(
            [traffic.TrafficTarget({"url": "spec1"})], [
                traffic.TrafficTarget({"url": "status1"}),
                traffic.TrafficTarget({"url": "status2"})
            ], "rev1", False).urls, ["status1", "status2"])

  def testDisplayPercent_noTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).displayPercent,
        "-")

  def testDisplayPercent_sameSpecAndStatusSumPercent(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"percent": 15}),
            traffic.TrafficTarget({"percent": 15})
        ], [
            traffic.TrafficTarget({"percent": 20}),
            traffic.TrafficTarget({"percent": 10})
        ], "rev1", False).displayPercent, "30%")

  def testDisplayPercent_differentSpecAndStatusSumPercent(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"percent": 15}),
            traffic.TrafficTarget({"percent": 15})
        ], [
            traffic.TrafficTarget({"percent": 20}),
            traffic.TrafficTarget({"percent": 20})
        ], "rev1", False).displayPercent, "30%  (currently 40%)")

  def testDisplayRevisionId_notLatest(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).displayRevisionId,
        "rev1")

  def testDisplayRevisionId_Latest(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", True).displayRevisionId,
        "LATEST (currently rev1)")

  def testDisplayTags_noTraffic(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([], [], "rev1", False).displayTags, "")

  def testDisplayTags_sameTags(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"tag": "tag1"}),
            traffic.TrafficTarget({"tag": "tag2"})
        ], [
            traffic.TrafficTarget({"tag": "tag1"}),
            traffic.TrafficTarget({"tag": "tag2"})
        ], "rev1", False).displayTags, "tag1, tag2")

  def testDisplayTags_differentTags(self):
    self.assertEqual(
        traffic_pair.TrafficTargetPair([
            traffic.TrafficTarget({"tag": "tag1"}),
            traffic.TrafficTarget({"tag": "tag2"})
        ], [
            traffic.TrafficTarget({"tag": "tag3"}),
            traffic.TrafficTarget({"tag": "tag4"})
        ], "rev1", False).displayTags, "tag1, tag2 (currently tag3, tag4)")

  def testGetTrafficTargetPairs_noLatest(self):
    spec_traffic = {
        "rev1": [traffic.TrafficTarget({"revisionName": "rev1"})],
        "rev2": [traffic.TrafficTarget({"revisionName": "rev2"})]
    }
    status_traffic = {
        "rev1": [traffic.TrafficTarget({"revisionName": "rev1"})],
        "rev2": [traffic.TrafficTarget({"revisionName": "rev2"})]
    }
    latest_ready_revision_name = "rev3"
    url = "service.example.com"

    pairs = traffic_pair.GetTrafficTargetPairs(spec_traffic, status_traffic,
                                               latest_ready_revision_name, url)
    self.assertIsNotNone(pairs)
    self.assertEqual(len(pairs), 2)
    self.assertEqual(pairs[0].revisionName, "rev1")
    self.assertEqual(pairs[1].revisionName, "rev2")

  def testGetTrafficTargetPairs_latestReadyRevOverridesTargetName(self):
    spec_traffic = {
        "LATEST": [traffic.TrafficTarget({"revisionName": "rev1"})],
        "rev2": [traffic.TrafficTarget({"revisionName": "rev2"})]
    }
    status_traffic = {
        "LATEST": [traffic.TrafficTarget({"revisionName": "rev1"})],
        "rev2": [traffic.TrafficTarget({"revisionName": "rev2"})]
    }
    latest_ready_revision_name = "rev3"
    url = "service.example.com"

    pairs = traffic_pair.GetTrafficTargetPairs(spec_traffic, status_traffic,
                                               latest_ready_revision_name, url)
    self.assertIsNotNone(pairs)
    self.assertEqual(len(pairs), 2)
    self.assertEqual(pairs[0].revisionName, "rev2")
    self.assertEqual(pairs[1].revisionName, "rev3")

if __name__ == "__main__":
  test_case.main()
