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

import logging

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class LoggingCommand(base.Command):

  def Run(self, unused_args):
    """Run this command."""
    # Standard logging stuff.
    logger = logging.getLogger()
    logger.info('INFO message1')
    logger.warning('WARNING message1')
    logger.error('ERROR message1')

    # Logging using the special logger
    log.info('INFO message2')
    log.warning('WARNING message2')
    log.error('ERROR message2')

    # Logging using the special writer
    log.out.write('INFO message3\n')
    log.err.write('INFO message4\n')
