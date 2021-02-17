# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Library for retrieving declarative parsers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.util.declarative.clients import client_base
from googlecloudsdk.core.util import files


def AddPathFlag(parser, required=False):
  parser.add_argument(
      '--path',
      required=required,
      type=files.ExpandHomeAndVars,
      default='-',
      help=('Path of the directory or file to output configuration(s). To '
            'output configurations to stdout, specify "--path=-".'))


def AddFormatFlag(parser):
  parser.add_argument(
      '--resource-format',
      choices=['krm', 'terraform'],
      help=('Format of the configuration to export. Available configuration '
            'formats are Kubernetes Resource Model (krm) or Terraform '
            'HCL (terraform). Command defaults to "krm".'))


def AddAllFlag(parser, collection='collection'):
  parser.add_argument(
      '--all',
      action='store_true',
      help=(
          'Retrieve all resources within the {}. If `--path` is '
          'specified and is a valid directory, resources will be output as '
          'individual files based on resource name and scope. If `--path` is not '
          'specified, resources will be streamed to stdout.'.format(collection)
      ))


def AddOnErrorFlag(parser):
  parser.add_argument(
      '--on-error',
      choices=['continue', 'halt', 'ignore'],
      default='ignore',
      help=('Determines behavior when a recoverable error is encountered while '
            'exporting a resource. To stop execution when encountering an '
            'error, specify "halt". To log errors when encountered and '
            'continue the export, specify "continue". To continue when errors '
            'are encountered without logging, specify "ignore".'))


def AddBulkExportArgs(parser):
  """Adds flags for the bulk-export command."""
  AddOnErrorFlag(parser)
  AddPathFlag(parser)
  AddFormatFlag(parser)
  group = parser.add_group(mutex=True)
  group.add_argument('--organization', type=str, help='Organization ID')
  group.add_argument('--project', help='Project ID')
  group.add_argument('--folder', type=str, help='Folder ID')


def ValidateAllPathArgs(args):
  if args.IsSpecified('all'):
    if args.IsSpecified('path') and not os.path.isdir(args.path):
      raise client_base.ClientException(
          'Error executing export: "{}" must be a directory when --all is specified.'
          .format(args.path))
