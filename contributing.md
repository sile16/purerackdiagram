
## Feature Wish List
 - Add XL
 - Make data packs a radio button to add like the PCI cards.
 - Add 2 drive add flexibility to be able to create any valid config.
 - Add FlashRecover
 - Add cabling diagrams
 - Instead of passing back an image only, allow to pass back an image plus some json info about port locations the config etc.  And the image can be base64 encoded in there and be interpreted by the js UI.  It would improve error reporting as well as allow more info being returned from the function.
 

## Lambda_package.sh

This is the entry point for the lambda function.  It maily routes to the correct function call under purerackdiagram\flasharray or flashblade , and turns errors into images, it also adds in the ports for an odd reason, probably isn't good to have the ports being added in there but it was the easiest way.

## purerackdiagram\flasharray or flashblade
These generate the images

## UI
This is all the HTML and javascript to create a web interface hosted on github.

## lambda_package.sh / Dockerfile / requirements.txt
This uses a container to package up the lambda funtion and requirements into a zip file.  We need to do this in order to add in Python library dependencies not available on on AWS Lambda.

Running this will create a docker container, add all the files, pull down dependencies and then extract a resulting zip file that can be uploaded to AWS Lambda.

## Update_config.py

This is the source of truth for the configuration information for the different models and where each image lands, the location of each PCI card etc.  I used code blocks to create the different points.   This updates the config file purerackdiagram/config.yaml 

## purerackdiagram/config.yaml 
Do not edit, edit update_config.py and run python3 update_config.py

## test.py

This runs a a bunch of tests locally, without needing to upload to AWS.  It does a hash of each resulting output for each input and compares to test_validation.json to try and prevent regressions if re-factoring code. Then the test output if needing to add more or fix, it creates an output json that when happy you can overwrite the validation json to be the new reference.

## vssx 
Templates for creating visio output files.

## purerackdiagram/png
All the source images used to build final output.

