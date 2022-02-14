#!/bin/bash
#create delplyment package:

python3 update_config.py
rm lambda.zip
docker build -t purerack .
imagename=`docker create purerack`
echo Created Image: $imagename
docker cp $imagename:/var/task/lambda.zip .