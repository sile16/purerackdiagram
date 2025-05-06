# Lambda Setup Guide for PureRackDiagram

This guide explains how to set up your Lambda functions with the correct environment variables to ensure metrics are properly sent to CloudWatch.

## Required Environment Variables

Each Lambda function needs the following environment variables to function correctly:

| Environment Variable | Description | Required Value |
|----------------------|-------------|---------------|
| `ENVIRONMENT` | Specifies which namespace metrics should go to | `Production` or `Staging` |
| `AWS_REGION` | Specifies which AWS region to send metrics to | `us-east-1` (must match dashboard region) |

## Configuring Environment Variables in AWS Console

1. Open the AWS Lambda console
2. Select your Lambda function
3. Click on the "Configuration" tab
4. Find "Environment variables" in the left sidebar
5. Add or update the variables listed above

## CloudWatch Dashboard

The CloudWatch dashboard is configured to show metrics from two separate namespaces:
- `PureRackDiagram-Production`: For the production Lambda function
- `PureRackDiagram-Staging`: For the staging/testing Lambda function

Make sure your Lambda functions are configured with the correct `ENVIRONMENT` value to separate metrics properly.

## Verifying Metrics

After setting up the Lambda function, you can verify metrics are being sent correctly by:

1. Open CloudWatch in the AWS Console
2. Go to "Metrics" → "All metrics"
3. Look for the `PureRackDiagram-Production` or `PureRackDiagram-Staging` namespace
4. You should see metrics for:
   - `SuccessCount`
   - `TotalErrorCount`
   - `ExceptionCount` (with dimensions for exception types)
   - `ModelType` and `Generation` (for FlashArray specific metrics)
   - `ArrayType` (for tracking FlashArray vs FlashBlade usage)

If you don't see these metrics, check the CloudWatch logs for your Lambda function to see if there are any errors related to emitting metrics.