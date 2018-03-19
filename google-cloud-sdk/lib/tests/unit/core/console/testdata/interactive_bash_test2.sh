#! /bin/bash
tmpfile=/tmp/exitval$PTYID
for i in 1 2; do
    # make sure compound commands run from scripts are not interactive
    gcloud meta test --is-interactive
done > /dev/null
echo $? > $tmpfile
