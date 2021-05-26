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
"""Implementation of rm command for deleting resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import multiprocessing

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task_iterator_factory
from googlecloudsdk.core import log


class Rm(base.Command):
  """Deletes Cloud Storage objects and buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      The rm command deletes objects and buckets.
      """,
      'EXAMPLES':
          """

      Delete a Google Cloud Storage object named "my-object":

        $ *{command}* rm gs://my-bucket/my-object

      Delete all objects of cloud directory "my-dir" but not subdirectories:

        $ *{command}* rm gs://my-bucket/my-dir/*

      Delete all objects and subdirectories of cloud directory "my-dir":

        $ *{command}* rm gs://my-bucket/my-dir/**

      Delete all versions of all objects and subdirectories of cloud directory
      "my-dir":

        $ *{command}* rm -r gs://my-bucket/my-dir/

      Delete all versions of all resources in "my-bucket" and then delete the
      bucket.

        $ *{command}* rm -r gs://my-bucket/

      Delete live version of all resources in "my-bucket" without deleting
      the bucket.

        $ *{command}* rm gs://my-bucket/**

      Delete all text files in "my-bucket":

        $ *{command}* rm -r gs://my-bucket/*.txt

      Delete one wildcard expression per line passed in by stdin:

        $ some_program | *{command}* rm -I
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls',
        nargs='*',
        help='Specifies the URLs of the resources to delete.')
    parser.add_argument(
        '--stdin',
        '-I',
        action='store_true',
        help='Reads the list of resources to remove from stdin.')
    parser.add_argument(
        '--recursive',
        '-R',
        '-r',
        action='store_true',
        help=('Deletes bucket or directory contents to be removed'
              ' recursively. Will delete matching bucket URLs (like'
              ' gs://bucket) after deleting objects and directories. This'
              ' option implies the -a option. If you want to delete only live'
              ' object versions, use the \'**\' wildcard instead.'))
    parser.add_argument(
        '--all-versions',
        '-a',
        action='store_true',
        help='Deletes all versions of an object.')

  def Run(self, args):
    if args.stdin:
      if args.urls:
        raise errors.Error(
            'No URL arguments allowed when reading URLs from stdin.')
      urls = stdin_iterator.StdinIterator()
    else:
      if not args.urls:
        raise errors.Error(
            'Without the --stdin flag, the rm command requires at least one URL'
            ' argument.')
      urls = args.urls

    name_expansion_iterator = name_expansion.NameExpansionIterator(
        urls,
        all_versions=args.all_versions or args.recursive,
        include_buckets=args.recursive,
        recursion_requested=args.recursive)

    task_status_queue = multiprocessing.Queue()

    task_iterator_factory = (
        delete_task_iterator_factory.DeleteTaskIteratorFactory(
            name_expansion_iterator,
            task_status_queue=task_status_queue))

    log.status.Print('Removing objects:')
    task_executor.execute_tasks(
        task_iterator_factory.object_iterator(),
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_type=task_status.ProgressType.COUNT)

    bucket_iterator = plurality_checkable_iterator.PluralityCheckableIterator(
        task_iterator_factory.bucket_iterator())

    # We perform the is_empty check to avoid printing unneccesary status lines.
    if args.recursive and not bucket_iterator.is_empty():
      log.status.Print('Removing Buckets:')
      task_executor.execute_tasks(
          bucket_iterator,
          parallelizable=True,
          task_status_queue=task_status_queue,
          progress_type=task_status.ProgressType.COUNT)
