# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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

"""A command that prints identity token.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class IdentityToken(base.Command):
  """Print an identity token for the active account."""
  detailed_help = {
      'DESCRIPTION': """\
        {description}
        """,
      'EXAMPLES': """\
        To print identity tokens:

          $ {command}
        """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--force-auth-refresh',
        action='store_true',
        help='Force a refresh of the credentials even if they have not '
             'expired yet. By default, credentials will only be refreshed when '
             'necessary.')

  @c_exc.RaiseErrorInsteadOf(auth_exceptions.AuthenticationError, client.Error)
  def Run(self, args):
    """Run the print_identity_token command."""

    cred = c_store.Load()
    if args.force_auth_refresh:
      c_store.Refresh(cred)
    if not cred.id_token64:
      raise auth_exceptions.InvalidIdentityTokenError(
          'No identity token can be obtained from the current credentials.')
    return cred.id_tokenb64
