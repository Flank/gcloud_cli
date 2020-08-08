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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')


def _GetMessagesForApi(api):
  if api == 'alpha':
    return alpha_messages
  elif api == 'beta':
    return beta_messages
  elif api == 'v1':
    return messages
  else:
    assert False


_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakeInstanceGroups(msgs, api, scope_type='zone', scope_name='zone-1'):
  """Creates a set of instanceGroup messages for the given API version.

  Args:
    msgs: The compute messages API handle.
    api: The API version for which to create the instances.
    scope_type: The type of scope (zone or region)
    scope_name: The name of scope (eg. us-central1-a)

  Returns:
    A list of message objects representing instanceGroups.
  """
  prefix = '{0}/{1}'.format(_COMPUTE_PATH, api)
  groups = [
      msgs.InstanceGroup(
          name='group-1',
          selfLink=(
              '{0}/projects/my-project/{1}/{2}/instanceGroups/group-1'.format(
                  prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          description='Test instance group',
          fingerprint=b'123',
          namedPorts=[
              msgs.NamedPort(name='serv-1', port=1111),
              msgs.NamedPort(name='serv-2', port=2222),
              msgs.NamedPort(name='serv-3', port=3333)
          ],
          size=0,
      ),
      msgs.InstanceGroup(
          name='group-2',
          selfLink=(
              '{0}/projects/my-project/{1}/{2}/instanceGroups/group-2'.format(
                  prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:55:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/default'),
          namedPorts=[msgs.NamedPort(name='serv-1', port=1111)],
          size=3,
      ),
      msgs.InstanceGroup(
          name='group-3',
          selfLink=(
              '{0}/projects/my-project/{1}/{2}/instanceGroups/group-3'.format(
                  prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:56:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/network-1'),
          size=10,
      ),
      msgs.InstanceGroup(
          name='group-4',
          selfLink=(
              '{0}/projects/my-project/{1}/{2}/instanceGroups/group-4'.format(
                  prefix, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:56:10.636-07:00',
          network=(prefix + '/projects/my-project/global/networks/network-1'),
          size=1,
      ),
  ]
  for group in groups:
    setattr(
        group, scope_type,
        '{0}/projects/my-project/{1}/{2}'.format(prefix, scope_type + 's',
                                                 scope_name))
  return groups


def MakeInstancesInInstanceGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-1'),
          status=(msgs.InstanceWithNamedPorts.StatusValueValuesEnum.RUNNING)),
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-2'),
          status=(msgs.InstanceWithNamedPorts.StatusValueValuesEnum.RUNNING)),
      msgs.InstanceWithNamedPorts(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-3'),
          status=(msgs.InstanceWithNamedPorts.StatusValueValuesEnum.STOPPED)),
  ]


def MakeLastAttemptErrors(msgs, error_spec):
  return msgs.ManagedInstanceLastAttempt(
      errors=msgs.ManagedInstanceLastAttempt.ErrorsValue(errors=[
          msgs.ManagedInstanceLastAttempt.ErrorsValue.ErrorsValueListEntry(
              code=err[0], message=err[1]) for err in error_spec
      ]))


def MakeInstancesInManagedInstanceGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-1'),
          instanceStatus=(
              msgs.ManagedInstance.InstanceStatusValueValuesEnum.RUNNING),
          instanceHealth=[
              msgs.ManagedInstanceInstanceHealth(
                  detailedHealthState=msgs.ManagedInstanceInstanceHealth
                  .DetailedHealthStateValueValuesEnum.HEALTHY)
          ],
          currentAction=(
              msgs.ManagedInstance.CurrentActionValueValuesEnum.NONE),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-1', name='xxx')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-2'),
          instanceStatus=(
              msgs.ManagedInstance.InstanceStatusValueValuesEnum.STOPPED),
          instanceHealth=[
              msgs.ManagedInstanceInstanceHealth(
                  detailedHealthState=msgs.ManagedInstanceInstanceHealth
                  .DetailedHealthStateValueValuesEnum.UNHEALTHY)
          ],
          currentAction=(
              msgs.ManagedInstance.CurrentActionValueValuesEnum.RECREATING),
          version=msgs.ManagedInstanceVersion(instanceTemplate='template-1')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-3'),
          instanceStatus=(
              msgs.ManagedInstance.InstanceStatusValueValuesEnum.RUNNING),
          instanceHealth=[
              msgs.ManagedInstanceInstanceHealth(
                  detailedHealthState=msgs.ManagedInstanceInstanceHealth
                  .DetailedHealthStateValueValuesEnum.TIMEOUT)
          ],
          currentAction=(
              msgs.ManagedInstance.CurrentActionValueValuesEnum.DELETING),
          version=msgs.ManagedInstanceVersion(
              instanceTemplate='template-2', name='yyy')),
      msgs.ManagedInstance(
          instance=(prefix +
                    'projects/my-project/zones/central2-a/instances/inst-4'),
          currentAction=(
              msgs.ManagedInstance.CurrentActionValueValuesEnum.CREATING),
          version=msgs.ManagedInstanceVersion(instanceTemplate='template-3'),
          lastAttempt=MakeLastAttemptErrors(
              msgs, [('CONDITION_NOT_MET', 'True is not False'),
                     ('QUOTA_EXCEEDED', 'Limit is 5')])),
  ]


def MakeErrorsInManagedInstanceGroup(msgs, api):
  prefix = '{0}/{1}/'.format(_COMPUTE_PATH, api)
  return [
      msgs.InstanceManagedByIgmError(
          instanceActionDetails=msgs
          .InstanceManagedByIgmErrorInstanceActionDetails(
              instance=prefix +
              'projects/my-project/zones/central2-a/instances/inst-1',
              action=msgs.InstanceManagedByIgmErrorInstanceActionDetails
              .ActionValueValuesEnum.CREATING,
              version=msgs.ManagedInstanceVersion(
                  instanceTemplate='template-1', name='xxx')),
          error=msgs.InstanceManagedByIgmErrorManagedInstanceError(
              code='foo', message='bar'),
          timestamp='2013-09-06T17:54:10.636-07:00'),
      msgs.InstanceManagedByIgmError(
          instanceActionDetails=msgs
          .InstanceManagedByIgmErrorInstanceActionDetails(
              instance=prefix +
              'projects/my-project/zones/central2-a/instances/inst-2',
              action=msgs.InstanceManagedByIgmErrorInstanceActionDetails
              .ActionValueValuesEnum.DELETING,
              version=msgs.ManagedInstanceVersion(
                  instanceTemplate='template-1', name='xxx')),
          error=msgs.InstanceManagedByIgmErrorManagedInstanceError(
              code='foo', message='bar'),
          timestamp='2013-09-06T17:54:10.636-07:00'),
  ]


def MakeInstanceGroupManagersWithActions(api,
                                         current_actions_count,
                                         scope_type='zone',
                                         scope_name='zone-1',
                                         actions_state='creating',
                                         is_stable=False,
                                         version_target_reached=None):
  """Creates instance group manages with current actions tests resources."""
  if current_actions_count and is_stable:
    raise Exception('Cannot create stable IGM with current actions.')

  used_messages = _GetMessagesForApi(api)
  igm = used_messages.InstanceGroupManager(
      name='group-1',
      selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                'my-project/{1}/{2}/instanceGroupManagers/group-1'.format(
                    api, scope_type + 's', scope_name)),
      creationTimestamp='2013-09-06T17:54:10.636-07:00',
      zone=('https://compute.googleapis.com/compute/{0}/'
            'projects/my-project/zones/zone-1'.format(api)),
      baseInstanceName='test-instance-name-1',
      description='Test description.',
      fingerprint=b'1234',
      instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                     'my-project/{1}/{2}/instanceGroups/group-1'.format(
                         api, scope_type + 's', scope_name)),
      instanceTemplate=(
          'https://compute.googleapis.com/compute/{0}/projects/'
          'my-project/global/instanceTemplates/template-1'.format(api)),
      targetPools=[],
      targetSize=1)
  igm.currentActions = used_messages.InstanceGroupManagerActionsSummary(**{
      actions_state: current_actions_count,
      'none': (10 - current_actions_count)
  })
  igm.status = used_messages.InstanceGroupManagerStatus(isStable=is_stable)
  if version_target_reached is not None:
    igm.status.versionTarget = (
        used_messages.InstanceGroupManagerStatusVersionTarget(
            isReached=version_target_reached))

  setattr(
      igm, scope_type,
      'https://compute.googleapis.com/compute/{0}/projects/my-project/{1}/{2}'
      .format(api, scope_type + 's', scope_name))
  return igm


