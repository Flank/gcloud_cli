# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Command for creating instances."""
import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import base_classes_resource_registry as resource_registry
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.maintenance_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.compute.maintenance_policies import util as maintenance_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """\
        *{command}* facilitates the creation of Google Compute Engine
        virtual machines. For example, running:

          $ {command} example-instance-1 example-instance-2 example-instance-3 --zone us-central1-a

        will create three instances called `example-instance-1`,
        `example-instance-2`, and `example-instance-3` in the
        `us-central1-a` zone.

        When an instance is in RUNNING state and the system begins to boot,
        the instance creation is considered finished, and the command returns
        with a list of new virtual machines.  Note that you usually cannot log
        into a new instance until it finishes booting. Check the progress of an
        instance using `gcloud compute instances get-serial-port-output`.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES': """\
        To create an instance with the latest ``Red Hat Enterprise Linux
        7'' image available, run:

          $ {command} example-instance --image-family rhel-7 --image-project rhel-cloud --zone us-central1-a
        """,
}


def _CommonArgs(parser,
                release_track,
                support_public_dns,
                support_network_tier,
                enable_regional=False,
                support_local_ssd_size=False,
                enable_kms=False,
                enable_maintenance_policies=False):
  """Register parser args common to all tracks."""
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_regional, enable_kms=enable_kms)
  if release_track in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
    instances_flags.AddCreateDiskArgs(parser, enable_kms=enable_kms)
  if release_track in [base.ReleaseTrack.ALPHA]:
    instances_flags.AddShieldedVMConfigArgs(parser)
  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(
      parser, instances=True,
      support_network_tier=support_network_tier)
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  deprecate_maintenance_policy = release_track in [base.ReleaseTrack.ALPHA]
  instances_flags.AddMaintenancePolicyArgs(parser, deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(
      parser, False,
      extra_scopes_help='However, if neither `--scopes` nor `--no-scopes` are '
                        'specified and the project has no default service '
                        'account, then the instance will be created with no '
                        'scopes.')
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddDeletionProtectionFlag(parser)
  instances_flags.AddPublicPtrArgs(parser, instance=True)
  if support_public_dns:
    instances_flags.AddPublicDnsArgs(parser, instance=True)
  if support_network_tier:
    instances_flags.AddNetworkTierArgs(parser, instance=True)
  if enable_maintenance_policies:
    maintenance_flags.AddResourceMaintenancePolicyArgs(parser, 'added to')

  labels_util.AddCreateLabelsFlags(parser)
  instances_flags.AddMinCpuPlatformArgs(parser, release_track)

  parser.add_argument(
      '--description',
      help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG_FOR_CREATE.AddArgument(
      parser, operation_type='create')

  csek_utils.AddCsekKeyArgs(parser)

  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddFormat(
      resource_registry.RESOURCE_REGISTRY['compute.instances'].list_format)
  parser.display_info.AddCacheUpdater(completers.InstancesCompleter)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = False
  _support_network_tier = False
  _support_public_dns = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.GA,
        support_public_dns=cls._support_public_dns,
        support_network_tier=cls._support_network_tier,
        enable_kms=cls._support_kms,
    )

  def Collection(self):
    return 'compute.instances'

  def GetSourceInstanceTemplate(self, args, resources):
    """Get sourceInstanceTemplate value as required by API."""
    return None

  def BuildShieldedVMConfigMessage(self, messages, args):
    # Set the default values for ShieledVmConfig parameters

    shieldedvm_config_message = None
    if (hasattr(args, 'shielded_vm_secure_boot') or
        hasattr(args, 'shielded_vm_vtpm') or
        hasattr(args, 'shielded_vm_integrity_monitoring')):
      enable_secure_boot = None
      enable_vtpm = None
      enable_integrity_monitoring = None

      if (not args.IsSpecified('shielded_vm_secure_boot') and
          not args.IsSpecified('shielded_vm_vtpm') and
          not args.IsSpecified('shielded_vm_integrity_monitoring')):
        return shieldedvm_config_message
      if args.shielded_vm_secure_boot is not None:
        enable_secure_boot = args.shielded_vm_secure_boot
      if args.shielded_vm_vtpm is not None:
        enable_vtpm = args.shielded_vm_vtpm
      if args.shielded_vm_integrity_monitoring is not None:
        enable_integrity_monitoring = args.shielded_vm_integrity_monitoring
      # compute message fot shielded VM configuration.
      shieldedvm_config_message = instance_utils.CreateShieldedVmConfigMessage(
          messages,
          enable_secure_boot,
          enable_vtpm,
          enable_integrity_monitoring)

    return shieldedvm_config_message

  def _GetNetworkInterfaces(
      self, args, client, holder, instance_refs, skip_defaults):
    return instance_utils.GetNetworkInterfaces(
        args, client, holder, instance_refs, skip_defaults)

  def _GetDiskMessagess(
      self, args, skip_defaults, instance_refs, compute_client,
      resource_parser, create_boot_disk, boot_disk_size_gb, image_uri,
      csek_keys):
    flags_to_check = [
        'disk', 'local_ssd', 'boot_disk_type', 'boot_disk_device_name',
        'boot_disk_auto_delete', 'require_csek_key_create',
    ]
    if self._support_kms:
      flags_to_check.extend([
          'create_disk', 'boot_disk_kms_key', 'boot_disk_kms_project',
          'boot_disk_kms_location', 'boot_disk_kms_keyring',
      ])
    if (skip_defaults and
        not instance_utils.IsAnySpecified(args, *flags_to_check)):
      return [[] for _ in instance_refs]

    # A list of lists where the element at index i contains a list of
    # disk messages that should be set for the instance at index i.
    disks_messages = []

    # A mapping of zone to boot disk references for all existing boot
    # disks that are being attached.
    # TODO(b/36050875): Simplify since resources.Resource is now hashable.
    existing_boot_disks = {}
    for instance_ref in instance_refs:
      persistent_disks, boot_disk_ref = (
          instance_utils.CreatePersistentAttachedDiskMessages(
              resource_parser, compute_client, csek_keys,
              args.disk or [], instance_ref))
      persistent_create_disks = (
          instance_utils.CreatePersistentCreateDiskMessages(
              compute_client,
              resource_parser,
              csek_keys,
              getattr(args, 'create_disk', []),
              instance_ref))
      local_ssds = []
      for x in args.local_ssd or []:
        local_ssds.append(
            instance_utils.CreateLocalSsdMessage(
                resource_parser,
                compute_client.messages,
                x.get('device-name'),
                x.get('interface'),
                x.get('size'),
                instance_ref.zone,
                instance_ref.project)
        )

      if create_boot_disk:
        boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
            compute_client, resource_parser,
            disk_type=args.boot_disk_type,
            disk_device_name=args.boot_disk_device_name,
            disk_auto_delete=args.boot_disk_auto_delete,
            disk_size_gb=boot_disk_size_gb,
            require_csek_key_create=(
                args.require_csek_key_create if csek_keys else None),
            image_uri=image_uri,
            instance_ref=instance_ref,
            csek_keys=csek_keys,
            kms_args=args)
        persistent_disks = [boot_disk] + persistent_disks
      else:
        existing_boot_disks[boot_disk_ref.zone] = boot_disk_ref
      disks_messages.append(persistent_disks + persistent_create_disks +
                            local_ssds)
    return disks_messages

  def _GetProjectToServiceAccountMap(
      self, args, instance_refs, client, skip_defaults):
    project_to_sa = {}
    for instance_ref in instance_refs:
      if instance_ref.project not in project_to_sa:
        scopes = None
        if not args.no_scopes and not args.scopes:
          # User didn't provide any input on scopes. If project has no default
          # service account then we want to create a VM with no scopes
          request = (client.apitools_client.projects,
                     'Get',
                     client.messages.ComputeProjectsGetRequest(
                         project=instance_ref.project))
          errors = []
          result = client.MakeRequests([request], errors)
          if not errors:
            if not result[0].defaultServiceAccount:
              scopes = []
              log.status.Print(
                  'There is no default service account for project {}. '
                  'Instance {} will not have scopes.'.format(
                      instance_ref.project, instance_ref.Name))
        if scopes is None:
          scopes = [] if args.no_scopes else args.scopes

        if args.no_service_account:
          service_account = None
        else:
          service_account = args.service_account
        if (skip_defaults and not args.IsSpecified('scopes') and
            not args.IsSpecified('no_scopes') and
            not args.IsSpecified('service_account') and
            not args.IsSpecified('no_service_account')):
          service_accounts = []
        else:
          service_accounts = instance_utils.CreateServiceAccountMessages(
              messages=client.messages,
              scopes=scopes,
              service_account=service_account)
        project_to_sa[instance_ref.project] = service_accounts
    return project_to_sa

  def _GetGetSoleTenancyHost(self, args, resource_parser, instance_ref):
    sole_tenancy_host_arg = getattr(args, 'sole_tenancy_host', None)
    if sole_tenancy_host_arg:
      sole_tenancy_host_ref = resource_parser.Parse(
          sole_tenancy_host_arg, collection='compute.hosts',
          params={
              'project': instance_ref.project,
              'zone': instance_ref.zone
          })
      return sole_tenancy_host_ref.SelfLink()

  def _GetImageUri(
      self, args, client, create_boot_disk, instance_refs, resource_parser):
    if create_boot_disk:
      image_expander = image_utils.ImageExpander(client, resource_parser)
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_refs[0].project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=False)
      return image_uri

  def _GetNetworkInterfacesWithValidation(
      self, args, resource_parser, compute_client, holder, instance_refs,
      skip_defaults):
    if args.network_interface:
      return instance_utils.CreateNetworkInterfaceMessages(
          resources=resource_parser,
          compute_client=compute_client,
          network_interface_arg=args.network_interface,
          instance_refs=instance_refs,
          support_network_tier=self._support_network_tier)
    else:
      instances_flags.ValidatePublicPtrFlags(args)
      if self._support_public_dns is True:
        instances_flags.ValidatePublicDnsFlags(args)

      return self._GetNetworkInterfaces(
          args, compute_client, holder, instance_refs, skip_defaults)

  def _CreateRequests(
      self, args, instance_refs, compute_client, resource_parser, holder):
    # gcloud creates default values for some fields in Instance resource
    # when no value was specified on command line.
    # When --source-instance-template was specified, defaults are taken from
    # Instance Template and gcloud flags are used to override them - by default
    # fields should not be initialized.
    source_instance_template = self.GetSourceInstanceTemplate(
        args, resource_parser)
    skip_defaults = source_instance_template is not None

    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                  base.ReleaseTrack.BETA]
    csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
    scheduling = instance_utils.GetScheduling(
        args, compute_client, skip_defaults)
    tags = instance_utils.GetTags(args, compute_client)
    labels = instance_utils.GetLabels(args, compute_client)
    metadata = instance_utils.GetMetadata(args, compute_client, skip_defaults)
    boot_disk_size_gb = instance_utils.GetBootDiskSizeGb(args)

    # Compute the shieldedVMConfig message.
    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      shieldedvm_config_message = self.BuildShieldedVMConfigMessage(
          messages=compute_client.messages,
          args=args)

    network_interfaces = self._GetNetworkInterfacesWithValidation(
        args, resource_parser, compute_client, holder, instance_refs,
        skip_defaults)

    machine_type_uris = instance_utils.GetMachineTypeUris(
        args, compute_client, holder, instance_refs, skip_defaults)

    create_boot_disk = not instance_utils.UseExistingBootDisk(args.disk or [])
    image_uri = self._GetImageUri(
        args, compute_client, create_boot_disk, instance_refs, resource_parser)

    disks_messages = self._GetDiskMessagess(
        args, skip_defaults, instance_refs, compute_client, resource_parser,
        create_boot_disk, boot_disk_size_gb, image_uri, csek_keys)

    project_to_sa = self._GetProjectToServiceAccountMap(
        args, instance_refs, compute_client, skip_defaults)

    requests = []
    for instance_ref, machine_type_uri, disks in zip(
        instance_refs, machine_type_uris, disks_messages):

      can_ip_forward = instance_utils.GetCanIpForward(args, skip_defaults)
      guest_accelerators = instance_utils.GetAccelerators(
          args, compute_client, resource_parser, instance_ref)

      instance = compute_client.messages.Instance(
          canIpForward=can_ip_forward,
          deletionProtection=args.deletion_protection,
          description=args.description,
          disks=disks,
          guestAccelerators=guest_accelerators,
          labels=labels,
          machineType=machine_type_uri,
          metadata=metadata,
          minCpuPlatform=args.min_cpu_platform,
          name=instance_ref.Name(),
          networkInterfaces=network_interfaces,
          serviceAccounts=project_to_sa[instance_ref.project],
          scheduling=scheduling,
          tags=tags)

      if self.ReleaseTrack() in [base.ReleaseTrack.ALPHA]:
        instance.shieldedVmConfig = shieldedvm_config_message

      sole_tenancy_host = self._GetGetSoleTenancyHost(
          args, resource_parser, instance_ref)
      if sole_tenancy_host:
        instance.host = sole_tenancy_host

      resource_maintenance_policies = getattr(
          args, 'resource_maintenance_policies', None)
      if resource_maintenance_policies:
        maintenance_policy_ref = maintenance_util.ParseMaintenancePolicy(
            resource_parser,
            args.resource_maintenance_policies,
            project=instance_ref.project,
            region=maintenance_util.GetRegionFromZone(instance_ref.zone))
        instance.maintenancePolicies = [maintenance_policy_ref.SelfLink()]

      request = compute_client.messages.ComputeInstancesInsertRequest(
          instance=instance,
          project=instance_ref.project,
          zone=instance_ref.zone)

      if source_instance_template:
        request.sourceInstanceTemplate = source_instance_template

      requests.append(
          (compute_client.apitools_client.instances, 'Insert', request))
    return requests

  def Run(self, args):
    instances_flags.ValidateDiskFlags(args, enable_kms=self._support_kms)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    instances_flags.ValidateAcceleratorArgs(args)
    if self._support_network_tier:
      instances_flags.ValidateNetworkTierArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resource_parser = holder.resources

    instance_refs = instance_utils.GetInstanceRefs(args, compute_client, holder)

    requests = self._CreateRequests(
        args, instance_refs, compute_client, resource_parser, holder)

    if not args.async:
      # TODO(b/63664449): Replace this with poller + progress tracker.
      try:
        # Using legacy MakeRequests (which also does polling) here until
        # replaced by api_lib.utils.waiter.
        return compute_client.MakeRequests(requests)
      except exceptions.ToolException as e:
        invalid_machine_type_message_regex = (
            r'Invalid value for field \'resource.machineType\': .+. '
            r'Machine type with name \'.+\' does not exist in zone \'.+\'\.')
        if re.search(invalid_machine_type_message_regex, e.message):
          raise exceptions.ToolException(
              e.message +
              '\nUse `gcloud compute machine-types list --zones` to see the '
              'available machine  types.')
        raise

    errors_to_collect = []
    responses = compute_client.BatchRequests(requests, errors_to_collect)
    for r in responses:
      err = getattr(r, 'error', None)
      if err:
        errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    for instance_ref, operation_ref in zip(instance_refs, operation_refs):
      log.status.Print('Instance creation in progress for [{}]: {}'
                       .format(instance_ref.instance, operation_ref.SelfLink()))
    log.status.Print('Use [gcloud compute operations describe URI] command '
                     'to check the status of the operation(s).')
    if not args.IsSpecified('format'):
      # For async output we need a separate format. Since we already printed in
      # the status messages information about operations there is nothing else
      # needs to be printed.
      args.format = 'disable'
    return responses


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = False
  _support_network_tier = False
  _support_public_dns = False

  def _GetNetworkInterfaces(
      self, args, client, holder, instance_refs, skip_defaults):
    return instance_utils.GetNetworkInterfaces(
        args, client, holder, instance_refs, skip_defaults)

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.BETA,
        support_public_dns=cls._support_public_dns,
        support_network_tier=cls._support_network_tier,
        enable_kms=cls._support_kms,
    )
    cls.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)

  def GetSourceInstanceTemplate(self, args, resources):
    if not args.IsSpecified('source_instance_template'):
      return None
    ref = self.SOURCE_INSTANCE_TEMPLATE.ResolveAsResource(args, resources)
    return ref.SelfLink()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create Google Compute Engine virtual machine instances."""

  _support_kms = True
  _support_network_tier = True
  _support_public_dns = True

  def _GetNetworkInterfaces(
      self, args, client, holder, instance_refs, skip_defaults):
    return instance_utils.GetNetworkInterfacesAlpha(
        args, client, holder, instance_refs, skip_defaults)

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--sole-tenancy-host',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.ALPHA,
        support_public_dns=cls._support_public_dns,
        support_network_tier=cls._support_network_tier,
        enable_regional=True,
        support_local_ssd_size=True,
        enable_kms=cls._support_kms,
        enable_maintenance_policies=True)
    CreateAlpha.SOURCE_INSTANCE_TEMPLATE = (
        instances_flags.MakeSourceInstanceTemplateArg())
    CreateAlpha.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)


Create.detailed_help = DETAILED_HELP
