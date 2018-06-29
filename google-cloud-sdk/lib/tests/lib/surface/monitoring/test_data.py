# Copyright 2018 Google Inc. All Rights Reserved.
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
"""`gcloud monitoring policies update` command."""

from __future__ import unicode_literals
ALERT_POLICY = """\
{
    "displayName": "Instance health",
    "combiner": "OR",
    "conditions": [
        {
            "displayName": "CPU usage is extremely high",
            "conditionThreshold": {
                "aggregations": [
                    {
                        "alignmentPeriod": "60s",
                        "crossSeriesReducer": "REDUCE_MEAN",
                        "groupByFields": [
                            "project",
                            "resource.label.instance_id",
                            "resource.label.zone"
                        ],
                        "perSeriesAligner": "ALIGN_MEAN"
                    }
                ],
                "comparison": "COMPARISON_GT",
                "duration": "900s",
                "filter": 'metric.type="compute.googleapis.com/instance/cpu/utilization" AND resource.type="gce_instance"',
                "thresholdValue": 0.9,
                "trigger": {
                    "count": 1
                }
            }
        }
    ],
}
"""

CONDITION = """\
{
    "displayName": "cores",
    "conditionThreshold": {
        "aggregations": [
            {
                "alignmentPeriod": "60s",
                "crossSeriesReducer": "REDUCE_SUM",
                "groupByFields": [
                    "project",
                    "resource.label.instance_id",
                    "resource.label.zone"
                ],
                "perSeriesAligner": "ALIGN_SUM"
            }
        ],
        "comparison": "COMPARISON_GT",
        "duration": "900s",
        "filter": 'metric.type="compute.googleapis.com/instance/cpu/reserved_cores"  AND resource.type="gce_instance"',
        "thresholdValue": 500,
        "trigger": {
            "count": 1
        }
    }
}
"""
