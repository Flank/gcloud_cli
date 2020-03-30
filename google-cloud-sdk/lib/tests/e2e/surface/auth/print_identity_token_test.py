# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.e2e.surface.auth.print_identity_token."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case


class PrintIdentityTokenTest(e2e_base.WithServiceAuth):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def testPrintIdentityToken(self):
    """Test print identity token for a service account."""
    self.Run('auth print-identity-token')
    self.AssertOutputNotContains('No identity token can be obtained from the '
                                 'current credentials.')


if __name__ == '__main__':
  test_case.main()
