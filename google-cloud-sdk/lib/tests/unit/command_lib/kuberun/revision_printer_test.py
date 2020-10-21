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
"""Unit tests for the revision printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.kuberun import revision_printer
from googlecloudsdk.command_lib.run import revision_printer as run_rev_printer
from tests.lib.core.resource import resource_printer_test_base
from tests.lib.surface.kuberun import cloudrun_object_helpers as runhelpers

run_v1_messages = apis.GetMessagesModule("run", "v1")


class RevisionPrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = revision_printer.RevisionPrinter()

  def testEmptyDefault(self):
    self._printer.Finish()
    self.AssertOutputEquals("")

  def testServiceRevisionTemplate_consistentWithCloudRun(self):
    container = runhelpers.Container(
        "user-container",
        "gcr.io/knative-samples/helloworld-go",
        env_vars={"TARGET": "KNATIVE"},
        secrets=[{
            "name": "mysecret",
            "secretKey": "secretkey",
            "secretName": "secretname"
        }],
        config_maps=[{
            "name": "myconfig",
            "configKey": "configkey",
            "configName": "configname"
        }],
        command=["run", "this", "container"],
        args=["use", "these", "arguments"],
        ports=[{
            "name": "http1",
            "port": 12345,
            "protocol": "TCP"
        }],
        limits={
            "cpu": "1000m",
            "memory": "1.5G"
        })
    spec = runhelpers.RevisionSpec(container, "hello-sa", 300, 5)
    meta = runhelpers.Metadata(
        "hello-dxtvy-1",
        "default",
        annotations={
            "client.knative.dev/user-image":
                "gcr.io/knative-samples/helloworld-go"
        },
        labels={"labelKey": "labelValue"})
    status = runhelpers.RevisionStatus(
        [runhelpers.Condition(condition_type="Ready", status="True")])

    run_rev = runhelpers.Revision(runhelpers.TestMessagesModule(), meta, spec,
                                  status)

    run_printer = run_rev_printer.RevisionPrinter()
    run_printer.AddRecord(run_rev)
    run_printer.Finish()
    run_out = self.GetOutput()
    self.ClearOutput()

    rev = revision.Revision({
        "metadata": {
            "namespace": "default",
            "name": "hello-dxtvy-1",
            "annotations": {
                "client.knative.dev/user-image":
                    "gcr.io/knative-samples/helloworld-go"
            },
            "labels": {
                "labelKey": "labelValue"
            }
        },
        "spec": {
            "metadata": {
                "annotations": {
                    "autoscaling.knative.dev/minScale": "1",
                    "autoscaling.knative.dev/maxScale": "5",
                }
            },
            "containers": [{
                "name": "user-container",
                "image": "gcr.io/knative-samples/helloworld-go",
                "command": [
                    "run",
                    "this",
                    "container",
                ],
                "args": [
                    "use",
                    "these",
                    "arguments",
                ],
                "ports": [{
                    "containerPort": 12345,
                    "name": "http1",
                    "protocol": "TCP"
                }],
                "env": [{
                    "name": "TARGET",
                    "value": "KNATIVE"
                }, {
                    "name": "mysecret",
                    "valueFrom": {
                        "secretKeyRef": {
                            "key": "secretkey",
                            "name": "secretname",
                        }
                    }
                }, {
                    "name": "myconfig",
                    "valueFrom": {
                        "configMapKeyRef": {
                            "key": "configkey",
                            "name": "configname",
                        }
                    }
                }],
                "resources": {
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1.5G"
                    }
                },
            }],
            "serviceAccountName": "hello-sa",
            "containerConcurrency": 5,
            "timeoutSeconds": 300
        },
        "status": {
            "conditions": [{
                "type": "Ready",
                "status": "true",
            }]
        }
    })
    self._printer.AddRecord(rev)
    self._printer.Finish()

    self.AssertOutputEquals(run_out)

  def testWithBasicRevision(self):
    rev = revision.Revision({
        "metadata": {
            "namespace": "default",
            "name": "hello-dxtvy-1",
        },
        "spec": {
            "metadata": {
            },
            "containers": [{
                "name": "user-container",
                "image": "gcr.io/knative-samples/helloworld-go",
                "resources": {},
            }],
            "serviceAccountName": "hello-sa",
        },
        "status": {
            "conditions": [{
                "type": "Ready",
                "status": "true",
            }]
        }
    })
    printer = revision_printer.RevisionPrinter()
    printer.Transform(rev)
    self.assertIsNone(printer.GetMinInstances(rev))
    self.assertIsNone(printer.GetMaxInstances(rev))
    self.assertIsNone(printer.GetTimeout(rev))
    self.assertEqual(printer.GetUserEnvironmentVariables(rev), [])
    self.assertEqual(printer.GetSecrets(rev), [])
    self.assertEqual(printer.GetConfigMaps(rev), [])

