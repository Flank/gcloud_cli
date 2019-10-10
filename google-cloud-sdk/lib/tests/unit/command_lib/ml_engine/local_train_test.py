# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.

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
"""Tests for the ML Engine local_train command_lib utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import atexit
import io
import os
import shutil
import subprocess

from googlecloudsdk.command_lib.ml_engine import local_train
from googlecloudsdk.core import yaml
from tests.lib import sdk_test_base
from tests.lib.surface.ml_engine import base
import mock


class LocalTrainTest(base.MlBetaPlatformTestBase):

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testMakeProcess_Master(self):
    package_dir = self.Resource(
        'tests', 'unit', 'command_lib', 'ml_engine', 'test_data',
        'package_root')
    run_root = os.path.join(self.temp_path, 'run_dir')
    shutil.copytree(package_dir, run_root)
    module_name = 'test_package.test_task'
    args = ['foo']
    # We can only check the return code due to the weird semantics of
    # MakeProcess
    return_code = local_train.MakeProcess(
        module_name,
        run_root,
        args=args,
        task_type='master',
        index=0,
        cluster={},
        stdout=subprocess.PIPE
    )
    self.assertEqual(return_code, 0)

  @sdk_test_base.Filters.RunOnlyOnGCE
  def testMakeProcess_Distributed(self):
    package_dir = self.Resource(
        'tests', 'unit', 'command_lib', 'ml_engine', 'test_data',
        'package_root')
    run_root = os.path.join(self.temp_path, 'run_dir')
    shutil.copytree(package_dir, run_root)
    module_name = 'test_package.test_task'
    out = io.BytesIO()
    args = ['foo']
    cluster = {'distributed': ['address_1']}
    stdout, _ = local_train.MakeProcess(
        module_name,
        run_root,
        args=args,
        task_type='distributed',
        index=0,
        cluster=cluster,
        stdout=subprocess.PIPE
    ).communicate()
    out.write(stdout)
    self.assertEqual(yaml.load(out.getvalue()), {
        'TF_CONFIG': {
            'job': {'job_name': module_name, 'args': args},
            'task': {'type': 'distributed', 'index': 0},
            'cluster': cluster,
            'environment': 'cloud',
        },
        'PWD': run_root,
        'ARGS': ['foo']
    })

  def _mockMakeProcess(self):
    wait_mock = mock.MagicMock()
    poll_mock = mock.MagicMock()
    poll_mock.return_value = None
    terminate_mock = mock.MagicMock()
    return mock.MagicMock(
        wait=wait_mock,
        poll=poll_mock,
        terminate=terminate_mock)

  def testRunDistributedErrorMaster(self):
    a = self._mockMakeProcess()
    b = self._mockMakeProcess()
    popen_mock = self.StartPatch('subprocess.Popen', side_effect=[
        a, b, RuntimeError])
    kill_mock = self.StartPatch(
        'googlecloudsdk.core.execution_utils.KillSubprocess')
    with self.assertRaises(RuntimeError):
      local_train.RunDistributed(
          'test_package.test_task', self.temp_path, 2, 2, 0)
    atexit._run_exitfuncs()
    self.assertEqual(popen_mock.call_count, 3)
    kill_mock.assert_has_calls([
        mock.call(a),
        mock.call(b)
    ], any_order=True)

  def testRunDistributed(self):
    exec_mock = self.StartPatch('googlecloudsdk.core.execution_utils.Exec')
    ps_mock = mock.MagicMock()
    worker_mock = mock.MagicMock()
    popen_mock = self.StartPatch('subprocess.Popen', side_effect=[
        ps_mock, worker_mock])
    kill_mock = self.StartPatch(
        'googlecloudsdk.core.execution_utils.KillSubprocess')
    local_train.RunDistributed(
        'test_package.test_task', self.temp_path, 1, 1, 0)
    self.assertEqual(popen_mock.call_count, 2)
    exec_mock.assert_called_once()
    atexit._run_exitfuncs()
    kill_mock.assert_has_calls([
        mock.call(ps_mock),
        mock.call(worker_mock)
    ], any_order=True)

  def testUseSystemPython(self):
    environ_cp = os.environ.copy()
    environ_cp['CLOUDSDK_PYTHON'] = 'DUMMY_STRING'
    self.StartPatch('os.environ', return_value=environ_cp)
    exec_mock = self.StartPatch('googlecloudsdk.core.execution_utils.Exec')
    local_train.MakeProcess('foo', 'bar', task_type='master')
    exec_cmd = exec_mock.call_args[0][0]
    self.assertNotEqual(exec_cmd[0], 'DUMMY_STRING')

  def testArgs(self):
    exec_mock = self.StartPatch('googlecloudsdk.core.execution_utils.Exec')
    args = ['foo', 'bar']
    local_train.MakeProcess('baz', 'zap', task_type='master', args=args)
    exec_cmd = exec_mock.call_args[0][0]
    self.assertEqual(exec_cmd[3:], args)
