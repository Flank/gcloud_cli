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
"""Tests of the JSON-based Kubernetes object wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import kubernetesobject
from googlecloudsdk.core.console import console_attr
from tests.lib import parameterized
from tests.lib import test_case


class KubernetesObjectTest(parameterized.TestCase):
  """Test KubernetesObject class."""

  def tearDown(self):
    console_attr.ResetConsoleAttr()
    super(KubernetesObjectTest, self)

  def testReadyCondition(self):
    self.assertFalse(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": "False"
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready_condition.status)

  def testReadyCondition_missing(self):
    self.assertIsNone(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "ConfigurationReady",
                    "status": "False"
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready_condition)

  @parameterized.named_parameters(("True", "True", True),
                                  ("False", "False", False),
                                  ("Unknown", "Unknown", None))
  def testReady(self, ready_status, expected):
    self.assertEqual(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": ready_status
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready, expected)

  def testReady_missing(self):
    self.assertIsNone(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "ConfigurationsReady",
                    "status": "False",
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready)

  @parameterized.named_parameters(("Ready", "True", "+"),
                                  ("Not ready", "False", "X"),
                                  ("Unknown", "Unknown", "."))
  def testReadySymbol(self, ready_status, expected):
    self.assertEqual(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": ready_status
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready_symbol, expected)

  @parameterized.named_parameters(
      ("Ready", "True", "\N{HEAVY CHECK MARK}"), ("Not ready", "False", "X"),
      ("Unknown", "Unknown", "\N{HORIZONTAL ELLIPSIS}"))
  def testReadySymbol_utf8(self, ready_status, expected):
    console_attr.ResetConsoleAttr("utf-8")
    self.assertEqual(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": ready_status
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ready_symbol, expected)

  @parameterized.named_parameters(
      ("Ready", "True", ("\N{HEAVY CHECK MARK}", "green")),
      ("Not ready", "False", ("X", "red")),
      ("Unknown", "Unknown", ("\N{HORIZONTAL ELLIPSIS}", "yellow")))
  def testReadySymbolAndColor_utf8(self, ready_status, expected):
    console_attr.ResetConsoleAttr("utf-8")
    self.assertEqual(
        kubernetesobject.KubernetesObject({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": ready_status
                }, {
                    "type": "RoutesReady",
                    "status": "True"
                }]
            }
        }).ReadySymbolAndColor(), expected)


if __name__ == "__main__":
  test_case.main()
