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

import json
import os
import pickle
import subprocess
import sys
import tempfile

from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import test_case
import mock


class MetricsTests(test_case.Base):

  def SetUp(self):
    # Mock out config/properties that enable/disable reporting
    self.prop_mock = self.StartObjectPatch(
        properties.VALUES.core.disable_usage_reporting, 'GetBool')
    self.prop_mock.return_value = None

    self.config_mock = self.StartObjectPatch(config, 'INSTALLATION_CONFIG')
    self.config_mock.disable_usage_reporting = False
    tmp_dir = files.TemporaryDirectory()
    self.StartEnvPatch({config.CLOUDSDK_CONFIG: tmp_dir.path})

    self.addCleanup(tmp_dir.Close)

    metrics._MetricsCollector._disabled_cache = None
    # Mock out project/machine specific values
    self.collector = metrics._MetricsCollector.GetCollector()
    self.collector._ga_event_params = [('a', 'b'), ('c', 'd')]
    self.collector._ga_timing_params = [('i', 'j')]
    self.collector._csi_params = [('e', 'f'), ('g', 'h')]
    self.collector._clearcut_request_params = {'e': 'f'}
    self.collector._clearcut_concord_event_params = {'a': 'b'}
    self.collector._clearcut_concord_event_metadata = [{'c': 'd'}]
    self.collector._user_agent = 'user-agent-007'
    self.collector._async_popen_args = {'e': 'f'}
    metrics._GA_ENDPOINT = 'http://example.com'
    metrics._CLEARCUT_ENDPOINT = 'endpoint'
    metrics._CSI_ENDPOINT = 'endpoint'
    metrics._MetricsCollector._disabled_cache = None

    # Ensure there are no previously collected metrics
    del self.collector._metrics[:]

    # Set the project id
    project_name = 'test-project'
    properties.VALUES.core.project.Set(project_name)

  def TearDown(self):
    # Disable metrics collection
    metrics._MetricsCollector._disabled_cache = True
    metrics._MetricsCollector._instance = None

  def testDisabling(self):
    cid_mock = self.StartObjectPatch(metrics._MetricsCollector, '_GetCID')
    cid_mock.return_value = '123'

    with mock.patch.dict(os.environ, values={b'_ARGCOMPLETE': b'something'}):
      self.assertEquals(None, metrics._MetricsCollector.GetCollector())
      self.assertEquals('', metrics.GetCIDIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

    with mock.patch.dict(os.environ, clear=True):
      self.assertEquals(
          self.collector, metrics._MetricsCollector.GetCollector())
      self.assertEquals(
          self.collector._GetCID(), metrics.GetCIDIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

    self.prop_mock.return_value = True
    self.assertEquals(None, metrics._MetricsCollector.GetCollector())
    self.assertEquals('', metrics.GetCIDIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

    self.prop_mock.return_value = False
    self.assertEquals(self.collector, metrics._MetricsCollector.GetCollector())
    self.assertEquals(
        self.collector._GetCID(), metrics.GetCIDIfMetricsEnabled())
    self.assertEquals(
        self.collector._GetUserAgent(), metrics.GetUserAgentIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

    self.prop_mock.return_value = None
    self.config_mock.disable_usage_reporting = True
    self.assertEquals(None, metrics._MetricsCollector.GetCollector())
    self.assertEquals('', metrics.GetCIDIfMetricsEnabled())
    self.assertEquals(None, metrics.GetUserAgentIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

    self.config_mock.disable_usage_reporting = False
    self.assertEquals(self.collector, metrics._MetricsCollector.GetCollector())
    self.assertEquals(
        self.collector._GetCID(), metrics.GetCIDIfMetricsEnabled())
    self.assertEquals(
        self.collector._GetUserAgent(), metrics.GetUserAgentIfMetricsEnabled())
    metrics._MetricsCollector._disabled_cache = None

  def _ClearcutMetricFromEventList(self, clearcut_events, request_time=0):
    clearcut_request = {
        'request_time_ms': request_time,
        'log_event': [
            {'source_extension_json': json.dumps(event, sort_keys=True)}
            for event in clearcut_events
        ]
    }
    clearcut_request.update(self.collector._clearcut_request_params)
    clearcut_metric = (
        metrics._CLEARCUT_ENDPOINT,
        'POST',
        json.dumps(clearcut_request, sort_keys=True),
        {'user-agent': self.collector._user_agent})
    return clearcut_metric

  def _ClearcutMetricFromEvent(self, clearcut_event, request_time):
    return self._ClearcutMetricFromEventList([clearcut_event], request_time)

  def testEventsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 0
    metrics.Started(0)

    collected_ga_events = self.collector._ga_events
    expected_ga_events = []
    self.assertEquals(expected_ga_events, collected_ga_events)

    collected_clearcut_events = self.collector._clearcut_concord_events
    expected_clearcut_events = []
    self.assertEquals(expected_clearcut_events, collected_clearcut_events)

    metrics.Installs('cmp1', 'v3')
    expected_ga_events.append('ec=Installs&ea=cmp1&el=v3&ev=0&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Installs',
        'event_name': 'cmp1',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'component_version', 'value': 'v3'}
        ],
        'a': 'b',
    })

    metrics.Executions('cmd1', 'v7')
    expected_ga_events.append('ec=Executions&ea=cmd1&el=v7&ev=0&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Executions',
        'event_name': 'cmd1',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'binary_version', 'value': 'v7'}
        ],
        'a': 'b',
    })

    metrics.Commands('cmd3', 'v13', None)
    expected_ga_events.append('ec=Commands&ea=cmd3&el=v13&ev=0&cd6=&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Commands',
        'event_name': 'cmd3',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    })

    metrics.Error('cmd3', Exception, None)
    expected_ga_events.append(
        'ec=Error&ea=cmd3&el=exceptions.Exception&ev=0&cd6=&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Error',
        'event_name': 'cmd3',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
            {'key': 'error_type', 'value': 'exceptions.Exception'},
        ],
        'a': 'b',
    })

    metrics.Help('cmd3', '--help')
    expected_ga_events.append('ec=Help&ea=cmd3&el=--help&ev=0&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Help',
        'event_name': 'cmd3',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'help_mode', 'value': '--help'}
        ],
        'a': 'b',
    })

    self.assertEquals(expected_ga_events, collected_ga_events)
    self.assertEquals(expected_clearcut_events, collected_clearcut_events)

    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Help%2Ccmd3%2C__help&rt=total.0'
        '&it=remote.0%2Clocal.0&e=f&g=h',
        'GET', None,
        {'user-agent': 'user-agent-007'})

    expected_ga_timings = [
        'utv=total&utt=0&utc=Help&utl=cmd3&i=j',
        'utv=remote&utt=0&utc=Help&utl=cmd3&i=j',
        'utv=local&utt=0&utc=Help&utl=cmd3&i=j'
    ]
    ga_metric = (
        'http://example.com',
        'POST',
        '\n'.join(expected_ga_events + expected_ga_timings),
        {'user-agent': 'user-agent-007'})

    for event in expected_clearcut_events:
      event['latency_ms'] = 0
      event['sub_event_latency_ms'] = [
          {'key': 'total', 'latency_ms': 0},
          {'key': 'local', 'latency_ms': 0},
          {'key': 'remote', 'latency_ms': 0}
      ]
    clearcut_metric = self._ClearcutMetricFromEventList(
        expected_clearcut_events)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testFlagCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 0
    metrics.Started(0)

    collected_ga_events = self.collector._ga_events
    expected_ga_events = []
    self.assertEquals(expected_ga_events, collected_ga_events)

    collected_clearcut_events = self.collector._clearcut_concord_events
    expected_clearcut_events = []
    self.assertEquals(expected_clearcut_events, collected_clearcut_events)

    metrics.Commands('cmd1', 'v13', [])
    expected_ga_events.append(
        'ec=Commands&ea=cmd1&el=v13&ev=0&cd6=%3D%3DNONE%3D%3D&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Commands',
        'event_name': 'cmd1',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '==NONE=='},
        ],
        'a': 'b',
    })

    metrics.Commands('cmd2', 'v13', ['BAZ', '--foo', 'BAR'])
    expected_ga_events.append(
        'ec=Commands&ea=cmd2&el=v13&ev=0&cd6=--foo%2CBAR%2CBAZ&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Commands',
        'event_name': 'cmd2',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '--foo,BAR,BAZ'},
        ],
        'a': 'b',
    })

    metrics.Error('cmd3', Exception, [])
    expected_ga_events.append(
        'ec=Error&ea=cmd3&el=exceptions.Exception&ev=0&cd6=%3D%3DNONE%3D%3D'
        '&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Error',
        'event_name': 'cmd3',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '==NONE=='},
            {'key': 'error_type', 'value': 'exceptions.Exception'}
        ],
        'a': 'b',
    })

    metrics.Error('cmd4', Exception, ['BAZ', '--foo', 'BAR'])
    expected_ga_events.append(
        'ec=Error&ea=cmd4&el=exceptions.Exception&ev=0&cd6=--foo%2CBAR%2CBAZ'
        '&a=b&c=d')
    expected_clearcut_events.append({
        'event_type': 'Error',
        'event_name': 'cmd4',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '--foo,BAR,BAZ'},
            {'key': 'error_type', 'value': 'exceptions.Exception'}
        ],
        'a': 'b',
    })

    self.assertEquals(expected_ga_events, collected_ga_events)
    self.assertEquals(expected_clearcut_events, collected_clearcut_events)

    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Error%2Ccmd4%2Cexceptions%2CException'
        '&flag_names=--foo%2CBAR%2CBAZ&rt=total.0'
        '&it=remote.0%2Clocal.0&e=f&g=h',
        'GET',
        None,
        {'user-agent': 'user-agent-007'})

    expected_ga_timings = [
        'utv=total&utt=0&utc=Error&utl=cmd4&cd6=--foo%2CBAR%2CBAZ&i=j',
        'utv=remote&utt=0&utc=Error&utl=cmd4&cd6=--foo%2CBAR%2CBAZ&i=j',
        'utv=local&utt=0&utc=Error&utl=cmd4&cd6=--foo%2CBAR%2CBAZ&i=j'
    ]
    ga_metric = (
        'http://example.com',
        'POST',
        '\n'.join(expected_ga_events + expected_ga_timings),
        {'user-agent': 'user-agent-007'})

    # In the event of nested execution, only the top level command should have
    # latencies.
    for event in expected_clearcut_events[:1] + expected_clearcut_events[2:]:
      event['latency_ms'] = 0
      event['sub_event_latency_ms'] = [
          {'key': 'total', 'latency_ms': 0},
          {'key': 'local', 'latency_ms': 0},
          {'key': 'remote', 'latency_ms': 0}
      ]
    clearcut_metric = self._ClearcutMetricFromEventList(
        expected_clearcut_events)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testCommandLatencyMetricsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', None)

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 100
    metrics.RPCDuration(0.100)

    time_mock.return_value = 150
    metrics.RPCDuration(0.150)

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Commands%2Ccmd%2Cs_cmd&flag_names=&rt=load.50%2C'
        'run.350%2Ctotal.450&it=remote.250%2Clocal.200&e=f&g=h', 'GET', None,
        {'user-agent': 'user-agent-007'})

    ga_metric = (
        'http://example.com',
        'POST',
        'ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=&a=b&c=d\n'
        'utv=load&utt=50&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=run&utt=350&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=total&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=remote&utt=250&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=local&utt=200&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 200},
            {'key': 'remote', 'latency_ms': 250},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testCommandLatencyMetricsCollectionWithError(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    class ExampleException(Exception):
      pass

    metrics.Commands(
        'group1.group2.command', 'v14', ['--project', '--quiet'],
        error=ExampleException, error_extra_info={'suggestion': 'alpha,beta'}
    )
    example_exception_path = '{0}.{1}'.format(
        ExampleException.__module__, ExampleException.__name__)

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 50
    metrics.RPCDuration(0.050)

    time_mock.return_value = 150
    metrics.RPCDuration(0.150)

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        ('endpoint?action=Commands%2Cgroup1%2Cgroup2%2Ccommand&'
         'flag_names=--project%2C--quiet&'
         'rt=load.50%2Crun.350%2Ctotal.450&it=remote.200%2Clocal.250&e=f&g=h'),
        'GET', None, {'user-agent': 'user-agent-007'})

    command_metric = (
        'http://example.com',
        'POST',
        ('ec=Commands&ea=group1.group2.command&el=v14&ev=0&'
         'cd6=--project%2C--quiet&'
         'cd8={0}&cd9=%7B%22suggestion%22%3A+%22alpha%2Cbeta%22%7D&a=b&c=d\n'
         'utv=load&utt=50&utc=Commands&utl=group1.group2.command&'
         'cd6=--project%2C--quiet&i=j\n'
         'utv=run&utt=350&utc=Commands&utl=group1.group2.command&'
         'cd6=--project%2C--quiet&i=j\n'
         'utv=total&utt=450&utc=Commands&utl=group1.group2.command&'
         'cd6=--project%2C--quiet&i=j\n'
         'utv=remote&utt=200&utc=Commands&utl=group1.group2.command&'
         'cd6=--project%2C--quiet&i=j\n'
         'utv=local&utt=250&utc=Commands&utl=group1.group2.command&'
         'cd6=--project%2C--quiet&i=j')
        .format(example_exception_path),
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Commands',
        'event_name': 'group1.group2.command',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '--project,--quiet'},
            {'key': 'error_type', 'value': example_exception_path},
            {'key': 'extra_error_info',
             'value': '{"suggestion": "alpha,beta"}'
            },
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 250},
            {'key': 'remote', 'latency_ms': 200},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, command_metric, clearcut_metric],
                      self.collector._metrics)

  def testCommandLatencyMetricsCollectionWithoutFlags(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', [])

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Commands%2Ccmd%2Cs_cmd&flag_names=%3D%3DNONE%3D%3D&rt='
        'load.50%2Crun.350%2Ctotal.450&it=remote.0%2Clocal.450&e=f&g=h', 'GET',
        None, {'user-agent': 'user-agent-007'})

    # pylint: disable=line-too-long
    ga_metric = (
        'http://example.com',
        'POST',
        'ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=%3D%3DNONE%3D%3D&a=b&c=d\n'
        'utv=load&utt=50&utc=Commands&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=run&utt=350&utc=Commands&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=total&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=remote&utt=0&utc=Commands&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=local&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '==NONE=='},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 450},
            {'key': 'remote', 'latency_ms': 0},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testCommandLatencyMetricsCollectionWithFlags(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', ['BAZ', '--foo', 'BAR'])

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Commands%2Ccmd%2Cs_cmd&flag_names=--foo%2CBAR%2CBAZ'
        '&rt=load.50%2Crun.350%2Ctotal.450&it=remote.0%2Clocal.450&e=f&g=h',
        'GET', None, {'user-agent': 'user-agent-007'})

    # pylint: disable=line-too-long
    command_metric = (
        'http://example.com',
        'POST',
        'ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=--foo%2CBAR%2CBAZ&a=b&c=d\n'
        'utv=load&utt=50&utc=Commands&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=run&utt=350&utc=Commands&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=total&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=remote&utt=0&utc=Commands&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=local&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '--foo,BAR,BAZ'},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 450},
            {'key': 'remote', 'latency_ms': 0},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, command_metric, clearcut_metric],
                      self.collector._metrics)

  def testErrorLatencyMetricsCollectionWithoutFlags(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Error('cmd.s-cmd', Exception, [])

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Error%2Ccmd%2Cs_cmd%2Cexceptions%2CException'
        '&flag_names=%3D%3DNONE%3D%3D&rt=load.50%2Crun.350%2Ctotal.450'
        '&it=remote.0%2Clocal.450&e=f&g=h', 'GET', None,
        {'user-agent': 'user-agent-007'})

    ga_metric = (
        'http://example.com',
        'POST',
        'ec=Error&ea=cmd.s-cmd&el=exceptions.Exception&ev=0&'
        'cd6=%3D%3DNONE%3D%3D&a=b&c=d\n'
        'utv=load&utt=50&utc=Error&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=run&utt=350&utc=Error&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=total&utt=450&utc=Error&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=remote&utt=0&utc=Error&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j\n'
        'utv=local&utt=450&utc=Error&utl=cmd.s-cmd&cd6=%3D%3DNONE%3D%3D&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Error',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '==NONE=='},
            {'key': 'error_type', 'value': 'exceptions.Exception'},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 450},
            {'key': 'remote', 'latency_ms': 0},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testErrorLatencyMetricsCollectionWithFlags(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Error('cmd.s-cmd', Exception, ['BAZ', '--foo', 'BAR'])

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Error%2Ccmd%2Cs_cmd%2Cexceptions%2CException'
        '&flag_names=--foo%2CBAR%2CBAZ&rt=load.50%2Crun.350%2Ctotal.450'
        '&it=remote.0%2Clocal.450&e=f&g=h', 'GET', None,
        {'user-agent': 'user-agent-007'})

    ga_metric = (
        'http://example.com',
        'POST',
        'ec=Error&ea=cmd.s-cmd&el=exceptions.Exception&ev=0&'
        'cd6=--foo%2CBAR%2CBAZ&a=b&c=d\n'
        'utv=load&utt=50&utc=Error&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=run&utt=350&utc=Error&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=total&utt=450&utc=Error&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=remote&utt=0&utc=Error&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j\n'
        'utv=local&utt=450&utc=Error&utl=cmd.s-cmd&cd6=--foo%2CBAR%2CBAZ&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Error',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': '--foo,BAR,BAZ'},
            {'key': 'error_type', 'value': 'exceptions.Exception'},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 450},
            {'key': 'remote', 'latency_ms': 0},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testNestedCommandsMetricsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', None)
    ga_events = ['ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=&a=b&c=d']
    clearcut_events = [{
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    }]

    time_mock.return_value = 150
    metrics.Loaded()

    metrics.Commands('cmd.inner-cmd', 'v0', None)
    ga_events.append('ec=Commands&ea=cmd.inner-cmd&el=v0&ev=0&cd6=&a=b&c=d')
    clearcut_events.append({
        'event_type': 'Commands',
        'event_name': 'cmd.inner-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    })

    time_mock.return_value = 250
    metrics.Loaded()

    time_mock.return_value = 100
    metrics.RPCDuration(0.100)

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 150
    metrics.RPCDuration(0.150)

    time_mock.return_value = 850
    metrics.Ran()

    time_mock.return_value = 950
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Commands%2Ccmd%2Cs_cmd&flag_names=&rt=load.50%2C'
        'run.750%2Ctotal.850&it=remote.250%2Clocal.600&e=f&g=h', 'GET', None,
        {'user-agent': 'user-agent-007'})

    ga_timings = [
        'utv=load&utt=50&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        'utv=run&utt=750&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        'utv=total&utt=850&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        'utv=remote&utt=250&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        'utv=local&utt=600&utc=Commands&utl=cmd.s-cmd&cd6=&i=j'
    ]
    ga_commands_metric = (
        'http://example.com',
        'POST',
        '\n'.join(ga_events + ga_timings),
        {'user-agent': 'user-agent-007'})

    clearcut_events[0].update({
        'latency_ms': 850,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 750},
            {'key': 'total', 'latency_ms': 850},
            {'key': 'local', 'latency_ms': 600},
            {'key': 'remote', 'latency_ms': 250},
        ]
    })
    clearcut_metric = self._ClearcutMetricFromEventList(clearcut_events, 950)

    self.assertEquals([csi_metric, ga_commands_metric, clearcut_metric],
                      self.collector._metrics)

  def testCustomTimedEventsMetricsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', None)

    time_mock.return_value = 150
    metrics.Loaded()

    time_mock.return_value = 450
    metrics.Ran()

    time_mock.return_value = 500
    metrics.CustomTimedEvent('myevent')

    time_mock.return_value = 525
    metrics.CustomTimedEvent('myevent')

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Commands%2Ccmd%2Cs_cmd&flag_names=&rt=load.50%2C'
        'run.350%2Cmyevent.400%2Cmyevent.425%2Ctotal.450'
        '&it=remote.0%2Clocal.450&e=f&g=h', 'GET', None,
        {'user-agent': 'user-agent-007'})

    ga_metric = (
        'http://example.com',
        'POST',
        'ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=&a=b&c=d\n'
        'utv=load&utt=50&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=run&utt=350&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=myevent&utt=400&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=myevent&utt=425&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=total&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=remote&utt=0&utc=Commands&utl=cmd.s-cmd&cd6=&i=j\n'
        'utv=local&utt=450&utc=Commands&utl=cmd.s-cmd&cd6=&i=j',
        {'user-agent': 'user-agent-007'})

    clearcut_event = {
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
        'latency_ms': 450,
        'sub_event_latency_ms': [
            {'key': 'load', 'latency_ms': 50},
            {'key': 'run', 'latency_ms': 350},
            {'key': 'myevent', 'latency_ms': 400},
            {'key': 'myevent', 'latency_ms': 425},
            {'key': 'total', 'latency_ms': 450},
            {'key': 'local', 'latency_ms': 450},
            {'key': 'remote', 'latency_ms': 0},
        ]
    }
    clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testCommandFollowedByErrorMetricsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', None)
    ga_events = ['ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=&a=b&c=d']
    clearcut_events = [{
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    }]

    time_mock.return_value = 150
    metrics.Loaded()

    metrics.Error('cmd.s-cmd', Exception, None)
    ga_events.append(
        'ec=Error&ea=cmd.s-cmd&el=exceptions.Exception&ev=0&cd6=&a=b&c=d')
    clearcut_events.append({
        'event_type': 'Error',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
            {'key': 'error_type', 'value': 'exceptions.Exception'},
        ],
        'a': 'b',
    })

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Error%2Ccmd%2Cs_cmd%2Cexceptions%2CException&'
        'flag_names=&rt=load.50%2Ctotal.450&it=remote.0%2Clocal.450&e=f&g=h',
        'GET', None, {'user-agent': 'user-agent-007'})

    ga_timings = [
        'utv=load&utt=50&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=total&utt=450&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=remote&utt=0&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=local&utt=450&utc=Error&utl=cmd.s-cmd&cd6=&i=j'
    ]
    ga_metric = (
        'http://example.com',
        'POST',
        '\n'.join(ga_events + ga_timings),
        {'user-agent': 'user-agent-007'})

    for event in clearcut_events:
      event['latency_ms'] = 450
      event['sub_event_latency_ms'] = [
          {'key': 'load', 'latency_ms': 50},
          {'key': 'total', 'latency_ms': 450},
          {'key': 'local', 'latency_ms': 450},
          {'key': 'remote', 'latency_ms': 0}
      ]
    clearcut_metric = self._ClearcutMetricFromEventList(clearcut_events, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testNestedCommandsFollowedByErrorMetricsCollection(self):
    time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
    time_mock.return_value = 100
    metrics.Started(0.100)

    metrics.Commands('cmd.s-cmd', 'v13', None)
    ga_events = ['ec=Commands&ea=cmd.s-cmd&el=v13&ev=0&cd6=&a=b&c=d']
    clearcut_events = [{
        'event_type': 'Commands',
        'event_name': 'cmd.s-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    }]

    time_mock.return_value = 150
    metrics.Loaded()

    metrics.Commands('cmd.inner-cmd', 'v0', None)
    ga_events.append('ec=Commands&ea=cmd.inner-cmd&el=v0&ev=0&cd6=&a=b&c=d')
    clearcut_events.append({
        'event_type': 'Commands',
        'event_name': 'cmd.inner-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
        ],
        'a': 'b',
    })

    time_mock.return_value = 250
    metrics.Loaded()

    time_mock.return_value = 150
    metrics.RPCDuration(0.150)

    metrics.Error('cmd.inner-cmd', Exception, None)
    ga_events.append(
        'ec=Error&ea=cmd.inner-cmd&el=exceptions.Exception&ev=0&cd6=&a=b&c=d')
    clearcut_events.append({
        'event_type': 'Error',
        'event_name': 'cmd.inner-cmd',
        'event_metadata': [
            {'c': 'd'},
            {'key': 'flag_names', 'value': ''},
            {'key': 'error_type', 'value': 'exceptions.Exception'},
        ],
        'a': 'b',
    })

    time_mock.return_value = 550
    self.StartObjectPatch(metrics._MetricsCollector, 'ReportMetrics')
    metrics.Shutdown()

    csi_metric = (
        'endpoint?action=Error%2Ccmd%2Cs_cmd%2Cexceptions%2CException&'
        'flag_names=&rt=load.50%2Ctotal.450&it=remote.150%2Clocal.300&e=f&g=h',
        'GET', None, {'user-agent': 'user-agent-007'})

    ga_timings = [
        'utv=load&utt=50&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=total&utt=450&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=remote&utt=150&utc=Error&utl=cmd.s-cmd&cd6=&i=j',
        'utv=local&utt=300&utc=Error&utl=cmd.s-cmd&cd6=&i=j'
    ]
    ga_metric = (
        'http://example.com',
        'POST',
        '\n'.join(ga_events + ga_timings),
        {'user-agent': 'user-agent-007'})

    # In the event of nested execution, only the top level command should have
    # latencies.
    for event in clearcut_events[:1] + clearcut_events[2:]:
      event['latency_ms'] = 450
      event['sub_event_latency_ms'] = [
          {'key': 'load', 'latency_ms': 50},
          {'key': 'total', 'latency_ms': 450},
          {'key': 'local', 'latency_ms': 300},
          {'key': 'remote', 'latency_ms': 150}
      ]
    clearcut_metric = self._ClearcutMetricFromEventList(clearcut_events, 550)

    self.assertEquals([csi_metric, ga_metric, clearcut_metric],
                      self.collector._metrics)

  def testMetricsReporting(self):
    with files.TemporaryDirectory() as temp_path:
      metrics_file_path = self.Touch(directory=temp_path)
      temp_file_mock = self.StartObjectPatch(tempfile, 'NamedTemporaryFile')
      temp_file_mock.return_value = open(metrics_file_path, 'wb')

      py_args_mock = self.StartObjectPatch(execution_utils, 'ArgsForPythonTool')
      py_args_mock.return_value = ['run', 'python']

      env_mock = self.StartObjectPatch(os.environ, 'copy')
      env_mock.return_value = {}

      popen_mock = self.StartObjectPatch(subprocess, 'Popen')

      self.collector.ReportMetrics()
      self.assertEquals(0, popen_mock.call_count)

      time_mock = self.StartObjectPatch(metrics, '_GetTimeMillis')
      time_mock.return_value = 100
      metrics.Started(0.100)

      metrics.Commands('cmd3', 'v13', None)

      custom_metric = ('https://foo.com', 'GET', 'body', {'header': 'val'})
      metrics.CustomBeacon(*custom_metric)

      time_mock.return_value = 550
      metrics.Shutdown()
      csi_metric = (
          'endpoint?action=Commands%2Ccmd3&flag_names=&rt=total.450'
          '&it=remote.0%2Clocal.450&e=f&g=h', 'GET', None,
          {'user-agent': 'user-agent-007'})

      ga_metric = ('http://example.com',
                   'POST',
                   'ec=Commands&ea=cmd3&el=v13&ev=0&cd6=&a=b&c=d\n'
                   'utv=total&utt=450&utc=Commands&utl=cmd3&cd6=&i=j\n'
                   'utv=remote&utt=0&utc=Commands&utl=cmd3&cd6=&i=j\n'
                   'utv=local&utt=450&utc=Commands&utl=cmd3&cd6=&i=j',
                   {'user-agent': 'user-agent-007'})

      clearcut_event = {
          'event_type': 'Commands',
          'event_name': 'cmd3',
          'event_metadata': [
              {'c': 'd'},
              {'key': 'flag_names', 'value': ''},
          ],
          'a': 'b',
          'latency_ms': 450,
          'sub_event_latency_ms': [
              {'key': 'total', 'latency_ms': 450},
              {'key': 'local', 'latency_ms': 450},
              {'key': 'remote', 'latency_ms': 0},
          ]
      }
      clearcut_metric = self._ClearcutMetricFromEvent(clearcut_event, 550)

      call_list = popen_mock.call_args_list
      self.assertEquals(1, len(call_list))
      args, kwargs = call_list[0]
      self.assertEquals(py_args_mock.return_value, args[0])
      self.assertEquals('f', kwargs['e'])
      self.assertIn('PYTHONPATH', kwargs['env'])
      missing_paths = (set(sys.path) -
                       set(kwargs['env']['PYTHONPATH'].split(os.pathsep)))
      self.assertEquals(set(), missing_paths)
      self.assertEquals([], self.collector._metrics)

      with open(metrics_file_path, 'rb') as metrics_file:
        reported_metrics = pickle.load(metrics_file)
      self.assertEquals([custom_metric, csi_metric, ga_metric, clearcut_metric],
                        reported_metrics)

  def testMetricsReporting_MetricsReportingProcessFails(self):
    self.StartObjectPatch(tempfile, 'NamedTemporaryFile')

    py_args_mock = self.StartObjectPatch(execution_utils, 'ArgsForPythonTool')
    py_args_mock.return_value = ['run', 'python']

    env_mock = self.StartObjectPatch(os.environ, 'copy')
    env_mock.return_value = {}

    popen_mock = self.StartObjectPatch(subprocess, 'Popen')
    popen_mock.side_effect = OSError()

    self.collector._metrics.append(('dummy metric',))
    # Shouldn't raise an exception
    self.collector.ReportMetrics()

    self.assertTrue(popen_mock.called)

  def testCommandsWhenException(self):
    func_mock = self.StartObjectPatch(
        metrics, '_RecordEventAndSetTimerContext')
    func_mock.side_effect = Exception('Failed')

    metrics.Commands('cmd1', 'v7', None)
    self.assertTrue(func_mock.called)

  def testErrorWhenException(self):
    func_mock = self.StartObjectPatch(
        metrics, '_RecordEventAndSetTimerContext')
    func_mock.side_effect = Exception('Failed')

    metrics.Error('cmd1', Exception('Test').__class__, None)
    self.assertTrue(func_mock.called)

  def testExecutionsWhenException(self):
    func_mock = self.StartObjectPatch(metrics._MetricsCollector, 'GetCollector')
    func_mock.side_effect = Exception('Failed to get collector')

    metrics.Executions('cmd1', 'v7')
    self.assertTrue(func_mock.called)

  def testHelpWhenException(self):
    func_mock = self.StartObjectPatch(
        metrics, '_RecordEventAndSetTimerContext')
    func_mock.side_effect = Exception('Failed')

    metrics.Help('cmd1', 'help')
    self.assertTrue(func_mock.called)

  def testInstallsWhenException(self):
    func_mock = self.StartObjectPatch(
        metrics, '_RecordEventAndSetTimerContext')
    func_mock.side_effect = Exception('Failed')

    metrics.Installs('cmd1', 'v7')
    self.assertTrue(func_mock.called)

  def testShutdownWhenException(self):
    func_mock = self.StartObjectPatch(
        metrics._MetricsCollector, 'GetCollectorIfExists')
    func_mock.side_effect = Exception('Failed')

    metrics.Shutdown()
    self.assertTrue(func_mock.called)

if __name__ == '__main__':
  test_case.main()
