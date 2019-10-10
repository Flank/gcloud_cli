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
"""Tests for `gcloud run remove-iam-policy`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.run import base


class RemoveIamPolicyTestBeta(base.ServerlessBase):
  """Tests outputs of remove-iam-policy command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testRemovePolicy(self):
    self._ExpectGetIamPolicy()
    self._ExpectSetIamPolicy(bindings=[self.next_binding])

    self.Run(
        'run services remove-iam-policy-binding my-service --member '
        'user:my-account@gmail.com --role roles/my-role --region us-central1')

    self.AssertOutputEquals('''
      bindings:
      - members:
        - user:next@gmail.com
        role: roles/next
      etag: {}
      '''.format(self.b64etag).lstrip('\n'), normalize_space=True)


class RemoveIamPolicyTestAlpha(RemoveIamPolicyTestBeta):
  """Tests outputs of remove-iam-policy command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
