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
"""Provides common arguments for the Run command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.run import exceptions


def AddFileArg(parser):
  parser.add_argument(
      'FILE',
      type=arg_parsers.YAMLFileContents(),
      help='The absolute path to the YAML file with an application '
      'definition to update or deploy.')


def AddTypeArg(parser):
  """Add an integration type arg."""
  parser.add_argument(
      '--type',
      required=True,
      help='Type of the integration.')


def AddNameArg(parser):
  """Add an integration name arg."""
  parser.add_argument(
      '--name',
      help='Name of the integration.')


def AddNamePositionalArg(parser):
  """Add an integration name arg."""
  parser.add_argument(
      'name',
      help='Name of the integration.')


def AddServiceCreateArg(parser):
  """Add a service arg for create."""
  parser.add_argument(
      '--service',
      help='Name of the Cloud Run service to attach to the integration.')


def AddServiceUpdateArgs(parser):
  """Add service arguments for update."""
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--add-service',
      help='Name of the Cloud Run service to attach to the integration.')
  group.add_argument(
      '--remove-service',
      help='Name of the Cloud Run service to remove from the integration.')


def AddParametersArg(parser):
  """Add a parameters arg."""
  parser.add_argument(
      '--parameters',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      default={},
      metavar='PARAMETER=VALUE',
      help='Comma-separated list of parameter names and values. '
      'Names must be one of the parameters shown when describing the '
      'integration type. Only simple values can be specified with this flag.')


def ValidateParameters(integration_type, parameters, is_create=True):
  """Validates given params conform to what's expected from the integration."""
  if integration_type == 'router':
    if is_create:
      requires = ['domain', 'dns-zone']
      for key in requires:
        if key not in parameters:
          raise exceptions.ArgumentError(
              '[{}] is required to create integration of type [{}]'.format(
                  key, integration_type))


def GetParameters(args):
  """Validates all parameters and returns a dict of values."""
  parameters = {}
  if args.IsSpecified('parameters'):
    parameters.update(args.parameters)

  return parameters
