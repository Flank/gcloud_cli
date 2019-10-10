# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests of gcloud performance.

These tests need a stable environment to get consistent results, so they only
run on Kokoro.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import csv
import datetime
import os
import timeit

from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case

CHANGE_NUMBER = os.environ.get('KOKORO_PIPER_CHANGELIST')
DATETIME = datetime.datetime.now().strftime('%Y-%m-%d %H:00:00')
MAX_TAB_COMPLETION_TIME = 0.05  # 50 milliseconds
MAX_STARTUP_TIME = 0.6  # 600 milliseconds
TAB_COMPLETION_OUTPUT_FILE = os.environ.get('TAB_COMPLETION_TIMES_FILE')
STARTUP_OUTPUT_FILE = os.environ.get('STARTUP_TIMES_FILE')
TIMING_RUNS = 10

TAB_COMPLETION_SCRIPT = """\
export _ARGCOMPLETE=1
export COMP_LINE="{comp_line}"
export COMP_POINT={comp_point}
gcloud 8>/dev/null 9>/dev/null
unset _ARGCOMPLETE COMP_LINE COMP_POINT
"""


class PerformanceTest(sdk_test_base.BundledBase, parameterized.TestCase):

  @parameterized.parameters([
      'gcloud inf',
      'gcloud info --s',
      'gcloud s',
      'gcloud beta c',
      'gcloud beta compute i',
      'gcloud beta compute instances n',
      'gcloud beta compute instances network-interfaces u',
      'gcloud beta compute instances network-interfaces update --al',
      'gcloud --verbosity w',
      'gcloud --verbosity=w',
      'gcloud --verb',
      'gcloud compu'
  ])
  def testStaticCommandCompletion(self, comp_line):
    shell_script = TAB_COMPLETION_SCRIPT.format(comp_line=comp_line,
                                                comp_point=len(comp_line))
    average_time = timeit.timeit(
        'os.system("""{}""")'.format(shell_script),
        setup='import os',
        number=TIMING_RUNS) / TIMING_RUNS
    with open(TAB_COMPLETION_OUTPUT_FILE, 'a') as csv_file:
      csv.writer(csv_file).writerow(
          [DATETIME, CHANGE_NUMBER, comp_line, average_time])
    self.assertLess(average_time, MAX_TAB_COMPLETION_TIME)

  @parameterized.named_parameters([
      ('AppDeploy', 'gcloud app deploy'),
      ('AuthLogin', 'gcloud auth login'),
      ('ComponentsUpdate', 'gcloud components update'),
      ('ContainerImagesList', 'gcloud container images list'),
      ('DataflowJobsRun', 'gcloud dataflow jobs run'),
      ('DataprocClustersList', 'gcloud dataproc clusters list'),
      ('DatastoreCreateIndexes', 'gcloud datastore indexes create'),
      ('DebugSnapshotsCreate', 'gcloud debug snapshots create'),
      ('DeploymentManagerTypesList', 'gcloud deployment-manager types list'),
      ('DnsOperationsDescribe', 'gcloud dns operations describe'),
      ('Docker', 'gcloud docker'),
      ('DomainsVerify', 'gcloud domains verify'),
      ('EndpointsServicesDeploy', 'gcloud endpoints services deploy'),
      ('FirebaseTestAndroidRun', 'gcloud firebase test android run'),
      ('FunctionsDeploy', 'gcloud functions deploy'),
      ('IamRolesCopy', 'gcloud iam roles copy'),
      ('IotDevicesDeleteMyDevice', 'gcloud iot devices delete my-device'),
      ('KmsCryptokeysList', 'gcloud kms cryptokeys list'),
      ('LoggingRead', 'gcloud logging read'),
      ('MetaApisList', 'gcloud meta apis list'),
      ('MlLanguageAnalyzeEntities', 'gcloud ml language analyze-entities'),
      ('MlEngineLocalPredict', 'gcloud ml-engine local predict'),
      ('OrganizationsList', 'gcloud organizations list'),
      ('ProjectsCreate', 'gcloud projects create'),
      ('PubsubSubscriptionsPull', 'gcloud pubsub subscriptions pull'),
      ('ServicesEnable', 'gcloud services enable'),
      ('SourceReposCloneDefault', 'gcloud source repos clone default'),
      ('SpannerDatabasesExecuteSql', 'gcloud spanner databases execute-sql'),
      ('SqlConnect', 'gcloud sql connect'),
      ('Version', 'gcloud version'),
  ])
  def testStartup(self, command):
    average_time = timeit.timeit(
        'os.system("{} --no-such-flag 2>/dev/null")'.format(command),
        setup='import os',
        number=TIMING_RUNS) / TIMING_RUNS
    with open(STARTUP_OUTPUT_FILE, 'a') as csv_file:
      csv.writer(csv_file).writerow(
          [DATETIME, CHANGE_NUMBER, command, average_time])
    self.assertLess(average_time, MAX_STARTUP_TIME)


if __name__ == '__main__':
  test_case.main()
