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

from googlecloudsdk.api_lib.kuberun import revision


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

REVISION = revision.Revision({
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
    }})

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
