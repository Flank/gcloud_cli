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
"""Constants used for AI Platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


ALPHA_VERSION = 'ALPHA'
BETA_VERSION = 'BETA'
GA_VERSION = 'GA'
AI_PLATFORM_API_VERSION = {
    GA_VERSION: 'v1',
    BETA_VERSION: 'v1beta1',
    ALPHA_VERSION: 'v1alpha1'
}
AI_PLATFORM_MESSAGE_PREFIX = {
    GA_VERSION: 'GoogleCloudAiplatformV1',
    BETA_VERSION: 'GoogleCloudAiplatformV1beta1',
    ALPHA_VERSION: 'GoogleCloudAiplatformV1alpha1'
}
AI_PLATFORM_API_NAME = 'aiplatform'

SUPPORTED_REGION = ['us-central1', 'europe-west4', 'asia-east1']

OPERATION_CREATION_DISPLAY_MESSAGE = """\
The {verb} operation [{name}] was submitted successfully.

You may view the status of your operation with the command

  $ gcloud beta ai operations describe {id} {sub_commands}\
"""

CUSTOM_JOB_CREATION_DISPLAY_MESSAGE = """\
Custom Job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ gcloud alpha ai custom-jobs describe {id}

Job State: {state}\
"""

CUSTOM_JOB_CANCEL_DISPLAY_MESSAGE = """\
Request to cancel custom job [{id}] has been sent

You may view the status of your job with the command

  $ gcloud alpha ai custom-jobs describe {id}
"""

DEFAULT_OPERATION_COLLECTION = 'aiplatform.projects.locations.operations'

CUSTOM_JOB_COLLECTION = 'aiplatform.projects.locations.customJobs'

ENDPOINTS_COLLECTION = 'aiplatform.projects.locations.endpoints'

INDEX_ENDPOINTS_COLLECTION = 'aiplatform.projects.locations.indexEndpoints'
INDEXES_COLLECTION = 'aiplatform.projects.locations.indexes'

TENSORBOARDS_COLLECTION = 'aiplatform.projects.locations.tensorboards'

TENSORBOARD_EXPERIMENTS_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments'

TENSORBOARD_RUNS_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments.runs'

TENSORBOARD_TIME_SERIES_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments.runs.timeSeries'

HPTUNING_JOB_CREATION_DISPLAY_MESSAGE = """\
Hyperparameter tuning job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ gcloud alpha ai hp-tuning-jobs describe {id}

Job State: {state}\
"""

HPTUNING_JOB_CANCEL_DISPLAY_MESSAGE = """\
Request to cancel hyperparameter tuning job [{id}] has been sent

You may view the status of your job with the command

  $ gcloud alpha ai hp-tuning-jobs describe {id}
"""

HPTUNING_JOB_COLLECTION = 'aiplatform.projects.locations.hyperparameterTuningJobs'

OP_AUTOSCALING_METRIC_NAME_MAPPER = {
    'cpu-usage':
        'aiplatform.googleapis.com/prediction/online/cpu/utilization',
    'gpu-duty-cycle':
        'aiplatform.googleapis.com/prediction/online/accelerator/duty_cycle',
}
