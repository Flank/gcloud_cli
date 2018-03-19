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
"""ml-engine versions update command."""
from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import versions_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _AddUpdateArgs(parser):
  """Get arguments for the `ml-engine versions update` command."""
  flags.AddVersionResourceArg(parser, 'to update')
  flags.GetDescriptionFlag('version').AddToParser(parser)
  labels_util.AddUpdateLabelsFlags(parser)


class Update(base.UpdateCommand):
  """Update a Cloud ML Engine model."""

  @staticmethod
  def Args(parser):
    _AddUpdateArgs(parser)

  def Run(self, args):
    versions_client = versions_api.VersionsClient()
    operations_client = operations.OperationsClient()
    version_ref = args.CONCEPTS.version.Parse()
    versions_util.Update(versions_client, operations_client, version_ref, args)
    log.UpdatedResource(args.model, kind='ml engine model')
