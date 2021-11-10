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
"""`gcloud dataplex asset create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import asset
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import flags
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Creating an Asset."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Dataplex Asset, run:

            $ {command} projects/{project_id}/locations/{location}/lakes/{lake_id}/zones/{zone_id}/assets/{asset_id}
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAssetResourceArg(parser, 'to create an Asset to.')
    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    parser.add_argument('--description', help='Description of the Asset')
    parser.add_argument('--display-name', help='Display Name of the Asset')
    resource_spec = parser.add_group(
        required=True,
        help='Specification of the resource that is referenced by this asset.')
    resource_spec.add_argument(
        '--resource-name',
        help=""""Relative name of the cloud resource that contains the data that
                 is being managed within a lake. For example:
                 projects/{project_number}/buckets/{bucket_id} projects/{project_number}/datasets/{dataset_id}"""
    )
    resource_spec.add_argument(
        '--resource-type',
        required=True,
        choices={
            'STORAGE_BUCKET': 'Cloud Storage Bucket',
            'BIGQUERY_DATASET': 'BigQuery Dataset',
        },
        type=arg_utils.ChoiceToEnumName,
        help='Type')
    flags.AddDiscoveryArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    asset_ref = args.CONCEPTS.asset.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_zones_assets.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesZonesAssetsCreateRequest(
            assetId=asset_ref.Name(),
            parent=asset_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Asset=asset.GenerateAssetForCreateRequest(
                args)))
    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      asset.WaitForOperation(create_req_op)
      log.CreatedResource(
          asset_ref.Name(),
          details='Asset created in zone [{0}] in lake [{1}] in project [{2}] with location [{3}]'
          .format(asset_ref.zonesId, asset_ref.lakesId, asset_ref.projectsId,
                  asset_ref.locationsId))
      return

    log.status.Print('Creating [{0}] with operation [{1}].'.format(
        asset_ref, create_req_op.name))