def MakeInstanceGroupManagers(api, scope_name='zone-1', scope_type='zone'):
  """Creates instance group manages tests resources."""

  used_messages = _GetMessagesForApi(api)
  group_managers = [
      used_messages.InstanceGroupManager(
          name='group-1',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-1'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          baseInstanceName='test-instance-name-1',
          description='Test description.',
          fingerprint=b'1234',
          instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-1'.format(
                             api, scope_type + 's', scope_name)),
          instanceTemplate=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/global/instanceTemplates/template-1'.format(api)),
          targetPools=[],
          targetSize=1,
      ),
      used_messages.InstanceGroupManager(
          name='group-2',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-2'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-2',
          description='Test description.',
          fingerprint=b'12345',
          instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-2'.format(
                             api, scope_type + 's', scope_name)),
          instanceTemplate=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/global/instanceTemplates/template-2'.format(api)),
          targetPools=[],
          targetSize=10,
      ),
      used_messages.InstanceGroupManager(
          name='group-3',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-3'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2012-01-01T00:00:00.001+11:00',
          baseInstanceName='test-instance-name-3',
          description='Test description.',
          fingerprint=b'12346',
          instanceGroup=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/zones/zone-1/instanceGroups/group-3'.format(api)),
          instanceTemplate=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/global/instanceTemplates/template-2'.format(api)),
          targetPools=[],
          targetSize=1,
      ),
  ]
  for group_manager in group_managers:
    setattr(
        group_manager, scope_type, 'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/{1}/{2}'.format(api, scope_type + 's', scope_name))
  return group_managers


