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
"""'logging operations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_projector


class List(base.ListCommand):
  """List long running operations.

  Return a list of long running operation details in given LOCATION. The
  operations were scheduled by other gcloud commands. For example: a
  copy_log_entries operation scheduled by command: gcloud alpha logging
  operations copy BUCKET_ID DESTINATION --location = LOCATION.

  ## EXAMPLES

  To list operations, run:

    $ {command} --location=LOCATION
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--location', required=True, help='Location of the operations.')
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat(
        'table(name, done, source, '
        'destination, filter, createTime, endTime, state)'
    )

    util.AddParentArgs(parser, 'List operations')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A list of operations.
    """
    operation_name = util.CreateResourceName(
        util.GetParentFromArgs(args), 'locations', args.location)

    request = util.GetMessages().LoggingProjectsLocationsOperationsListRequest(
        name=operation_name, filter=args.filter, pageSize=args.page_size)

    result = util.GetClient().projects_locations_operations.List(request)
    operations = resource_projector.MakeSerializable(result.operations)

    for operation in operations:
      yield self.GetOperationData(operation)

  def GetOperationData(self, operation):
    """Get one operation details.

    Args:
      operation: a serialized operation infomation.

    Returns:
      Operation details for printing.
    """
    metadata = operation.get('metadata', {})
    request = metadata.get('request', {})
    return {
        'name': operation.get('name', '/').split('/')[-1],
        'done': operation.get('done', ''),
        'source': request.get('name', ''),
        'destination': request.get('destination', ''),
        'filter': request.get('filter', '(empty filter)'),
        'createTime': metadata.get('createTime', ''),
        'endTime': metadata.get('endTime', ''),
        'state': metadata.get('state', '')
    }
