# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud run set-iam-policy`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.run import base


class SetIamPolicyTestBeta(base.ServerlessBase):
  """Tests outputs of set-iam-policy command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def _CreatePolicyFile(self):
    temp_file = self.Touch(
        self.temp_path,
        'policy.json',
        contents="""{
          "bindings": [
            {
              "role": roles/other-role,
              "members": ["user:other-account@gmail.com"]
            }
          ],
          "etag": "bXktZXRhZw=="
        }""")
    return temp_file

  def testSetPolicy(self):
    temp_file = self._CreatePolicyFile()
    self._ExpectSetIamPolicy(
        bindings=[self.other_binding], update_mask='bindings,etag')

    self.Run('run services set-iam-policy my-service '
             '--region us-central1 {}'.format(temp_file))

    self.AssertOutputEquals('''
      bindings:
      - members:
        - user:other-account@gmail.com
        role: roles/other-role
      etag: {}
      '''.format(self.b64etag).lstrip('\n'), normalize_space=True)


class SetIamPolicyTestAlpha(SetIamPolicyTestBeta):
  """Tests outputs of set-iam-policy command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
