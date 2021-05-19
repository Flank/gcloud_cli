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
"""Command to create transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.transfer import creds_util
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties

_SOURCE_HELP_TEXT = (
    'The source of your data, typically specified by a scheme to show source'
    ' (e.g., gs:// for a Google Cloud Storage bucket);'
    ' name of the resource (e.g., bucket or container name);'
    ' and, if transferring from a folder, the path to the folder.'
    ' Example formatting:\n\n'
    'Public clouds:\n'
    '- Google Cloud Storage - gs://example-bucket/example-folder\n'
    '- Amazon S3 - s3://examplebucket/example-folder\n'
    '- Azure Storage - http://examplestorageaccount.blob.core.windows.net/'
    'examplecontainer/examplefolder\n\n'
    'Publicly-accessible objects:\n'
    '- URL list of objects - http://example.com/tsvfile')


class Create(base.Command):
  """Create a Transfer Service transfer job."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Creates a Transfer Service transfer job, allowing you to transfer data to
      Google Cloud Storage on a one-time or recurring basis.
      """,
      'EXAMPLES':
          """\
      To create a one-time, immediate transfer job to move data from Google
      Cloud Storage bucket "foo" into the "baz" folder in Cloud Storage bucket
      "bar", run:

        $ {command} gs://foo gs://bar/baz/
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('source', help=_SOURCE_HELP_TEXT)
    parser.add_argument(
        'destination',
        help='The destination for your data in Google Cloud Storage, specified'
        ' by bucket name and, if transferring to a folder, any subsequent'
        ' path to the folder. E.g., gs://example-bucket/example-folder')
    parser.add_argument(
        '--name',
        help='A unique identifier for the job. Referring to your source and'
        ' destination is recommended. If left blank, the name is'
        ' auto-generated upon submission of the job.')
    parser.add_argument(
        '--description',
        help='An optional description to help identify the job using details'
        " that don't fit in its name.")
    parser.add_argument(
        '--source-creds-file',
        help='Path to local file that'
        ' includes relevant AWS or Azure credentials. Required only for jobs'
        ' with Amazon S3 buckets and Azure Storage containers as sources.'
        ' If not specified for an AWS transfer, will check default config '
        ' paths. For credential file formatting information, see:'
        ' http://cloud/storage-transfer/docs/reference/rest/v1/TransferSpec')
    parser.add_argument(
        '--no-async',
        action='store_true',
        help='For jobs set to run upon creation, this flag blocks other tasks'
        " in your terminal until the job's initial, immediate transfer"
        ' operation has completed. If not included, tasks will run'
        ' asynchronously.')
    parser.add_argument(
        '--do-not-run',
        action='store_true',
        help='Disables default behavior of running job upon creation when no'
        " schedule is set. If specified, job won't run until an operation is"
        ' manually started or a schedule is added.')

  def Run(self, args):
    client = apis.GetClientInstance('storagetransfer', 'v1')
    messages = apis.GetMessagesModule('storagetransfer', 'v1')

    destination_url = storage_url.storage_url_from_string(args.destination)
    transfer_spec = messages.TransferSpec(
        gcsDataSink=messages.GcsData(
            bucketName=destination_url.bucket_name,
            path=destination_url.object_name,
        ))

    try:
      source_url = storage_url.storage_url_from_string(args.source)
    except errors.InvalidUrlError:
      if args.source.startswith(storage_url.ProviderPrefix.HTTP.value):
        transfer_spec.httpDataSource = messages.HttpData(listUrl=args.source)
        source_url = None
      else:
        raise

    if source_url:
      if source_url.scheme is storage_url.ProviderPrefix.GCS:
        transfer_spec.gcsDataSource = messages.GcsData(
            bucketName=source_url.bucket_name,
            path=source_url.object_name,
        )
      elif source_url.scheme is storage_url.ProviderPrefix.S3:
        if args.source_creds_file:
          creds_dict = creds_util.get_values_for_keys_from_file(
              args.source_creds_file,
              ['aws_access_key_id', 'aws_secret_access_key'])
        else:
          creds_dict = creds_util.get_aws_creds()
        transfer_spec.awsS3DataSource = messages.AwsS3Data(
            awsAccessKey=messages.AwsAccessKey(
                accessKeyId=creds_dict.get('aws_access_key_id', None),
                secretAccessKey=creds_dict.get('aws_secret_access_key', None)),
            bucketName=source_url.bucket_name,
            path=source_url.object_name,
        )
      elif isinstance(source_url, storage_url.AzureUrl):
        if args.source_creds_file:
          sas_token = creds_util.get_values_for_keys_from_file(
              args.source_creds_file, ['sasToken'])['sasToken']
        else:
          sas_token = None
        transfer_spec.azureBlobStorageDataSource = (
            messages.AzureBlobStorageData(
                azureCredentials=messages.AzureCredentials(sasToken=sas_token),
                container=source_url.bucket_name,
                path=source_url.object_name,
                storageAccount=source_url.account,
            ))

    if args.name:
      formatted_job_name = name_util.add_job_prefix(args.name)
    else:
      formatted_job_name = None

    if args.do_not_run:
      schedule = schedule = messages.Schedule()
    else:
      today_date = datetime.date.today()
      today_message = messages.Date(
          day=today_date.day, month=today_date.month, year=today_date.year)
      # TODO(b/187409634): Allow user to set this.
      schedule = messages.Schedule(
          scheduleStartDate=today_message,
          scheduleEndDate=today_message,
      )

    result = client.transferJobs.Create(
        messages.TransferJob(
            description=args.description,
            name=formatted_job_name,
            projectId=properties.VALUES.core.project.Get(),
            schedule=schedule,
            status=messages.TransferJob.StatusValueValuesEnum.ENABLED,
            transferSpec=transfer_spec))

    if args.no_async:
      operations_util.block_until_done(job_name=result.name)

    return result
