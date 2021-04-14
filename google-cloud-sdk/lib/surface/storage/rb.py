# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of rb command for deleting buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.rb import delete_bucket_task_iterator


class Rb(base.Command):
  """Deletes Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      The rb command deletes a bucket.
      """,
      'EXAMPLES':
          """

      Delete a Google Cloud Storage bucket named "my-bucket":

        $ *{command}* rb gs://my-bucket

      Delete two buckets:

        $ *{command}* rb gs://my-bucket gs://my-other-bucket

      Delete all buckets beginning with "my" and continue on errors:

        $ *{command}* rb --force gs://my*
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls', nargs='+', help='Specifies the URLs of the buckets to delete.')

  def Run(self, args):
    bucket_wildcard_iterators = []
    for url_string in args.urls:
      url_object = storage_url.storage_url_from_string(url_string)
      if not url_object.is_bucket():
        raise errors.InvalidUrlError(
            'rb only accepts cloud bucket URLs. Example: "gs://bucket"')

      bucket_wildcard_iterators.append(
          wildcard_iterator.CloudWildcardIterator(url_object))

    with task_status.ProgressManager(
        task_status.ProgressType.COUNT) as progress_manager:
      tasks_iterator = plurality_checkable_iterator.PluralityCheckableIterator(
          delete_bucket_task_iterator.DeleteBucketTaskIterator(
              bucket_wildcard_iterators,
              task_status_queue=progress_manager.task_status_queue))

      if tasks_iterator.is_empty():
        raise errors.InvalidUrlError('Wildcard query matched no buckets.')

      task_executor.ExecuteTasks(
          tasks_iterator,
          is_parallel=True,
          task_status_queue=progress_manager.task_status_queue)
