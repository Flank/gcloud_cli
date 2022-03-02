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
"""Base formatter for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc

from googlecloudsdk.core.console import console_attr


class BaseFormatter:
  """Prints the run Integration in a custom human-readable format."""

  @abc.abstractmethod
  def TransformConfig(self, record):
    """Override to describe the format of the config of the integration."""

  @abc.abstractmethod
  def TransformComponentStatus(self, record):
    """Override to describe the format of the components and status of the integration."""

  def CallToAction(self, record):
    """Override to return call to action message.

    Args:
      record: dict, the integration.

    Returns:
      A formatted string of the call to action message,
      or None if no call to action is required.
    """
    del record  # Unused
    return None

  def PrintType(self, ctype):
    """Return the type in a user friendly format.

    Args:
      ctype: the type name to be formatted.

    Returns:
      A formatted string.
    """
    return (ctype
            .replace('google_', '')
            .replace('compute_', '')
            .replace('_', ' ')
            .title())

  def GetResourceState(self, resource):
    """Return the state of the resource.

    Args:
      resource: dict, the resource object.

    Returns:
      The state string.
    """
    state = resource.get('state', '')
    return {
        'GCP_RESOURCE_STATE_DEPLOYED': 'DEPLOYED',
        'GCP_RESOURCE_STATE_MISSING': 'MISSING',
        'GCP_RESOURCE_STATE_PROVISIONING': 'PROVISIONING',
        'GCP_RESOURCE_STATE_READY': 'READY',
        'GCP_RESOURCE_STATE_FAILED': 'FAILED',
    }.get(state, 'UNKNOWN')

  def PrintStatus(self, status):
    """Print the status with symbol and color.

    Args:
      status: string, the status.

    Returns:
      The formatted string.
    """
    return '{} {}'.format(self.StatusSymbolAndColor(status), status)

  def StatusSymbolAndColor(self, status):
    """Return the color symbol for the status.

    Args:
      status: string, the status.

    Returns:
      The symbol string.
    """
    con = console_attr.GetConsoleAttr()
    encoding = console_attr.GetConsoleAttr().GetEncoding()
    if status == 'DEPLOYED' or status == 'READY':
      return con.Colorize(
          self._PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding), 'green')
    if status == 'PROVISIONING':
      return con.Colorize(self._PickSymbol(
          '\N{HORIZONTAL ELLIPSIS}', '.', encoding), 'yellow')
    if status == 'MISSING':
      return con.Colorize('?', 'yellow')
    if status == 'FAILED':
      return con.Colorize('X', 'red')
    return con.Colorize('~', 'blue')

  def _PickSymbol(self, best, alt, encoding):
    """Choose the best symbol (if it's in this encoding) or an alternate."""
    try:
      best.encode(encoding)
      return best
    except UnicodeError:
      return alt
