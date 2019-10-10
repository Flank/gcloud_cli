## Google Cloud SDK - Release Notes

Copyright 2013-2014 Google LLC. All rights reserved.

### 0.9.41 (2014/12/17)

- Progress Bars.
- Compute Instances start/stop commands.

### 0.9.35 (2014/11/04)

- Added support for Google Container Engine. It is available under the 'gcloud preview container' command group.

### 0.9.33 (2014/09/30)

- Overhaul of 'gcloud sql'
  - Updated the output for all commands.
  - Updated usage for 'gcloud sql ssl-certs create'.

### 0.9.31 (2014/09/02)

- Added support for creating and maintaining Cloud SQL read replica instances.
  - Added *--master-instance-name* property that can be set during replica
    creation to indicate the replication master for the read replica instance.
  - Added *--enable-database-replication*, *--no-enable-database-replication*
    flags that can be used to start, stop replication for the read replica
    instance.
  - Added 'promote-replica' command that promotes a read replica instance into
    a stand-alone Cloud SQL instance.
- Added several new features to the compute component:
  - Implemented new subcommands for interacting with HTTP load balancing:
    - gcloud compute backend-services update
    - gcloud compute url-maps add-host-rule
    - gcloud compute url-maps add-path-matcher
    - gcloud compute url-maps remove-host-rule
    - gcloud compute url-maps remove-path-matcher
    - gcloud compute url-maps set-default-service
  - Added support for automatically generating initial Windows username and
    password when creating a virtual machine instance from a Windowsuimage or a
    disk initializaed from a Windows image.
  - Added a new scope alias for Cloud SQL administration: 'sql-admin'.

### 0.9.27 (2014/06/18)

- Added *--shell* mode to all gcloud commands
  - Type a partial command followed by *--shell* to drop into a sub shell at
    that point in the command tree.
  - e.g.:
    $ gcloud compute --shell
    gcloud compute $ instances list
    gcloud compute $ copy-files ...
- Updated gsutil to 4.3
- Allow installed crcmod to be used by default with gsutil by enabling site
  packages

### 0.9.26 (2014/06/04)

- Windows support for SSH and SCP to Compute VMs
  - The following will now work natively on Windows without the need for cygwin:
    - gcloud compute ssh
    - gcloud compute copy-files
    - gcutil ssh
    - gcutil push
    - gcutil pull
- Support for Java apps in 'gcloud preview app run'
- Updated gsutil to 4.1
- Updated gcutil to 1.16.0
- Updated all App Engine tools to 1.9.6
  - https://code.google.com/p/googleappengine/wiki/SdkReleaseNotes.
  - https://code.google.com/p/googleappengine/wiki/SdkForJavaReleaseNotes


## NOTES

A special note.
