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
"""Test of the 'dataflow jobs export-steps' command."""

from apitools.base.py import encoding

from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.dataflow import base

JOB_1_ID = base.JOB_1_ID


WORDCOUNT_DOT = """\
strict digraph "StepGraph" {
subgraph "cluster CountWords" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords";
label="CountWords";
subgraph "cluster CountWords/Count.PerElement" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords/Count.PerElement";
label="Count.PerElement";
"s3" [label="Init", tooltip="CountWords/Count.PerElement/Init", style=filled, fillcolor=white];
subgraph "cluster CountWords/Count.PerElement/Sum.PerKey" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords/Count.PerElement/Sum.PerKey";
label="Sum.PerKey";
"s4" [label="GroupByKey/GroupByKeyOnly", tooltip="CountWords/Count.PerElement/Sum.PerKey/GroupByKey/GroupByKeyOnly", style=filled, fillcolor=white];
"s5" [label="GroupedValues", tooltip="CountWords/Count.PerElement/Sum.PerKey/GroupedValues", style=filled, fillcolor=white];
}
}
"s2" [label="ExtractWords", tooltip="CountWords/ExtractWords", style=filled, fillcolor=white];
"s6" [label="FormatCounts", tooltip="CountWords/FormatCounts", style=filled, fillcolor=white];
}
"s1" [label="ReadLines", tooltip="ReadLines", style=filled, fillcolor=white];
"s7" [label="WriteCounts", tooltip="WriteCounts", style=filled, fillcolor=white];

"s1" -> "s2" [taillabel="output", style=solid];
"s2" -> "s3" [taillabel="out", style=solid];
"s3" -> "s4" [taillabel="out", style=solid];
"s4" -> "s5" [taillabel="output", style=solid];
"s5" -> "s6" [taillabel="output", style=solid];
"s6" -> "s7" [taillabel="out", style=solid];
}
"""


class ExportStepsUnitTest(base.DataflowMockingTestBase,
                          sdk_test_base.WithOutputCapture):

  def SetUp(self):
    self.view_all = (
        base.MESSAGE_MODULE.DataflowProjectsLocationsJobsGetRequest.
        ViewValueValuesEnum.JOB_VIEW_ALL)

  def testExportStepsWordCountDot(self):
    job_json = self.Resource('tests', 'unit', 'surface', 'dataflow',
                             'test_data', 'WordCountJob.json')
    with open(job_json) as f:
      job = encoding.JsonToMessage(base.MESSAGE_MODULE.Job, f.read())
    self.MockGetJob(job, view=self.view_all)
    self.Run('beta dataflow jobs export-steps %s' % JOB_1_ID)

    self.AssertOutputEquals(WORDCOUNT_DOT)

  def testExportStepsWordCountDotWithRegion(self):
    my_region = 'europe-west1'
    job_json = self.Resource('tests', 'unit', 'surface', 'dataflow',
                             'test_data', 'WordCountJob.json')
    with open(job_json) as f:
      job = encoding.JsonToMessage(base.MESSAGE_MODULE.Job, f.read())
    self.MockGetJob(job, view=self.view_all, location=my_region)
    self.Run('beta dataflow jobs export-steps --region=%s %s' % (my_region,
                                                                 JOB_1_ID))

    self.AssertOutputEquals(WORDCOUNT_DOT)

  def testExportStepsWordCountDefault(self):
    job_json = self.Resource('tests', 'unit', 'surface', 'dataflow',
                             'test_data', 'WordCountJob.json')
    with open(job_json) as f:
      job = encoding.JsonToMessage(
          base.MESSAGE_MODULE.Job,
          f.read())
    self.MockGetJob(job, view=self.view_all)
    self.Run('beta dataflow jobs export-steps %s' % JOB_1_ID)

    self.AssertOutputEquals("""\
strict digraph "StepGraph" {
subgraph "cluster CountWords" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords";
label="CountWords";
subgraph "cluster CountWords/Count.PerElement" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords/Count.PerElement";
label="Count.PerElement";
"s3" [label="Init", tooltip="CountWords/Count.PerElement/Init", style=filled, fillcolor=white];
subgraph "cluster CountWords/Count.PerElement/Sum.PerKey" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="CountWords/Count.PerElement/Sum.PerKey";
label="Sum.PerKey";
"s4" [label="GroupByKey/GroupByKeyOnly", tooltip="CountWords/Count.PerElement/Sum.PerKey/GroupByKey/GroupByKeyOnly", style=filled, fillcolor=white];
"s5" [label="GroupedValues", tooltip="CountWords/Count.PerElement/Sum.PerKey/GroupedValues", style=filled, fillcolor=white];
}
}
"s2" [label="ExtractWords", tooltip="CountWords/ExtractWords", style=filled, fillcolor=white];
"s6" [label="FormatCounts", tooltip="CountWords/FormatCounts", style=filled, fillcolor=white];
}
"s1" [label="ReadLines", tooltip="ReadLines", style=filled, fillcolor=white];
"s7" [label="WriteCounts", tooltip="WriteCounts", style=filled, fillcolor=white];

"s1" -> "s2" [taillabel="output", style=solid];
"s2" -> "s3" [taillabel="out", style=solid];
"s3" -> "s4" [taillabel="out", style=solid];
"s4" -> "s5" [taillabel="output", style=solid];
"s5" -> "s6" [taillabel="output", style=solid];
"s6" -> "s7" [taillabel="out", style=solid];
}
""")

  def testExportStepsMissingJobId(self):
    # argparse raises SystemExit rather than ArgumentError for missing
    # required arguments.
    with self.AssertRaisesArgumentErrorMatches(
        'argument JOB_ID: Must be specified.'):
      self.Run('beta dataflow jobs export-steps')

  def testExportStepsMissingJobIdWithFormat(self):
    # argparse raises SystemExit rather than ArgumentError for missing
    # required arguments.
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --export-format=dot (did you mean "
        "'--format'?)"):
      self.Run('beta dataflow jobs export-steps --export-format=dot')

  def testExportStepsNoSuchJob(self):
    self.MockGetJobFailure(JOB_1_ID, view=self.view_all)
    with self.AssertRaisesHttpExceptionRegexp(
        r'Requested entity was not found.'.format(normalize_space=True)):
      self.Run('beta dataflow jobs export-steps ' + JOB_1_ID)

    # Neither stdout nor stderr should contain Http(Exception|Error)
    self.AssertErrNotContains('HttpE')
    self.AssertOutputNotContains('HttpE')

    # Neither stdout nor stderr should contain Http(Exception|Error)
    self.AssertErrNotContains('HttpE')
    self.AssertOutputNotContains('HttpE')


if __name__ == '__main__':
  test_case.main()
