# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""The super-group for the cloud CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class PrintTraceEmailAction(argparse.Action):

  def __init__(self, *args, **kwargs):
    super(PrintTraceEmailAction, self).__init__(*args, nargs=0, **kwargs)

  def __call__(self, *args):
    log.warning('trace_email = {0}'
                .format(properties.VALUES.core.trace_email.Get()))


class Sdk5(calliope_base.Group):

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--print-trace-email-during-parse',
        help='Write trace_email to log.warning during arg parsing.',
        action=PrintTraceEmailAction)
