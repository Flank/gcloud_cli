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

"""Test of the 'pubsub topics update' command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.pubsub import base


class TopicsUpdateTest(base.CloudPubsubTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.svc = self.client.projects_topics.Patch
    properties.VALUES.core.user_output_enabled.Set(True)

  def _RunLabelsTest(self, old_labels, new_labels, command):
    topic_ref = util.ParseTopic('topic', self.Project())
    old_labels_properties = []
    for key, value in old_labels:
      old_labels_properties.append(
          self.msgs.Topic.LabelsValue.AdditionalProperty(
              key=key, value=value))
    new_labels_properties = []
    if new_labels is not None:
      for key, value in new_labels:
        new_labels_properties.append(
            self.msgs.Topic.LabelsValue.AdditionalProperty(
                key=key, value=value))
    old_topic = self.msgs.Topic(
        name=topic_ref.RelativeName(),
        labels=self.msgs.Topic.LabelsValue(
            additionalProperties=old_labels_properties))
    new_topic = self.msgs.Topic(
        name=topic_ref.RelativeName(),
        labels=self.msgs.Topic.LabelsValue(
            additionalProperties=new_labels_properties))

    update_req = self.msgs.PubsubProjectsTopicsPatchRequest(
        updateTopicRequest=self.msgs.UpdateTopicRequest(
            topic=new_topic,
            updateMask=('labels')),
        name=topic_ref.RelativeName())
    self.client.projects_topics.Get.Expect(
        self.msgs.PubsubProjectsTopicsGetRequest(
            topic=topic_ref.RelativeName()),
        old_topic)
    if new_labels is not None:
      self.svc.Expect(request=update_req,
                      response=self.msgs.Topic())  # Ignore
      self.Run('pubsub topics update topic ' + command)
      self.AssertErrEquals('Updated topic [{0}].\n'
                           .format(topic_ref.RelativeName()))
    else:
      self.Run('pubsub topics update topic ' + command)
      self.AssertErrEquals('No update to perform.\n')

  def testUpdateNoUpdatesRequested(self):
    with self.assertRaises(topics.NoFieldsSpecifiedError):
      self.Run('pubsub topics update topic')

  def testUpdateNoOp(self):
    self._RunLabelsTest(
        [('foo', 'value1')],
        None,
        '--update-labels foo=value1')

  def testUpdateRemoveLabels(self):
    # Removing non-existent label 'baz' should be ignored
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [('bar', 'value2')],
        '--remove-labels foo,baz')

  def testUpdateClearLabels(self):
    self._RunLabelsTest(
        [('foo', 'value1'), ('bar', 'value2')],
        [],
        '--clear-labels')

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

  def testUpdateNoFieldsSpecified(self):
    with self.assertRaises(topics.NoFieldsSpecifiedError):
      self.Run('pubsub topics update non-existent')


if __name__ == '__main__':
  test_case.main()
