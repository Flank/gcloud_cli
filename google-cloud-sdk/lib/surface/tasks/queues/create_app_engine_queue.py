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
"""`gcloud tasks queues create-app-engine-queue` command."""

from googlecloudsdk.api_lib.tasks import queues
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import log


class CreateAppEngine(base.CreateCommand):
  """Create an App Engine queue.

  An App Engine queue is a push queue sent to an App Engine endpoint. The flags
  available to this command represent the fields of an App Engine queue that are
  mutable.

  For more information about the different queue target types, see:
  https://cloud.google.com/cloud-tasks/docs/queue-types
  """

  @staticmethod
  def Args(parser):
    flags.AddIdArg(parser, 'App Engine queue', 'to create')
    flags.AddLocationFlag(parser)
    flags.AddCreateAppEngineQueueFlags(parser)

  def Run(self, args):
    queues_client = queues.Queues()
    queue_ref = parsers.ParseQueue(args.id, args.location)
    location_ref = parsers.ExtractLocationRefFromQueueRef(queue_ref)
    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        args, constants.APP_ENGINE_QUEUE, queues_client.api.messages)
    log.warning(constants.QUEUE_MANAGEMENT_WARNING)
    create_response = queues_client.Create(
        location_ref, queue_ref,
        retry_config=queue_config.retryConfig,
        rate_limits=queue_config.rateLimits,
        app_engine_http_target=queue_config.appEngineHttpTarget)
    log.CreatedResource(queue_ref.Name(), 'queue')
    return create_response
