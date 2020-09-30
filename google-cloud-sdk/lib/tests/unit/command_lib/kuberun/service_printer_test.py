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
"""Unit tests for service_printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import service
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.kuberun import service_printer
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import service_printer as run_svc_printer
from googlecloudsdk.core import properties
from tests.lib.core.resource import resource_printer_test_base
from tests.lib.surface.kuberun import cloudrun_object_helpers as runhelpers

run_v1_messages = apis.GetMessagesModule("run", "v1")


class ServicePrinterTest(resource_printer_test_base.Base):

  def SetUp(self):
    self._printer = service_printer.ServicePrinter()
    self.ShowTestOutput()

  def testEmptyDefault(self):
    self._printer.Finish()
    self.AssertOutputEquals("")

  def testService_consistentWithCloudRun(self):
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
        },
        volume_mounts=[{
            "name": "secretvol",
            "path": "/path/to/secret"
        }, {
            "name": "configmapvol",
            "path": "/path/to/configmap"
        }])
    spec = runhelpers.RevisionSpec(
        container,
        "hello-sa",
        300,
        5,
        volumes=[{
            "name": "secretvol",
            "secret": {
                "secretName": "mySecretName",
                "items": [{
                    "key": "secretKey",
                    "path": "foo/bar/secret"
                }]
            }
        }, {
            "name": "configmapvol",
            "configMap": {
                "name": "myconfigMapName",
                "items": [{
                    "key": "configMapKey",
                    "path": "foo/bar/configMap"
                }]
            }
        }])
    meta = runhelpers.Metadata(
        "hello-dxtvy-1",
        "default",
        annotations={
            "client.knative.dev/user-image":
                "gcr.io/knative-samples/helloworld-go"
        },
        labels={"labelKey": "labelValue"})
    rev_msg = run_v1_messages.RevisionTemplate()
    rev_msg.metadata = meta
    rev_msg.spec = spec

    spec_traffic = (runhelpers.TrafficTarget("rev1", 30, None, "tag1",
                                             "rev1.service.example.com"),
                    runhelpers.TrafficTarget("rev2", 30, False, "tag2",
                                             "rev2.service.example.com"),
                    runhelpers.TrafficTarget("", 40, True, "tag3",
                                             "conf3.service.example.com",
                                             "conf3"))
    svc_spec = runhelpers.ServiceSpec(rev_msg, spec_traffic)

    status_traffic = (runhelpers.TrafficTarget("rev1", 50, None, "tag1",
                                               "rev1.service.example.com"),
                      runhelpers.TrafficTarget("rev2", 50, False, "tag2",
                                               "rev2.service.example.com"))
    ready_cond = runhelpers.Condition(
        "Ready", "false", last_transition_time="2020-02-28T16:09:23Z")
    conf_cond = runhelpers.Condition(
        "ConfigurationsReady",
        "true",
        last_transition_time="2020-01-31T01:06:31Z")
    route_cond = runhelpers.Condition(
        "RoutesReady", last_transition_time="2020-03-31T16:09:23Z")
    svc_status = runhelpers.ServiceStatus("service-address.example.com",
                                          (route_cond, conf_cond, ready_cond),
                                          "rev2", "rev2", 42, status_traffic,
                                          "service-url.example.com")
    svc_meta = runhelpers.Metadata(
        "my-service", "my-namespace", {
            "serving.knative.dev/creator": "foo@example.com",
            "serving.knative.dev/lastModifier": "bar@example.com"
        }, {"svc-label": "svc-label-value"})
    svc = runhelpers.RunService(runhelpers.TestMessagesModule(), svc_meta,
                                svc_spec, svc_status)

    properties.VALUES.run.platform.Set(flags.PLATFORM_GKE)
    run_printer = run_svc_printer.ServicePrinter()
    run_printer.AddRecord(svc)
    run_printer.Finish()
    run_out = self.GetOutput()
    self.ClearOutput()

    kuberun_svc = service.Service({
        "kind": "Service",
        "apiVersion": "serving.knative.dev/v1",
        "metadata": {
            "name": "my-service",
            "namespace": "my-namespace",
            "generation": 42,
            "annotations": {
                "serving.knative.dev/creator": "foo@example.com",
                "serving.knative.dev/lastModifier": "bar@example.com"
            },
            "labels": {
                "svc-label": "svc-label-value"
            },
        },
        "spec": {
            "template": {
                "metadata": {
                    "name": "hello-dxtvy-1",
                    "annotations": {
                        "client.knative.dev/user-image":
                            "gcr.io/knative-samples/helloworld-go"
                    },
                    "labels": {
                        "labelKey": "labelValue",
                    }
                },
                "spec": {
                    "containers": [{
                        "command": ["run", "this", "container"],
                        "args": ["use", "these", "arguments"],
                        "name":
                            "user-container",
                        "image":
                            "gcr.io/knative-samples/helloworld-go",
                        "env": [{
                            "name": "TARGET",
                            "value": "KNATIVE"
                        }, {
                            "name": "mysecret",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "key": "secretkey",
                                    "name": "secretname"
                                }
                            }
                        }, {
                            "name": "myconfig",
                            "valueFrom": {
                                "configMapKeyRef": {
                                    "key": "configkey",
                                    "name": "configname"
                                }
                            }
                        }],
                        "ports": [{
                            "containerPort": 12345
                        }],
                        "resources": {
                            "limits": {
                                "cpu": "1000m",
                                "memory": "1.5G",
                            }
                        },
                        "volumeMounts": [{
                            "name": "secretvol",
                            "mountPath": "/path/to/secret"
                        }, {
                            "name": "configmapvol",
                            "mountPath": "/path/to/configmap"
                        }]
                    }],
                    "serviceAccountName":
                        "hello-sa",
                    "containerConcurrency":
                        5,
                    "timeoutSeconds":
                        300,
                    "volumes": [{
                        "name": "secretvol",
                        "secret": {
                            "secretName":
                                "mySecretName",
                            "items": [{
                                "key": "secretKey",
                                "path": "foo/bar/secret"
                            }]
                        }
                    }, {
                        "name": "configmapvol",
                        "configMap": {
                            "name":
                                "myconfigMapName",
                            "items": [{
                                "key": "configMapKey",
                                "path": "foo/bar/configMap"
                            }]
                        }
                    }]
                }
            },
            "traffic": [{
                "revisionName": "rev1",
                "percent": 30,
                "tag": "tag1",
                "url": "rev1.service.example.com",
            }, {
                "revisionName": "rev2",
                "percent": 30,
                "latestRevision": False,
                "tag": "tag2",
                "url": "rev2.service.example.com",
            }, {
                "revisionName": "",
                "configName": "conf3",
                "latestRevision": True,
                "percent": 40,
                "tag": "tag3",
                "url": "conf3.service.example.com",
            }]
        },
        "status": {
            "observedGeneration":
                3,
            "conditions": [{
                "type": "ConfigurationsReady",
                "status": "True",
                "lastTransitionTime": "2020-01-31T01:06:31Z"
            }, {
                "type": "Ready",
                "status": "False",
                "lastTransitionTime": "2020-02-28T16:09:23Z"
            }, {
                "type": "RoutesReady",
                "status": "Unknown",
                "lastTransitionTime": "2020-03-31T16:09:23Z"
            }],
            "latestReadyRevisionName":
                "rev2",
            "latestCreatedRevisionName":
                "rev2",
            "url":
                "service-url.example.com",
            "address": {
                "url": "service-address.example.com"
            },
            "traffic": [{
                "revisionName": "rev1",
                "percent": 50,
                "latestRevision": False,
                "tag": "tag1",
                "url": "rev1.service.example.com",
            }, {
                "revisionName": "rev2",
                "percent": 50,
                "tag": "tag2",
                "url": "rev2.service.example.com",
            }]
        }
    })
    self._printer.AddRecord(kuberun_svc)
    self._printer.Finish()
    self.AssertOutputEquals(run_out)
