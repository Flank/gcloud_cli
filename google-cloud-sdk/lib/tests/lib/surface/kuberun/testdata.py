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
"""CloudRun object strings and types to use in tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import devkit
from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.api_lib.kuberun import service

SERVICE_STRING = """{
  "apiVersion": "serving.knative.dev/v1",
  "kind": "Service",
  "metadata": {
    "annotations": {
      "client.knative.dev/user-image": "gcr.io/cloudrun/hello",
      "run.googleapis.com/client-name": "gcloud"
    },
    "creationTimestamp": "2020-09-18T21:56:33Z",
    "generation": 1,
    "name": "hello",
    "namespace": "default",
    "resourceVersion": "2102",
    "selfLink": "/apis/serving.knative.dev/v1/namespaces/default/services/hello",
    "uid": "addfda59-46ec-44f1-8869-2e7cb06215d1"
  },
  "spec": {
    "template": {
      "metadata": {
        "annotations": {
          "client.knative.dev/user-image": "gcr.io/cloudrun/hello",
          "run.googleapis.com/client-name": "gcloud"
        },
        "name": "hello-00001-loq"
      },
      "spec": {
        "containerConcurrency": 0,
        "containers": [
          {
            "image": "gcr.io/cloudrun/hello",
            "name": "user-container",
            "readinessProbe": {
              "successThreshold": 1,
              "tcpSocket": {
                "port": 0
              }
            },
            "resources": {}
          }
        ],
        "timeoutSeconds": 300
      }
    },
    "traffic": [
      {
         "revisionName": "hello-00001-loq",
         "percent": 100,
         "tag": "tag1",
         "url": "hello-00001-loq.service.example.com",
         "latestRevision": false
       }
    ]
  },
  "status": {
    "address": {
      "url": "http://hello.default.svc.cluster.local"
    },
    "conditions": [
      {
        "lastTransitionTime": "2020-09-18T21:56:44Z",
        "status": "True",
        "type": "ConfigurationsReady"
      },
      {
        "lastTransitionTime": "2020-09-18T21:56:44Z",
        "status": "True",
        "type": "Ready"
      },
      {
        "lastTransitionTime": "2020-09-18T21:56:44Z",
        "status": "True",
        "type": "RoutesReady"
      }
    ],
    "latestCreatedRevisionName": "hello-00001-loq",
    "latestReadyRevisionName": "hello-00001-loq",
    "observedGeneration": 1,
    "traffic": [
      {
         "revisionName": "hello-00001-loq",
         "percent": 100,
         "tag": "tag1",
         "url": "hello-00001-loq.service.example.com",
         "latestRevision": false
       }
    ],
    "url": "http://hello.default.example.com"
  }
}"""

SERVICE = service.Service(json.loads(SERVICE_STRING))

REVISION_STRING = """{
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
                    "autoscaling.knative.dev/maxScale": "5"
                }
            },
            "containers": [{
                "name": "user-container",
                "image": "gcr.io/knative-samples/helloworld-go",
                "resources": {
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1.5G"
                    }
                }
            }],
            "serviceAccountName": "hello-sa",
            "containerConcurrency": 5,
            "timeoutSeconds": 300
        },
        "status": {
            "conditions": [{
                "type": "Ready",
                "status": "true"
            }]
        }
    }"""

REVISION = revision.Revision(json.loads(REVISION_STRING))

DOMAIN_MAPPING_STRING = """
{
   "metadata":{
      "name":"hello.example.com",
      "namespace":"default",
      "selfLink":"/apis/domains.cloudrun.com/v1alpha1/namespaces/default/domainmappings/hello.example.com",
      "uid":"228764ec-9b45-4569-b43d-8928ac9895aa",
      "resourceVersion":"39712876",
      "generation":1,
      "creationTimestamp":"2020-09-22T18:54:54Z",
      "finalizers":[
         "domainmappings.domains.cloudrun.com"
      ]
   },
   "spec":{
      "routeName":"hello"
   },
   "status":{
      "conditions":[
         {
            "type":"CertificateProvisioned",
            "status":"Unknown",
            "lastTransitionTime":"2020-09-22T18:54:56Z",
            "reason":"AwaitingChallenge",
            "message":"Waiting Self-Verification of the Challenges"
         },
         {
            "type":"DomainMappingGatewayReady",
            "status":"True",
            "lastTransitionTime":"2020-09-22T18:54:54Z"
         },
         {
            "type":"GatewayReady",
            "status":"True",
            "lastTransitionTime":"2020-09-22T18:54:54Z"
         },
         {
            "type":"Ready",
            "status":"Unknown",
            "lastTransitionTime":"2020-09-22T18:54:56Z",
            "reason":"AwaitingChallenge",
            "message":"Waiting Self-Verification of the Challenges"
         },
         {
            "type":"RouteReady",
            "status":"True",
            "lastTransitionTime":"2020-09-22T18:54:54Z"
         }
      ],
      "resourceRecords":[
         {
            "name":"hello",
            "type":"A",
            "rrdata":"35.233.197.0"
         }
      ],
      "mappedRouteName":"hello"
   }
}
"""


DEVKITS_LIST_JSON = """
[
  {
    "id": "test-devkit",
    "name": "Unit Test Development Kit",
    "description": "A Fake Development Kit for Unit Testing",
    "version": "v0.1.0"
  }
]
"""

DEVKITS_LIST = [
    devkit.DevKit(
        id_='test-devkit',
        name='Unit Test Development Kit',
        description='A Fake Development Kit for Unit Testing',
        version='v0.1.0')
]
