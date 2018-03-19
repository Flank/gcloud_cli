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
"""This is a command for testing calliope's ability to provide other groups."""

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Recommand(base.Command):

  @staticmethod
  def Args(unused_parser):
    exec_func = Recommand.GetExecutionFunction('command1', '--coolstuff')
    Recommand.func_dict = {'func': exec_func}

  def Run(self, args):
    Recommand.func_dict['func']()
    log.Print('Done!')
