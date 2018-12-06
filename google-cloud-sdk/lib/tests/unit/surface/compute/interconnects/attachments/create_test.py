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
"""Tests for the interconnect create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import test_base


# TODO(b/79153388): Clean up this test after 3 months of deprecation.
class InterconnectAttachmentsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def testCreateInterconnectAttachment_deprecated(self):
    with self.assertRaisesRegexp(
        calliope_base.DeprecationException,
        '`create` has been removed. Please use `gcloud compute interconnects '
        'attachments dedicated create` instead.'):
      self.Run(
          'compute interconnects attachments create my-attachment --region '
          'us-central1 --interconnect my-interconnect --router my-router '
          '--description "this is my attachment" ')


class InterconnectAttachmentsCreateBetaTest(InterconnectAttachmentsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta


class InterconnectAttachmentsCreateAlphaTest(InterconnectAttachmentsCreateTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha
