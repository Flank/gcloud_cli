# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex lake update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import lake
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Updating a lake."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Dataplex Lake, run:

            $ {command} update projects/{project_id}/locations/{location}/lakes/{lake_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddLakeResourceArg(parser, 'to updating a Lake to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the update action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Lake')
    parser.add_argument('--display-name', help='Display Name')
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    update_mask = []
    if args.IsSpecified('description'):
      update_mask.append('description')
    if args.IsSpecified('display_name'):
      update_mask.append('displayName')
    if args.IsSpecified('labels'):
      update_mask.append('labels')
    lake_ref = args.CONCEPTS.lake.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    update_req_op = dataplex_client.projects_locations_lakes.Patch(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesPatchRequest(
            name=lake_ref.RelativeName(),
            validateOnly=args.validate_only,
            updateMask=u','.join(update_mask),
            googleCloudDataplexV1Lake=dataplex_util.GetMessageModule()
            .GoogleCloudDataplexV1Lake(
                description=args.description,
                displayName=args.display_name,
                labels=args.labels)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete with errors:')
      return update_req_op

    async_ = getattr(args, 'async_', False)
    if not async_:
      return lake.WaitForOperation(update_req_op)
    return update_req_op
