# Copyright 2015 Google Inc. All Rights Reserved.
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
"""This is a command for testing."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


class DictList(base.Command):  # pylint:disable=missing-docstring

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--list',
        type=arg_parsers.ArgList(),
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-list',
        type=arg_parsers.ArgList(),
        action='append',
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-list-update',
        type=arg_parsers.ArgList(),
        action=arg_parsers.UpdateAction,
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-list-update-with-append',
        type=arg_parsers.ArgList(),
        action=arg_parsers.UpdateActionWithAppend,
        help='Auxilio aliis.')

    parser.add_argument(
        '--dict',
        type=arg_parsers.ArgDict(),
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-dict',
        type=arg_parsers.ArgDict(),
        action='append',
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-dict-update',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help='Auxilio aliis.')
    parser.add_argument(
        '--repeated-dict-update-with-append',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateActionWithAppend,
        help='Auxilio aliis.')
    parser.add_argument(
        '--store-once',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.StoreOnceAction,
        help='Auxilio aliis.')

    parser.add_argument(
        '--int-list',
        type=arg_parsers.ArgList(element_type=int),
        help='Auxilio aliis.')
    parser.add_argument(
        '--choice-list',
        type=arg_parsers.ArgList(choices=['a', 'b', 'c']),
        help='Auxilio aliis.')

  def repr_dict_ordered(self, d):
    """Return a dictionary string in key-sorted order."""
    if not d:
      return '{}'

    values = []
    for k in sorted(d.iterkeys()):
      value = d[k]
      if isinstance(value, list):
        values.append("'{0}': {1}".format(k, value))
      else:
        values.append("'{0}': '{1}'".format(k, value))

    return '{' + ', '.join(values) + '}'

  def Run(self, args):
    print 'list:', repr(args.list)
    print 'repeated-list:', repr(args.repeated_list)
    print 'repeated-list-update:', repr(args.repeated_list_update)
    print 'repeated-list-update-with-append:', repr(
        args.repeated_list_update_with_append)
    print 'dict:', repr(args.dict)
    print 'repeated-dict:', repr(args.repeated_dict)
    print 'repeated-dict-update:', self.repr_dict_ordered(
        args.repeated_dict_update)
    print 'repeated-dict-update-with-append:', self.repr_dict_ordered(
        args.repeated_dict_update_with_append)
    print 'store-once:', self.repr_dict_ordered(args.store_once)
    print 'int-list:', repr(args.int_list)
    print 'choice-list:', repr(args.choice_list)