def MakeInstanceGroupManagersWithVersions(api,
                                          scope_name='zone-1',
                                          scope_type='zone'):
  """Creates instance group manager test resources."""

  used_messages = _GetMessagesForApi(api)
  group_managers = [
      used_messages.InstanceGroupManager(
          name='group-1',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-1'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2013-09-06T17:54:10.636-07:00',
          baseInstanceName='test-instance-name-1',
          description='Test description.',
          fingerprint=b'1234',
          instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-1'.format(
                             api, scope_type + 's', scope_name)),
          instanceTemplate=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/global/instanceTemplates/template-1'.format(api)),
          targetPools=[],
          targetSize=1,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{0}/'
                      'projects/my-project/global/'
                      'instanceTemplates/template-1'.format(api)),),
          ],
      ),
      used_messages.InstanceGroupManager(
          name='group-2',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-2'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-2',
          description='Test description.',
          fingerprint=b'12345',
          instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-2'.format(
                             api, scope_type + 's', scope_name)),
          targetPools=[],
          targetSize=10,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{0}/'
                      'projects/my-project/global/'
                      'instanceTemplates/template-1'.format(api)),
                  targetSize=used_messages.FixedOrPercent(percent=60)),
              used_messages.InstanceGroupManagerVersion(
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{0}/'
                      'projects/my-project/global/'
                      'instanceTemplates/template-2'.format(api)),),
          ],
      ),
      used_messages.InstanceGroupManager(
          name='group-3',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-3'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2012-01-01T00:00:00.001+11:00',
          baseInstanceName='test-instance-name-3',
          description='Test description.',
          fingerprint=b'12346',
          instanceGroup=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/zones/zone-1/instanceGroups/group-3'.format(api)),
          instanceTemplate=(
              'https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/global/instanceTemplates/template-2'.format(api)),
          targetPools=[],
          targetSize=1,
      ),
      used_messages.InstanceGroupManager(
          name='group-4',
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/instanceGroupManagers/group-4'.format(
                        api, scope_type + 's', scope_name)),
          creationTimestamp='2014-12-31T23:59:59.999-11:00',
          baseInstanceName='test-instance-name-4',
          description='Test description.',
          fingerprint=b'12347',
          instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/{1}/{2}/instanceGroups/group-4'.format(
                             api, scope_type + 's', scope_name)),
          targetPools=[],
          targetSize=10,
          versions=[
              used_messages.InstanceGroupManagerVersion(
                  name='some-tag',
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{0}/'
                      'projects/my-project/global/'
                      'instanceTemplates/template-1'.format(api)),
                  targetSize=used_messages.FixedOrPercent(percent=60),
              ),
              used_messages.InstanceGroupManagerVersion(
                  name='other-tag',
                  instanceTemplate=(
                      'https://compute.googleapis.com/compute/{0}/'
                      'projects/my-project/global/'
                      'instanceTemplates/template-1'.format(api)),
              ),
          ],
      ),
  ]
  for group_manager in group_managers:
    setattr(
        group_manager, scope_type, 'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/{1}/{2}'.format(api, scope_type + 's', scope_name))
  return group_managers


