# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Command to deploy an Apigee archive deployment to an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import archives as cmd_lib
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.DescribeCommand):
  """Deploy an Apigee archive deployment to an environment."""

  detailed_help = {
      "DESCRIPTION":
          """\
   {description}

  `{command}` installs an archive deployment in an Apigee environment.

  By default, the archive deployment will be deployed on the remote management
  plane for the specified Apigee organization. To deploy on a locally running
  Apigee emulator, use the `--local` flag.
  """,
      "EXAMPLES":
          """\
  To deploy the contents of the current working directory as an archive
  deployment to an environment named ``my-test'', given that the Cloud Platform
  project has been set in gcloud settings, run:

    $ {command} --environment=my-test

  To deploy an archive deployment from a local directory other than the current
  working directory, to an environment named ``my-demo'' in an organization
  belonging to a Cloud Platform project other than the one set in gcloud
  settings, named ``my-org'', run:

    $ {command} --organization=my-org --environment=my-demo --source=/apigee/dev

  """
  }

  @staticmethod
  def Args(parser):
    fallthroughs = [defaults.GCPProductOrganizationFallthrough()]
    resource_args.AddSingleResourceArgument(
        parser,
        resource_path="organization.environment",
        help_text=("Apigee environment in which to deploy the archive "
                   "deployment."),
        fallthroughs=fallthroughs,
        positional=False,
        required=True)
    parser.add_argument(
        "--source", required=False, help="The source directory to upload.")
    parser.add_argument(
        "--async",
        action="store_true",
        dest="async_",
        help=("If set, returns immediately and outputs a description of the "
              "long running operation that was launched. Else, `{command}` "
              "will block until the archive deployment has been successfully "
              "deployed to the specified environment.\n\n"
              "To monitor the operation once it's been launched, run "
              "`{grandparent_command} operations describe OPERATION_NAME`."))

  def Run(self, args):
    """Run the deploy command."""
    identifiers = args.CONCEPTS.environment.Parse().AsDict()
    # Using as a context manager automatically cleans up the temp file on exit.
    with cmd_lib.LocalDirectoryArchive(args.source) as local_dir_archive:
      zip_file_path = local_dir_archive.Zip()
      get_upload_url_resp = apigee.ArchivesClient.GetUploadUrl(identifiers)
      if "uploadUri" not in get_upload_url_resp:
        raise errors.RequestError(
            resource_type="getUploadUrl",
            resource_identifier=identifiers,
            body=get_upload_url_resp,
            user_help="Please try again.")
      upload_url = get_upload_url_resp["uploadUri"]
      # HTTP PUT request to upload the local archive to GCS.
      upload_archive_resp = cmd_lib.UploadArchive(upload_url, zip_file_path)
      if not upload_archive_resp.ok:
        raise errors.HttpRequestError(upload_archive_resp.status_code,
                                      upload_archive_resp.reason,
                                      upload_archive_resp.url,
                                      upload_archive_resp.request.method)
      # CreateArchiveDeployment starts an LRO.
      create_archive_deployment_resp = \
          apigee.ArchivesClient.CreateArchiveDeployment(identifiers, upload_url)
      operation = apigee.OperationsClient.SplitName(
          create_archive_deployment_resp)
      if "organization" not in operation or "uuid" not in operation:
        raise waiter.OperationError(
            "Unknown operation response: {}".format(operation))
      if args.async_:
        return operation
      log.info("Started archives deploy operation %s", operation["name"])
      waiter.WaitFor(
          apigee.LROPoller(operation["organization"]),
          operation["uuid"],
          message="Waiting for operation [{}] to complete".format(
              operation["uuid"]))
