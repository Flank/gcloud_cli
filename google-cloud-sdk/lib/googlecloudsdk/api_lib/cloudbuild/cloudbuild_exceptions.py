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
"""Exceptions for the cloudbuild API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class ParserError(exceptions.Error):
  """Error parsing YAML into a dictionary."""

  def __init__(self, path, msg):
    msg = 'parsing {path}: {msg}'.format(
        path=path,
        msg=msg,
    )
    super(ParserError, self).__init__(msg)


class ParseProtoException(exceptions.Error):
  """Error interpreting a dictionary as a specific proto message."""

  def __init__(self, path, proto_name, msg):
    msg = 'interpreting {path} as {proto_name}: {msg}'.format(
        path=path,
        proto_name=proto_name,
        msg=msg,
    )
    super(ParseProtoException, self).__init__(msg)


class HybridUnsupportedRegionError(exceptions.Error):
  """Unsupported region for hybrid worker pools specified."""

  def __init__(self, region):
    msg = """hybrid worker pools currently does not support the {region} region. Please use {supported_regions}.""".format(
        region=region,
        supported_regions='\'us-west4\'')
    super(HybridUnsupportedRegionError, self).__init__(msg)


class HybridNonAlphaConfigError(exceptions.Error):
  """Hybrid Configs are currently only supported in the alpha release track."""

  def __init__(self):
    msg = 'invalid config file.'
    super(HybridNonAlphaConfigError, self).__init__(msg)


class WorkerConfigButNoWorkerpoolError(exceptions.Error):
  """The user has not supplied a worker pool even though a workerconfig has been specified."""

  def __init__(self):
    msg = ('Detected a worker pool config but no worker pool. Please specify a '
           'worker pool.')
    super(WorkerConfigButNoWorkerpoolError, self).__init__(msg)