def MakeStatefulInstanceGroupManager(api,
                                     scope_name='zone-1',
                                     scope_type='zone'):
  """Creates sample stateful IGM test resource."""

  used_messages = _GetMessagesForApi(api)
  auto_delete_never = used_messages.StatefulPolicyPreservedStateDiskDevice\
    .AutoDeleteValueValuesEnum.NEVER
  return used_messages.InstanceGroupManager(
      name='group-stateful-1',
      selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                'my-project/{1}/{2}/instanceGroupManagers/group-stateful-1'
                .format(api, scope_type + 's', scope_name)),
      creationTimestamp='2019-05-10T17:54:10.636-07:00',
      baseInstanceName='test-instance-name-1',
      description='Test description.',
      fingerprint=b'1234',
      instanceGroup=('https://compute.googleapis.com/compute/{0}/projects/'
                     'my-project/{1}/{2}/instanceGroups/group-stateful-1'
                     .format(api, scope_type + 's', scope_name)),
      instanceTemplate=('https://compute.googleapis.com/compute/{0}/projects/'
                        'my-project/global/instanceTemplates/template-1'
                        .format(api)),
      statefulPolicy=used_messages.StatefulPolicy(
          preservedState=(
              used_messages.StatefulPolicyPreservedState(
                  disks=used_messages.StatefulPolicyPreservedState.DisksValue(
                      additionalProperties=[
                          used_messages.StatefulPolicyPreservedState \
                            .DisksValue.AdditionalProperty(
                                key='disk-1',
                                value=used_messages.\
                                StatefulPolicyPreservedStateDiskDevice(
                                    autoDelete=auto_delete_never))
                      ]
                  )
              )
          )
      ),
      targetPools=[],
      targetSize=1,
      versions=[
          used_messages.InstanceGroupManagerVersion(
              instanceTemplate=('https://compute.googleapis.com/compute/{0}/'
                                'projects/my-project/global/'
                                'instanceTemplates/template-1'.format(api)),
          ),
      ],
  )


