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
"""End-to-end tests for the `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


class QueuesTest(e2e_base.WithServiceAuth):

  def SetUp(self):
    self.retryer = retry.Retryer(max_wait_ms=60000)

  def TearDown(self):
    # There is delay between when a queue is created and when it can be deleted
    self.retryer.RetryOnException(
        self.Run, args=['alpha tasks queues delete {}'.format(self.queue_id)])
    self.AssertErrContains('Deleted queue [{}].'.format(self.queue_id))

  def testCreateQueueNoOptions(self):
    self.queue_id = next(e2e_utils.GetResourceNameGenerator('queue'))
    expected_queue = self.Run(
        'alpha tasks queues create-pull-queue {}'.format(self.queue_id))

    actual_queue = self.retryer.RetryOnException(  # Creation can take 1 minute
        self.Run, args=['alpha tasks queues describe {}'.format(self.queue_id)])

    self.assertEqual(actual_queue, expected_queue)


if __name__ == '__main__':
  test_case.main()
