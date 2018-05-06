# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Test of the 'pubsub subscriptions delete' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SubscriptionsDeleteTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_subscriptions.Delete

  def testSubscriptionsDelete(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    subscription_to_delete = util.ParseSubscription(
        'subs1', self.Project()).RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=subscription_to_delete),
        response='')

    self.Run('pubsub subscriptions delete subs1')

    self.AssertErrContains(
        'Deleted subscription [{}]'.format(subscription_to_delete))

  def testSubscriptionsDeleteFullUri(self):
    properties.VALUES.core.user_output_enabled.Set(True)
    subscription_to_delete = util.ParseSubscription(
        'subs1', self.Project())
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=subscription_to_delete.RelativeName()),
        response='')

    self.Run('pubsub subscriptions delete {}'
             .format(subscription_to_delete.SelfLink()))

    self.AssertErrContains('Deleted subscription [{}]'
                           .format(subscription_to_delete.RelativeName()))

  def testSubscriptionsDeleteNonExistent(self):
    subscription_to_delete = util.ParseSubscription(
        'not_there', self.Project()).RelativeName()

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=subscription_to_delete),
        response='',
        exception=http_error.MakeHttpError(404, 'Subscription does not exist.'))

    with self.AssertRaisesExceptionMatches(
        util.RequestsFailedError,
        'Failed to delete the following: [not_there].'):
      self.Run('pubsub subscriptions delete not_there')
    self.AssertErrContains(subscription_to_delete)
    self.AssertErrContains('Subscription does not exist.')


class SubscriptionsDeleteGATest(SubscriptionsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_subscriptions.Delete

  def testSubscriptionsDeleteNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    subscription_to_delete = util.ParseSubscription(
        'subs1', self.Project()).RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=subscription_to_delete),
        response=self.msgs.Empty())

    result = self.Run('pubsub subscriptions delete subs1')

    self.assertEqual(result[0], self.msgs.Empty())


class SubscriptionsDeleteBetaTest(SubscriptionsDeleteTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testSubscriptionsDeleteWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    subscription_to_delete = util.ParseSubscription(
        'subs1', self.Project()).RelativeName()
    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsDeleteRequest(
            subscription=subscription_to_delete),
        response='')

    result = list(self.Run('pubsub subscriptions delete subs1'))

    self.assertEqual(len(result), 1)
    self.assertEqual(result[0]['subscriptionId'], subscription_to_delete)

if __name__ == '__main__':
  test_case.main()
