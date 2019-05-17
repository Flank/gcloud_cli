# -*- coding: utf-8 -*- #
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

"""Test of the 'pubsub subscriptions modify-push-config' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class SubscriptionsModifyPushConfigTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.ModifyPushConfig

  def testSubscriptionsModify(self):
    new_endpoint = 'https://my.appspot.com/push2'
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(pushEndpoint=new_endpoint)),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-push-config subs2'
             ' --push-endpoint https://my.appspot.com/push2')

    self.AssertErrContains(
        'Updated subscription [{}]'.format(sub_ref.RelativeName()))

  def testSubscriptionsModifyFullUri(self):
    new_endpoint = 'https://my.appspot.com/push2'
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(pushEndpoint=new_endpoint)),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-push-config {}'
             ' --push-endpoint https://my.appspot.com/push2'
             .format(sub_ref.SelfLink()))

    self.AssertErrContains('Updated subscription [{}]'.format(
        sub_ref.RelativeName()))


class SubscriptionsModifyPushConfigBetaTest(SubscriptionsModifyPushConfigTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    properties.VALUES.core.user_output_enabled.Set(True)
    self.svc = self.client.projects_subscriptions.ModifyPushConfig

  def testSubscriptionsModifyWithLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    new_endpoint = 'https://my.appspot.com/push2'
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(pushEndpoint=new_endpoint)),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-push-config subs2'
             ' --push-endpoint https://my.appspot.com/push2')

    self.AssertErrContains(
        'Updated subscription [{}]'.format(sub_ref.RelativeName()))
    self.AssertOutputEquals(
        'pushEndpoint: https://my.appspot.com/push2\n'
        'subscriptionId: {}\n'.format(sub_ref.RelativeName()))

  def testSubscriptionsModifyPushAuthServiceAccountAndAudience(self):
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(
                    pushEndpoint='https://example.com/push',
                    oidcToken=self.msgs.OidcToken(
                        serviceAccountEmail='account@example.com',
                        audience='my-audience'))),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-push-config subs2 '
             '--push-endpoint=https://example.com/push '
             '--push-auth-service-account=account@example.com '
             '--push-auth-token-audience=my-audience')

    self.AssertErrContains('Updated subscription [{}]'.format(
        sub_ref.RelativeName()))

  def testSubscriptionsModifyPushAuthServiceAccountNoAudience(self):
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(
                    pushEndpoint='https://example.com/push',
                    oidcToken=self.msgs.OidcToken(
                        serviceAccountEmail='account@example.com'))),
            subscription=sub_ref.RelativeName()),
        response='')

    self.Run('pubsub subscriptions modify-push-config subs2 '
             '--push-endpoint=https://example.com/push '
             '--push-auth-service-account=account@example.com')

    self.AssertErrContains('Updated subscription [{}]'.format(
        sub_ref.RelativeName()))


class SubscriptionsModifyPushConfigAlphaTest(
    SubscriptionsModifyPushConfigBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.svc = self.client.projects_subscriptions.ModifyPushConfig


class SubscriptionsModifyPushConfigGATest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.svc = self.client.projects_subscriptions.ModifyPushConfig

  def testSubscriptionsModifyPushConfigNoLegacyOutput(self):
    properties.VALUES.pubsub.legacy_output.Set(True)
    new_endpoint = 'https://my.appspot.com/push2'
    sub_ref = util.ParseSubscription('subs2', self.Project())

    self.svc.Expect(
        request=self.msgs.PubsubProjectsSubscriptionsModifyPushConfigRequest(
            modifyPushConfigRequest=self.msgs.ModifyPushConfigRequest(
                pushConfig=self.msgs.PushConfig(pushEndpoint=new_endpoint)),
            subscription=sub_ref.RelativeName()),
        response=self.msgs.Empty())

    result = self.Run('pubsub subscriptions modify-push-config subs2'
                      ' --push-endpoint https://my.appspot.com/push2')

    self.assertEqual(result, self.msgs.Empty())


if __name__ == '__main__':
  test_case.main()
