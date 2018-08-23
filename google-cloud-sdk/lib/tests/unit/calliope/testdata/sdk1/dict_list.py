# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
import six


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

  def repr_all(self, obj):
    """Basically just a helper to make repr work the same on python 2 and 3."""
    if not obj:
      return ''
    if isinstance(obj, six.string_types):
      return "'{}'".format(obj)
    elif isinstance(obj, list):
      return '[{}]'.format(', '.join([self.repr_all(v) for v in obj]))
    elif isinstance(obj, dict):
      values = []
      for k, v in sorted(six.iteritems(obj)):
        values.append("'{0}': {1}".format(k, self.repr_all(v)))
      return '{' + ', '.join(values) + '}'
    else:
      return six.text_type(obj)

  def Run(self, args):
    print('list:', self.repr_all(args.list))
    print('repeated-list:', self.repr_all(args.repeated_list))
    print('repeated-list-update:', self.repr_all(args.repeated_list_update))
    print('repeated-list-update-with-append:', self.repr_all(
        args.repeated_list_update_with_append))
    print('dict:', self.repr_all(args.dict))
    print('repeated-dict:', self.repr_all(args.repeated_dict))
    print('repeated-dict-update:', self.repr_all(
        args.repeated_dict_update) or '{}')
    print('repeated-dict-update-with-append:', self.repr_all(
        args.repeated_dict_update_with_append) or '{}')
    print('store-once:', self.repr_all(args.store_once) or '{}')
    print('int-list:', self.repr_all(args.int_list))
    print('choice-list:', self.repr_all(args.choice_list))
