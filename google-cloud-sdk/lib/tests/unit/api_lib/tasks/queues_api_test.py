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
"""Unit tests for Cloud Tasks API queues service in gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.tasks import queues as queues_api
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.api_lib.util import list_slicer
from tests.lib.surface.tasks import test_base
from six.moves import range
from six.moves import zip


class PushQueuesTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_ref = resources.REGISTRY.Parse(
        'us-central1', params={'projectsId': self.Project()},
        collection='cloudtasks.projects.locations')
    self.queue_ref = resources.REGISTRY.Parse(
        'my-queue', params={'projectsId': self.Project(),
                            'locationsId': 'us-central1'},
        collection='cloudtasks.projects.locations.queues')

    # Define separately from queue_ref because we know that this is what the API
    # expects
    self.queue_name = ('projects/{}/locations/us-central1/queues'
                       '/my-queue'.format(self.Project()))

  def testGet(self):
    expected_queue = self.messages.Queue(name=self.queue_name)
    self.queues_service.Get.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
            name=expected_queue.name),
        expected_queue)
    actual_queue = self.queues_client.Get(self.queue_ref)
    self.assertEqual(actual_queue, expected_queue)

  def _ExpectList(self, queues, limit=None, page_size=100):
    if limit:
      queues = queues[:limit]
    slices, token_pairs = list_slicer.SliceList(queues, page_size)
    for slice_, (current_token, next_token) in zip(slices, token_pairs):
      self.queues_service.List.Expect(
          self.messages.CloudtasksProjectsLocationsQueuesListRequest(
              parent=self.location_ref.RelativeName(),
              pageToken=current_token, pageSize=page_size),
          self.messages.ListQueuesResponse(queues=queues[slice_],
                                           nextPageToken=next_token))

  def testList(self):
    expected_queue_list = [
        self.messages.Queue(name='{}{}'.format(self.queue_name, i))
        for i in range(200)]
    self._ExpectList(expected_queue_list)
    actual_queue_list = list(self.queues_client.List(self.location_ref))
    self.assertEqual(actual_queue_list, expected_queue_list)

  def testList_AllOptions(self):
    expected_queue_list = [
        self.messages.Queue(name='{}{}'.format(self.queue_name, i))
        for i in range(200)]
    limit = 150
    page_size = 50
    self._ExpectList(expected_queue_list, limit=limit, page_size=page_size)
    actual_queue_list = list(self.queues_client.List(
        self.location_ref, limit=limit, page_size=page_size))
    # Verify that only `limit` items were returned
    self.assertEqual(actual_queue_list, expected_queue_list[:limit])

  def _TestQueueCreation(self, retry_config=None, rate_limits=None,
                         app_engine_http_queue=None):
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=retry_config,
        rateLimits=rate_limits,
        appEngineHttpQueue=app_engine_http_queue)
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        expected_queue)
    actual_queue = self.queues_client.Create(
        self.location_ref, self.queue_ref, retry_config=retry_config,
        rate_limits=rate_limits,
        app_engine_http_queue=app_engine_http_queue)
    self.assertEqual(actual_queue, expected_queue)

  def testCreate_NoOptions(self):
    self._TestQueueCreation()

  def testCreate_AllOptions_AppEngineQueue(self):
    retry_config = self.messages.RetryConfig(
        maxAttempts=100, maxRetryDuration='0s',
        maxDoublings=16, minBackoff='0.1s', maxBackoff='3600s')
    rate_limits = self.messages.RateLimits(
        maxConcurrentDispatches=10, maxDispatchesPerSecond=1, maxBurstSize=10)
    app_engine_http_queue = self.messages.AppEngineHttpQueue(
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'))
    self._TestQueueCreation(retry_config=retry_config,
                            rate_limits=rate_limits,
                            app_engine_http_queue=app_engine_http_queue)

  def _TestQueueUpdate(self, retry_config=None, rate_limits=None,
                       app_engine_routing_override=None, update_mask=''):
    app_engine_http_queue = None
    if app_engine_routing_override is not None:
      app_engine_http_queue = self.messages.AppEngineHttpQueue(
          appEngineRoutingOverride=app_engine_routing_override)
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=retry_config,
        rateLimits=rate_limits, appEngineHttpQueue=app_engine_http_queue)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue, updateMask=update_mask),
        expected_queue)
    actual_queue = self.queues_client.Patch(
        self.queue_ref, retry_config=retry_config, rate_limits=rate_limits,
        app_engine_routing_override=app_engine_routing_override)
    self.assertEqual(actual_queue, expected_queue)

  def testPatch_NoOptions(self):
    with self.assertRaises(queues_api.NoFieldsSpecifiedError):
      self.queues_client.Patch(self.queue_ref)

  def testPatch_SomeOptions(self):
    rate_limits = self.messages.RateLimits(
        maxConcurrentDispatches=10, maxDispatchesPerSecond=1, maxBurstSize=10)
    self._TestQueueUpdate(rate_limits=rate_limits, update_mask='rateLimits')

  def testPatch_AllOptions_AppEngineQueue(self):
    retry_config = self.messages.RetryConfig(
        maxAttempts=100, maxRetryDuration='0s',
        maxDoublings=16, minBackoff='0.1s', maxBackoff='3600s')
    rate_limits = self.messages.RateLimits(
        maxConcurrentDispatches=10, maxDispatchesPerSecond=1, maxBurstSize=10)
    app_engine_routing_override = self.messages.AppEngineRouting(service='abc')
    self._TestQueueUpdate(
        retry_config=retry_config, rate_limits=rate_limits,
        app_engine_routing_override=app_engine_routing_override,
        update_mask=('retryConfig,rateLimits,'
                     'appEngineHttpQueue.appEngineRoutingOverride'))

  def testDelete(self):
    expected_queue = self.messages.Queue(name=self.queue_name)
    self.queues_service.Delete.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesDeleteRequest(
            name=expected_queue.name),
        self.messages.Empty())
    actual_queue = self.queues_client.Delete(self.queue_ref)
    self.assertEqual(actual_queue, self.messages.Empty())

  def testPurge(self):
    expected_queue = self.messages.Queue(name=self.queue_name)
    self.queues_service.Purge.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPurgeRequest(
            name=expected_queue.name),
        expected_queue)
    actual_queue = self.queues_client.Purge(self.queue_ref)
    self.assertEqual(actual_queue, expected_queue)

  def testPause(self):
    expected_queue = self.messages.Queue(name=self.queue_name)
    self.queues_service.Pause.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPauseRequest(
            name=expected_queue.name),
        expected_queue)
    actual_queue = self.queues_client.Pause(self.queue_ref)
    self.assertEqual(actual_queue, expected_queue)

  def testResume(self):
    expected_queue = self.messages.Queue(name=self.queue_name)
    self.queues_service.Resume.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesResumeRequest(
            name=expected_queue.name),
        expected_queue)
    actual_queue = self.queues_client.Resume(self.queue_ref)
    self.assertEqual(actual_queue, expected_queue)

  def testGetIamPolicy(self):
    expected_policy = self.messages.Policy()
    expected_request = (
        self.messages.CloudtasksProjectsLocationsQueuesGetIamPolicyRequest(
            resource=self.queue_ref.RelativeName()))
    self.queues_service.GetIamPolicy.Expect(expected_request, expected_policy)
    actual_policy = self.queues_client.GetIamPolicy(self.queue_ref)
    self.assertEqual(actual_policy, expected_policy)

  def testSetIamPolicy(self):
    expected_policy = self.messages.Policy()
    expected_request = (
        self.messages.CloudtasksProjectsLocationsQueuesSetIamPolicyRequest(
            resource=self.queue_ref.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=expected_policy)))
    self.queues_service.SetIamPolicy.Expect(expected_request, expected_policy)
    actual_policy = self.queues_client.SetIamPolicy(self.queue_ref,
                                                    expected_policy)
    self.assertEqual(actual_policy, expected_policy)


class PullQueuesTest(test_base.CloudTasksAlphaTestBase):

  def SetUp(self):
    self.location_ref = resources.REGISTRY.Parse(
        'us-central1', params={'projectsId': self.Project()},
        collection='cloudtasks.projects.locations')
    self.queue_ref = resources.REGISTRY.Parse(
        'my-queue', params={'projectsId': self.Project(),
                            'locationsId': 'us-central1'},
        collection='cloudtasks.projects.locations.queues')

    # Define separately from queue_ref because we know that this is what the API
    # expects
    self.queue_name = ('projects/{}/locations/us-central1/queues'
                       '/my-queue'.format(self.Project()))

  def _TestQueueCreation(self, retry_config=None, rate_limits=None,
                         pull_target=None, app_engine_http_target=None):
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=retry_config,
        rateLimits=rate_limits, pullTarget=pull_target,
        appEngineHttpTarget=app_engine_http_target)
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        expected_queue)
    actual_queue = self.queues_client.Create(
        self.location_ref, self.queue_ref, retry_config=retry_config,
        rate_limits=rate_limits, pull_target=pull_target,
        app_engine_http_target=app_engine_http_target)
    self.assertEqual(actual_queue, expected_queue)

  def testCreate_AllOptions_PullQueue(self):
    retry_config = self.messages.RetryConfig(
        maxAttempts=100, unlimitedAttempts=False, maxRetryDuration='0s',
        maxDoublings=0, minBackoff='0s', maxBackoff='0s')
    pull_target = self.messages.PullTarget()
    self._TestQueueCreation(retry_config=retry_config,
                            pull_target=pull_target)

  def testCreate_AttemptPullandAppEngineQueue(self):
    retry_config = self.messages.RetryConfig(
        maxAttempts=100, unlimitedAttempts=False, maxRetryDuration='0s',
        maxDoublings=16, minBackoff='0.1s', maxBackoff='3600s')
    rate_limits = self.messages.RateLimits(
        maxConcurrentTasks=10, maxTasksDispatchedPerSecond=1, maxBurstSize=10)
    pull_target = self.messages.PullTarget()
    app_engine_http_target = self.messages.AppEngineHttpTarget(
        appEngineRoutingOverride=self.messages.AppEngineRouting(service='abc'))

    with self.assertRaises(queues_api.CreatingPullAndAppEngineQueueError):
      self.queues_client.Create(
          self.location_ref,
          self.queue_ref,
          retry_config=retry_config,
          rate_limits=rate_limits,
          pull_target=pull_target,
          app_engine_http_target=app_engine_http_target)

  def _TestQueueUpdate(self, retry_config=None, rate_limits=None,
                       app_engine_routing_override=None, update_mask=''):
    app_engine_http_target = None
    if app_engine_routing_override is not None:
      app_engine_http_target = self.messages.AppEngineHttpTarget(
          appEngineRoutingOverride=app_engine_routing_override)
    expected_queue = self.messages.Queue(
        name=self.queue_name, retryConfig=retry_config,
        rateLimits=rate_limits, appEngineHttpTarget=app_engine_http_target)
    self.queues_service.Patch.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
            name=self.queue_name, queue=expected_queue, updateMask=update_mask),
        expected_queue)
    actual_queue = self.queues_client.Patch(
        self.queue_ref, retry_config=retry_config, rate_limits=rate_limits,
        app_engine_routing_override=app_engine_routing_override)
    self.assertEqual(actual_queue, expected_queue)

  def testPatch_AllOptions_PullQueue(self):
    retry_config = self.messages.RetryConfig(
        maxAttempts=100, unlimitedAttempts=False, maxRetryDuration='0s',
        maxDoublings=0, minBackoff='0s', maxBackoff='0s')
    self._TestQueueUpdate(retry_config=retry_config, update_mask='retryConfig')


if __name__ == '__main__':
  test_case.main()
