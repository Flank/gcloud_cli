# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for InsightType Config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import base
from googlecloudsdk.api_lib.recommender import flag_utils
from googlecloudsdk.api_lib.util import apis


def CreateClient(release_track):
  """Creates Client."""
  api_version = flag_utils.GetApiVersion(release_track)
  return InsightTypeConfig(api_version)


class InsightTypeConfig(object):
  """Base InsightTypeConfig client for all versions."""

  def __init__(self, api_version):
    client = apis.GetClientInstance(base.API_NAME, api_version)
    self._api_version = api_version
    self._messages = client.MESSAGES_MODULE
    self._message_prefix = base.RECOMMENDER_MESSAGE_PREFIX[api_version]
    self._project_service = client.projects_locations_insightTypes
    self._org_service = client.organizations_locations_insightTypes

  def _GetMessage(self, message_name):
    """Returns the API messages class by name."""
    return getattr(
        self._messages,
        '{prefix}{name}'.format(prefix=self._message_prefix,
                                name=message_name), None)

  def Get(self, config_name):
    """Gets a InsightTypeConfig.

    Args:
      config_name: str, the name of the config being retrieved.

    Returns:
      The InsightTypeConfig message.
    """
    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsInsightTypesGetConfigRequest(
        name=config_name)
    return self._project_service.GetConfig(request)

  def Update(self, config_name, args):
    """Updates a InsightTypeConfig.

    Args:
      config_name: str, the name of the config being retrieved.
      args: argparse.Namespace, The arguments that the command was invoked with.

    Returns:
      The updated InsightTypeConfig message.
    Raises:
      Exception: If nothing is updated.
    """

    # TODO(b/205859938): Support annotations
    update_mask = []
    config = self._GetMessage('InsightTypeConfig')()
    config.name = config_name
    config.etag = args.etag

    if args.config_file:
      gen_config = flag_utils.ReadConfig(
          args.config_file, self._GetMessage('InsightTypeGenerationConfig'))
      config.insightTypeGenerationConfig = gen_config
      update_mask.append('insight_type_generation_config')

    if args.display_name:
      config.displayName = args.display_name
      update_mask.append('display_name')

    if not update_mask:
      raise Exception(
          'Nothing is being updated. Please specify one of config-file or display-name.'
      )

    # Need to do it this way to dynamically set the versioned InsightTypeConfig
    kwargs = {
        'name':
            config_name,
        flag_utils.ToCamelCase(self._message_prefix + 'InsightTypeConfig'):
            config,
        'updateMask':
            ','.join(update_mask),
        'validateOnly':
            args.validate_only
    }

    # Using Project message is ok for all entities if the name is correct.
    request = self._messages.RecommenderProjectsLocationsInsightTypesUpdateConfigRequest(
        **kwargs)
    return self._project_service.UpdateConfig(request)
