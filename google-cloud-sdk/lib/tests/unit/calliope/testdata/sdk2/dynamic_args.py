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

"""DynamicPositionalAction test command."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import log


def IsInterestingDest(dest):
  return (dest[0].isalpha() and dest.islower() and
          dest not in ['authority_selector', 'authorization_token_file',
                       'calliope_command', 'command_path', 'configuration',
                       'credential_file_override', 'document', 'flatten',
                       'format', 'http_timeout', 'log_http',
                       'top_flag', 'user_output_enabled'])


class AddDynamicFlags(parser_extensions.DynamicPositionalAction):
  """Add flags during the parse."""

  def GenerateArgs(self, namespace, name):
    log.status.write('{}\n'.format(
        ','.join([dest for dest in sorted(namespace.__dict__.keys())
                  if IsInterestingDest(dest)])))
    args = []
    if not namespace.additional:
      return args
    if namespace.flags:
      for dest in namespace.flags.split():
        flag = '--' + dest
        arg = base.Argument(
            flag,
            dest=dest,
            category='DYNAMIC FLAGS',
            help='`{}` dynamic flag.'.format(dest))
        args.append(arg)
      arg = base.Argument(
          'extra',
          nargs='?',
          help='An extra positional.')
      args.append(arg)
    setattr(namespace, 'name', name)
    return args

  def Completions(self, prefix, parsed_args, **kwargs):
    return ['alpha', 'beta', 'gamma']


class DynamiArgs(base.Command):
  """parser_extensions.DynamicPositionalAction test command."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--additional',
        action='store_true',
        default=True,
        help='Add additional dynamic args.')
    parser.add_argument(
        '--flags',
        default='',
        help='A comma separated list of flag dest names to add.')
    parser.AddDynamicPositional(
        'name',
        action=AddDynamicFlags,
        help='The dynamic arg positional.')

  def Run(self, args):
    log.status.write('{}\n'.format(
        ','.join([dest for dest in sorted(args.__dict__.keys())
                  if IsInterestingDest(dest)])))
    for name in [
        'additional', 'extra', 'flags', 'name'] + args.flags.split(','):
      if hasattr(args, name):
        print '{}={}'.format(name, getattr(args, name))
    return None
