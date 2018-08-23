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
"""Test of the 'pubsub subscriptions describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsDescribeTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.Get

  def testSubscriptionsAcknowledge(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    subscription = self.msgs.Subscription(name=sub_ref.RelativeName())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsGetRequest(
            subscription=sub_ref.RelativeName()),
        response=subscription)

    result = self.Run('pubsub subscriptions describe subs1')

    self.assertEqual(result, subscription)

  def testSubscriptionsDescribeFullUri(self):
    sub_ref = util.ParseSubscription('subs1', self.Project())
    subscription = self.msgs.Subscription(name=sub_ref.RelativeName())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsGetRequest(
            subscription=sub_ref.RelativeName()),
        response=subscription)

    result = self.Run(
        'pubsub subscriptions describe {}'.format(sub_ref.SelfLink()))

    self.assertEqual(result, subscription)


if __name__ == '__main__':
  test_case.main()
