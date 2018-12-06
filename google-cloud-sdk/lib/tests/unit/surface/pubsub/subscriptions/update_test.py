# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Test of the 'pubsub subscriptions update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.pubsub import base


class SubscriptionsUpdateTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.svc = self.client.projects_subscriptions.Patch
    properties.VALUES.core.user_output_enabled.Set(True)

  def testUpdateNone(self):
    with self.assertRaises(subscriptions.NoFieldsSpecifiedError):
      self.Run('pubsub subscriptions update sub')

  def testUpdateAll(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=100,
        pushConfig=self.msgs.PushConfig(
            pushEndpoint='https://my.appspot.com/push'),
        retainAckedMessages=True,
        messageRetentionDuration='259200s')

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub,
            updateMask=('ackDeadlineSeconds,pushConfig,retainAckedMessages,'
                        'messageRetentionDuration')),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run(
        'pubsub subscriptions update sub --ack-deadline 100'
        ' --push-endpoint https://my.appspot.com/push'
        ' --retain-acked-messages --message-retention-duration 3d')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def _RunLabelsTest(self, old_labels, new_labels, command):
    sub_ref = util.ParseSubscription('sub', self.Project())
    old_labels_properties = []
    for key, value in old_labels:
      old_labels_properties.append(
          self.msgs.Subscription.LabelsValue.AdditionalProperty(
              key=key, value=value))
    new_labels_properties = []
    if new_labels is not None:
      for key, value in new_labels:
        new_labels_properties.append(
            self.msgs.Subscription.LabelsValue.AdditionalProperty(
                key=key, value=value))
    old_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=50,
        pushConfig=self.msgs.PushConfig(
            pushEndpoint='https://my.appspot.com/old-push'),
        retainAckedMessages=False,
        labels=self.msgs.Subscription.LabelsValue(
            additionalProperties=old_labels_properties),
        messageRetentionDuration='0s')
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        labels=self.msgs.Subscription.LabelsValue(
            additionalProperties=new_labels_properties))

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub,
            updateMask=('labels')),
        name=sub_ref.RelativeName())
    self.client.projects_subscriptions.Get.Expect(
        self.msgs.PubsubProjectsSubscriptionsGetRequest(
            subscription=sub_ref.RelativeName()),
        old_sub)
    if new_labels is not None:
      self.svc.Expect(request=update_req,
                      response=self.msgs.Subscription())  # Ignore
      self.Run('pubsub subscriptions update sub ' + command)
      self.AssertErrEquals('Updated subscription [{0}].\n'
                           .format(sub_ref.RelativeName()))
    else:
      self.Run('pubsub subscriptions update sub ' + command)
      self.AssertErrEquals('No update to perform.\n')

  def testUpdateRemoveLabels(self):
    # Removing non-existent label 'baz' should be ignored
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [('bar', 'value2')],
        '--remove-labels foo,baz')

  def testUpdateClearLabels(self):
    # Removing non-existent label 'baz' should be ignored
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [],
        '--clear-labels')

  def testUpdateLabelsNoOp(self):
    # No update should happen
    self._RunLabelsTest(
        [('foo', 'value1')],
        None,
        '--update-labels foo=value1')

  def testUpdateUpdateLabels(self):
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [('baz', 'newvalue3'), ('foo', 'newvalue1')],
        '--remove-labels bar '
        '--update-labels foo=newvalue1,baz=newvalue3')

  def testUpdateUpdateRemoveLabels(self):
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [('bar', 'value2'), ('baz', 'newvalue3'), ('foo', 'newvalue1')],
        '--update-labels foo=newvalue1,baz=newvalue3')

  def testUpdateAllFullUri(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        ackDeadlineSeconds=100,
        pushConfig=self.msgs.PushConfig(
            pushEndpoint='https://my.appspot.com/push'),
        retainAckedMessages=True,
        messageRetentionDuration='259200s')

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub,
            updateMask=('ackDeadlineSeconds,pushConfig,retainAckedMessages,'
                        'messageRetentionDuration')),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run(
        'pubsub subscriptions update {} --ack-deadline 100'
        ' --push-endpoint https://my.appspot.com/push'
        ' --retain-acked-messages --message-retention-duration 3d'
        .format(sub_ref.SelfLink()))
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def testUnsetPushEndpoint(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        pushConfig=self.msgs.PushConfig(pushEndpoint=''))

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='pushConfig'),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run('pubsub subscriptions update sub --push-endpoint ""')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def testUnsetMessageRetention(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(), retainAckedMessages=False)

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='retainAckedMessages'),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run('pubsub subscriptions update sub --no-retain-acked-messages')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def testDefaultMessageRetentionDuration(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(name=sub_ref.RelativeName(),
                                     messageRetentionDuration=None)

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='messageRetentionDuration'),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run('pubsub subscriptions update sub'
             '     --message-retention-duration default')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def testUpdateWithNonExistentSubscription(self):
    sub_ref = util.ParseSubscription('non-existent', self.Project())
    new_sub = self.msgs.Subscription(name=sub_ref.RelativeName(),
                                     ackDeadlineSeconds=100)

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='ackDeadlineSeconds'),
        name=sub_ref.RelativeName())
    self.svc.Expect(
        request=update_req,
        response=None,
        exception=http_error.MakeHttpError(404, 'Subscription does not exist.'))

    with self.AssertRaisesHttpExceptionMatches(r'Subscription does not exist.'):
      self.Run('pubsub subscriptions update non-existent'
               '    --ack-deadline 100')

  def testUpdateNoExpiration(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        expirationPolicy=self.msgs.ExpirationPolicy())

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='expirationPolicy'),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run('pubsub subscriptions update sub --expiration-period never')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))

  def testUpdateExpirationPeriod(self):
    sub_ref = util.ParseSubscription('sub', self.Project())
    new_sub = self.msgs.Subscription(
        name=sub_ref.RelativeName(),
        expirationPolicy=self.msgs.ExpirationPolicy(ttl='172800s'))

    update_req = self.msgs.PubsubProjectsSubscriptionsPatchRequest(
        updateSubscriptionRequest=self.msgs.UpdateSubscriptionRequest(
            subscription=new_sub, updateMask='expirationPolicy'),
        name=sub_ref.RelativeName())
    self.svc.Expect(request=update_req,
                    response=self.msgs.Subscription())  # Ignore
    self.Run('pubsub subscriptions update sub --expiration-period 2d')
    self.AssertErrEquals('Updated subscription [{0}].\n'
                         .format(sub_ref.RelativeName()))
if __name__ == '__main__':
  test_case.main()
