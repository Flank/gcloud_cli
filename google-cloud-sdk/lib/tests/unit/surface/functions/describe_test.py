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

"""Tests of the 'describe' command."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.functions import base


class FunctionsGetTest(base.FunctionsTestBase,
                       parameterized.TestCase):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')

  def assertGettingFunction(self, test_function):
    test_name = 'projects/{0}/locations/us-central1/functions/my-test'.format(
        self.Project())
    self.mock_client.projects_locations_functions.Get.Expect(
        self.messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=test_name),
        test_function)
    properties.VALUES.core.user_output_enabled.Set(False)
    result = self.Run('functions describe my-test')
    self.assertEqual(test_function, result)

  def testGetTriggerlessFunction(self):
    self.assertGettingFunction(self.messages.CloudFunction(
        name='my-test', sourceArchiveUrl='my-url',))

  def testGetHttpTriggeredFunction(self):
    self.assertGettingFunction(self.messages.CloudFunction(
        name='my-test',
        sourceArchiveUrl='my-url',
        httpsTrigger=self.messages.HttpsTrigger()))

  @parameterized.named_parameters(
      ('CloudStorage',
       'cloud.storage', 'object.change', 'projects/_/buckets/pail'),
      ('GoogleStorage',
       'google.storage', 'object.change', 'projects/_/buckets/pail'),
      ('CloudPubSub',
       'cloud.pubsub', 'object.change', 'projects/_/buckets/attester'),
      ('GooglePubSub',
       'google.pubsub', 'object.change', 'projects/_/buckets/benefactor'),
      ('FirestoreCreateEvent',
       'cloud.firestore', 'document.create', 'foobar'),
      ('FirestoreDeleteDocument',
       'cloud.firestore', 'document.delete', 'foobar'),
      ('FirestoreUpdateDocument',
       'cloud.firestore', 'document.update', 'foobar'),
      ('FirestoreWriteDocuemnt',
       'cloud.firestore', 'document.write', 'foobar'),
      ('FirebaseCreateUser',
       'firebase.auth', 'user.create', 'foobar'),
      ('FirebaseDeleteUser',
       'firebase.auth', 'user.delete', 'foobar'),
      ('FirebaseNewIssue',
       'firebase.crashlytics', 'issue.new', 'foobar'),
      ('FirebaseRegressedIssue',
       'firebase.crashlytics', 'issue.regressed', 'foobar'),
      ('FirebaseIssueVelocityAlert',
       'firebase.crashlytics', 'issue.velocityAlert', 'foobar'),
      ('FirebaseCreateRef',
       'google.firebase.database', 'ref.create', 'foobar'),
      ('FirebaseDeleteRef',
       'google.firebase.database', 'ref.delete', 'foobar'),
      ('FirebaseUpdateRef',
       'google.firebase.database', 'ref.update', 'foobar'),
      ('FirebaseWriteRef',
       'google.firebase.database', 'ref.write', 'foobar'),
      ('FirebaseLogEvent',
       'google.firebase.analytics', 'event.log', 'foobar'),
  )
  def testGetEventTriggeredFunctionV1Beta1Format(
      self, provider, event_type, resource):
    self.assertGettingFunction(self.messages.CloudFunction(
        name='my-test',
        sourceArchiveUrl='my-url',
        eventTrigger=self.messages.EventTrigger(
            eventType='providers/{}/eventTypes/{}'.format(provider, event_type),
            resource=resource,
        )))

  @parameterized.named_parameters(
      ('PublishTopic', 'google.pubsub.topic.publish'),
      ('ArchiveBucket', 'google.storage.bucket.archive'),
      ('DeleteBucket', 'google.storage.bucket.delete'),
      ('FinalizeBucket', 'google.storage.bucket.finalize'),
      ('UpdateBucketMeta', 'google.storage.bucket.metadata_update'),
  )
  def testGetEventTriggeredFunctionV1Beta2Format(self, event_type):
    self.assertGettingFunction(self.messages.CloudFunction(
        name='my-test',
        sourceArchiveUrl='my-url',
        eventTrigger=self.messages.EventTrigger(
            eventType=event_type,
        )))

  def testGetNoAuth(self):
    # Remove credentials.
    self.FakeAuthSetCredentialsPresent(False)
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_AUTH_REGEXP):
      self.Run('functions describe my-test')


class FunctionsGetWithoutProjectTest(base.FunctionsTestBase):

  def Project(self):
    return None

  def testGetNoProject(self):
    # We don't care what type of exception is raised here.
    with self.assertRaisesRegexp(Exception, base.NO_PROJECT_REGEXP):
      self.Run('functions describe my-test')

if __name__ == '__main__':
  test_case.main()