def MakeAutoscalers(api, scope_name='zone-1', scope_type='zone'):
  """Makes Autoscaler test resources."""
  used_messages = _GetMessagesForApi(api)
  autoscalers = [
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(
              coolDownPeriodSec=60,
              cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
                  utilizationTarget=0.8,),
              customMetricUtilizations=[
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/seconds',
                      utilizationTarget=60.,
                      utilizationTargetType=(
                          used_messages.AutoscalingPolicyCustomMetricUtilization
                          .UtilizationTargetTypeValueValuesEnum.DELTA_PER_MINUTE
                      ),
                  ),
              ],
              loadBalancingUtilization=(
                  used_messages.AutoscalingPolicyLoadBalancingUtilization)(
                      utilizationTarget=0.9,),
              maxNumReplicas=10,
              minNumReplicas=2,
          ),
          name='autoscaler-1',
          target=('https://compute.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-1'.format(
                      api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-1'.format(
                        api, scope_type + 's', scope_name)),
      ),
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(maxNumReplicas=10,),
          name='autoscaler-2',
          target=('https://compute.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-2'.format(
                      api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-2'.format(
                        api, scope_type + 's', scope_name)),
      ),
      used_messages.Autoscaler(
          autoscalingPolicy=used_messages.AutoscalingPolicy(
              customMetricUtilizations=[
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/seconds',
                      utilizationTarget=60.,
                      utilizationTargetType=(
                          used_messages.AutoscalingPolicyCustomMetricUtilization
                          .UtilizationTargetTypeValueValuesEnum.DELTA_PER_MINUTE
                      ),
                  ),
                  used_messages.AutoscalingPolicyCustomMetricUtilization(
                      metric='custom.cloudmonitoring.googleapis.com/my-metric',
                      utilizationTarget=30568.,
                      utilizationTargetType=(
                          used_messages.AutoscalingPolicyCustomMetricUtilization
                          .UtilizationTargetTypeValueValuesEnum.DELTA_PER_MINUTE
                      ),
                  ),
              ],
              maxNumReplicas=10,
              minNumReplicas=2,
          ),
          name='autoscaler-3',
          target=('https://compute.googleapis.com/compute/{0}/projects/'
                  'my-project/{1}/{2}/instanceGroupManagers/group-3'.format(
                      api, scope_type + 's', scope_name)),
          creationTimestamp='Two days ago',
          id=1,
          selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/{1}/{2}/autoscalers/autoscaler-3'.format(
                        api, scope_type + 's', scope_name)),
      ),
  ]
  for autoscaler in autoscalers:
    setattr(
        autoscaler, scope_type, 'https://compute.googleapis.com/compute/{0}/'
        'projects/my-project/{1}/{2}'.format(api, scope_type + 's', scope_name))
  return autoscalers


def MakeAutoscalerOk(api, scope_name='zone-1', scope_type='zone'):
  """Create autoscaler resource with OK status."""

  used_messages = _GetMessagesForApi(api)
  autoscaler = used_messages.Autoscaler(
      autoscalingPolicy=used_messages.AutoscalingPolicy(
          coolDownPeriodSec=60,
          cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
              utilizationTarget=0.8,),
          maxNumReplicas=10,
          minNumReplicas=2,
      ),
      name='autoscaler-1',
      target=('https://compute.googleapis.com/compute/{0}/projects/'
              'my-project/{1}/{2}/instanceGroupManagers/group-1'.format(
                  api, scope_type + 's', scope_name)),
      creationTimestamp='Two days ago',
      status=used_messages.Autoscaler.StatusValueValuesEnum.ACTIVE,
      id=2,
      selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                'my-project/{1}/{2}/autoscalers/autoscaler-1'.format(
                    api, scope_type + 's', scope_name)),
  )
  setattr(
      autoscaler, scope_type,
      'https://compute.googleapis.com/compute/{0}/projects/my-project/{1}/{2}'
      .format(api, scope_type + 's', scope_name))
  return autoscaler


def MakeAutoscalerWithError(api):
  used_messages = _GetMessagesForApi(api)
  return used_messages.Autoscaler(
      autoscalingPolicy=used_messages.AutoscalingPolicy(
          coolDownPeriodSec=60,
          cpuUtilization=used_messages.AutoscalingPolicyCpuUtilization(
              utilizationTarget=0.8,),
          maxNumReplicas=10,
          minNumReplicas=2,
      ),
      name='autoscaler-2',
      target=(
          'https://compute.googleapis.com/compute/{0}/projects/'
          'my-project/zones/zone-1/instanceGroupManagers/group-2'.format(api)),
      zone=('https://compute.googleapis.com/compute/{0}/'
            'projects/my-project/zones/zone-1'.format(api)),
      creationTimestamp='Two days ago',
      status=used_messages.Autoscaler.StatusValueValuesEnum.ERROR,
      id=2,
      selfLink=('https://compute.googleapis.com/compute/{0}/projects/'
                'my-project/zones/zone-1/autoscalers/autoscaler-2'.format(api)),
  )
