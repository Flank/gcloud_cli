tmpfile=/tmp/exitval$PTYID
for i in 1 2; do
    gcloud meta test --is-interactive
done > /dev/null
echo $? > $tmpfile
