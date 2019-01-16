FROM lambci/lambda:build-python3.7

WORKDIR /var/task
ENV WORKDIR /var/task

# Make the dir and to install all packages into packages/
COPY requirements.txt "$WORKDIR"
RUN mkdir -p deploy/ && \
    pip install -r requirements.txt -t deploy/ &&
    rm -rf deploy/botocore*

COPY *.py "$WORKDIR/deploy/"
COPY *.ttf "$WORKDIR/deploy/"


# Compress all source codes.

RUN cd deploy && zip -r9 $WORKDIR/lambda.zip .

ENTRYPOINT [ "/bin/bash" ]