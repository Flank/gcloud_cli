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
"""Rollback a Cloud Deploy target to a prior rollout."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import promote_util
from googlecloudsdk.command_lib.deploy import release_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
  To rollback a target 'prod' for delivery pipeline 'test-pipeline' in region 'us-central1', run:

  $ {command} prod --delivery-pipeline=test-pipeline --region=us-central1


""",
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Rollback(base.CreateCommand):
  """Rollbacks a target to a prior rollout.

  If release is not specified, the command rollbacks the target with the last
  successful deployed release. If optional rollout-id parameter is not
  specified, a generated rollout ID will be used.

  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddTargetResourceArg(parser, positional=True)
    flags.AddRelease(parser, 'Name of the release to rollback to.')
    flags.AddRolloutID(parser)
    flags.AddDeliveryPipeline(parser)

  def Run(self, args):
    target_ref = args.CONCEPTS.target.Parse()
    # Check if target exists
    target_util.GetTarget(target_ref)

    release_ref = _GetRollbackRelease(args.release, args.delivery_pipeline,
                                      target_ref)
    try:
      release_obj = release.ReleaseClient().Get(release_ref.RelativeName())
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

    prompt = 'Rolling back target {} to release {}.\n\n'.format(
        target_ref.Name(), release_ref.Name())
    release_util.PrintDiff(release_ref, release_obj, target_ref.Name(), prompt)

    console_io.PromptContinue(cancel_on_no=True)

    promote_util.Promote(release_ref, release_obj, target_ref.Name(),
                         args.rollout_id)


def _GetRollbackRelease(release_id, pipeline_id, target_ref):
  """Gets the release that will be used by promote API to create the rollback rollout."""
  if release_id:
    ref_dict = target_ref.AsDict()
    return resources.REGISTRY.Parse(
        release_id,
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': pipeline_id,
            'releasesId': release_id
        })
  else:
    try:
      _, prior_rollout = target_util.GetReleasesAndCurrentRollout(
          target_ref, pipeline_id, 1)
    except core_exceptions.Error:
      raise core_exceptions.Error(
          'unable to rollback target {}. Target has less than 2 rollouts.'
          .format(target_ref.Name()))

    return resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            prior_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts'
        ).Parent().RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases')
