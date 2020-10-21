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
"""Tests for the JSON-based Kubernetes service template wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import revision
from tests.lib import test_case


class RevisionTest(test_case.TestCase):

  def testUserImage_noImage(self):
    self.assertIsNone(
        revision.Revision({
            "spec": {
                "containers": [{}]
            }
        }).UserImage())

  def testUserImage_noImageHash(self):
    self.assertEqual(
        revision.Revision({
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld"
                }]
            }
        }).UserImage(), "gcr.us/helloworld")

  def testUserImage_hasImageHashNoAnnotation(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {}
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa"
                }]
            }
        }).UserImage(), "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa")

  def testUserImage_hasImageHashOutOfDateAnnotation(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {
                    "client.knative.dev/user-image": "gcr.us/oldimage",
                }
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa"
                }]
            }
        }).UserImage(), "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa")

  def testUserImage_hasImageHashOutOfDateServiceAnnotation(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {}
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa"
                }]
            }
        }).UserImage("gcr.us/oldimage"),
        "gcr.us/helloworld@sha256:aaaaaaaaaaaaaaa")

  def testUserImage_hasImageHashUpToDateAnnotation(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {
                    "client.knative.dev/user-image": "gcr.us/helloworld",
                }
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:123456789"
                }]
            }
        }).UserImage(), "gcr.us/helloworld at 12345678...")

  def testUserImage_hasImageHashUpToDateServiceAnnotation(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {}
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:123456789"
                }]
            }
        }).UserImage("gcr.us/helloworld"), "gcr.us/helloworld at 12345678...")

  def testUserImage_hasImageHashUpToDateAnnotationAndOldServiceAnnotation(self):
    # revision annotation overrides service annotation
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {
                    "client.knative.dev/user-image": "gcr.us/helloworld"
                }
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:123456789"
                }]
            }
        }).UserImage("gcr.us/oldimage"), "gcr.us/helloworld at 12345678...")

  def testUserImage_hasImageHashOldAnnotationAndUpToDateServiceAnnotation(self):
    # revision annotation overrides service annotation, but considered out of
    # date
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "annotations": {
                    "client.knative.dev/user-image": "gcr.us/oldimage"
                }
            },
            "spec": {
                "containers": [{
                    "image": "gcr.us/helloworld@sha256:aaaaaaaaa"
                }]
            }
        }).UserImage("gcr.us/helloworld"), "gcr.us/helloworld@sha256:aaaaaaaaa")

  def testCreationTimestamp(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "creationTimestamp": "2019-05-20T18:26:35.210Z"
            }
        }).creation_timestamp, "2019-05-20T18:26:35.210Z")

  def testServiceName(self):
    self.assertEqual(
        revision.Revision({
            "metadata": {
                "labels": {
                    "serving.knative.dev/service": "my-svc"
                }
            }
        }).service_name, "my-svc")

  def testActive(self):
    self.assertEqual(
        revision.Revision({
            "status": {
                "conditions": [{
                    "type": "Active",
                    "status": "True"
                }]
            }
        }).active, True)

  def testReadySymbolAndColor(self):
    self.assertEqual(
        revision.Revision({
            "status": {
                "conditions": [{
                    "type": "Ready",
                    "status": "False"
                }]
            }
        }).ReadySymbolAndColor(), ("!", "yellow"))

  def testVolumesSecret(self):
    s = revision.Revision({
        "spec": {
            "volumes": [{
                "name": "myvolumeName",
                "secret": {
                    "secretName": "mysecret",
                    "items": [{
                        "key": "mysecretKey",
                        "path": "mysecretPath"
                    }]
                }
            }]
        }
    }).volumes.secrets
    self.assertEqual(len(s), 1)
    self.assertIn("myvolumeName", s)
    self.assertDictEqual(
        s["myvolumeName"]._props, {
            "secretName": "mysecret",
            "items": [{
                "key": "mysecretKey",
                "path": "mysecretPath"
            }]
        })

  def testVolumesConfigMap(self):
    cm = revision.Revision({
        "spec": {
            "volumes": [{
                "name": "myvolumeName",
                "configMap": {
                    "name":
                        "myconfigMap",
                    "items": [{
                        "key": "myconfigMapKey",
                        "path": "myconfigMapPath"
                    }]
                }
            }]
        }
    }).volumes.config_maps
    self.assertEqual(len(cm), 1)
    self.assertIn("myvolumeName", cm)
    self.assertDictEqual(
        cm["myvolumeName"]._props, {
            "name": "myconfigMap",
            "items": [{
                "key": "myconfigMapKey",
                "path": "myconfigMapPath"
            }]
        })

  def testVolumeMountsSecret(self):
    r = revision.Revision({
        "spec": {
            "containers": [{
                "volumeMounts": [{
                    "mountPath": "/my/secret/path",
                    "name": "myvolumeName",
                }]
            }],
            "volumes": [{
                "name": "myvolumeName",
                "secret": {
                    "secretName": "mysecret",
                    "items": [{
                        "key": "mysecretKey",
                        "path": "mysecretPath"
                    }]
                }
            }]
        }
    })
    s = r.volume_mounts.secrets
    self.assertEqual(len(s), 1)
    self.assertIn("/my/secret/path", s)
    self.assertDictEqual(s, {"/my/secret/path": "myvolumeName"})

  def testVolumeMountsConfigMap(self):
    cm = revision.Revision({
        "spec": {
            "containers": [{
                "volumeMounts": [{
                    "mountPath": "/my/configMap/path",
                    "name": "myvolumeName",
                }]
            }],
            "volumes": [{
                "name": "myvolumeName",
                "configMap": {
                    "name":
                        "myconfigMap",
                    "items": [{
                        "key": "myconfigMapKey",
                        "path": "myconfigMapPath"
                    }]
                }
            }]
        }
    }).volume_mounts.config_maps
    self.assertEqual(len(cm), 1)
    self.assertIn("/my/configMap/path", cm)
    self.assertDictEqual(cm, {"/my/configMap/path": "myvolumeName"})


class EnvVarsTest(test_case.TestCase):

  TEST_ENV_VARS = [
      {
          # literal
          "name": "envVar",
          "value": "val1"
      },
      {
          # secret
          "name": "secretVar",
          "valueFrom": {
              "secretKeyRef": {
                  "name": "secretname",
                  "key": "secretkey",
              }
          }
      },
      {
          # config map
          "name": "configMapVar",
          "valueFrom": {
              "configMapKeyRef": {
                  "name": "configmapname",
                  "key": "configmapkey",
              }
          }
      }
  ]

  def testLiterals_noLiterals(self):
    self.assertEqual(revision.EnvVars(self.TEST_ENV_VARS[1:]).literals, {})

  def testLiterals(self):
    l = revision.EnvVars(self.TEST_ENV_VARS).literals
    self.assertIsNotNone(l)
    self.assertEqual(len(l), 1)
    self.assertIn("envVar", l)

  def testSecrets_noSecret(self):
    self.assertEqual(
        revision.EnvVars([self.TEST_ENV_VARS[0],
                          self.TEST_ENV_VARS[2]]).secrets, {})

  def testSecrets(self):
    s = revision.EnvVars(self.TEST_ENV_VARS).secrets
    self.assertIsNotNone(s)
    self.assertEqual(len(s), 1)
    self.assertIn("secretVar", s)

  def testConfigMaps_noConfigMap(self):
    self.assertEqual(revision.EnvVars(self.TEST_ENV_VARS[:2]).config_maps, {})

  def testConfigMaps(self):
    c = revision.EnvVars(self.TEST_ENV_VARS).config_maps
    self.assertIsNotNone(c)
    self.assertEqual(len(c), 1)
    self.assertIn("configMapVar", c)

  def testNoneLiterals(self):
    l = revision.EnvVars(None).literals
    self.assertIsNotNone(l)
    self.assertEqual(dict(), l)

  def testNoneConfigMaps(self):
    c = revision.EnvVars(None).config_maps
    self.assertIsNotNone(c)
    self.assertEqual(dict(), c)

  def testNoneSecrets(self):
    s = revision.EnvVars(None).secrets
    self.assertIsNotNone(s)
    self.assertEqual(dict(), s)


if __name__ == "__main__":
  test_case.main()
