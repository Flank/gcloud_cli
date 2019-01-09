# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests that exercise the 'gcloud dns policies delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.dns import base


class DeleteTest(base.DnsMockBetaTest):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def testDelete(self):
    delete_req = self.messages.DnsPoliciesDeleteRequest(
        project=self.Project(), policy='mypolicy0')
    delete_resp = self.messages.DnsPoliciesDeleteResponse()
    self.client.policies.Delete.Expect(request=delete_req, response=delete_resp)
    self.WriteInput('y')
    self.Run('dns policies delete mypolicy0')
    self.AssertErrContains('Deleted policy [mypolicy0].')


if __name__ == '__main__':
  test_case.main()
