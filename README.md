# AI-Powered-Meeting-Analyst
  This project is a fully automated, serverless pipeline on AWS that transcribes and analyzes meeting recordings. When a video or audio file of a meeting is uploaded to an S3 bucket, this system automatically      generates a text transcript, identifies key decisions, summarizes main topics using Amazon Bedrock, and stores the results in DynamoDB. A notification is sent via SNS upon completion.

# Features
  - Automated Transcription: Automatically transcribes uploaded audio/video files using Amazon Transcribe with speaker diarization (identifying different speakers).
  - AI-Powered Analysis: Leverages Amazon Bedrock (with models like Anthropic's Claude) to extract key decisions and summarize main topics from the transcript.
  - Serverless & Event-Driven: Built entirely on serverless services (Lambda, S3, SQS, DynamoDB), ensuring scalability, resilience, and cost-effectiveness. You only pay for what you use.
  - Asynchronous & Resilient: Uses an SQS queue to decouple file uploads from processing, making the system robust against failures.
  - Real-time Notifications: Sends an email notification via SNS as soon as the analysis is complete.

# Architecture
  -The architecture is event-driven and uses two Lambda functions to handle the long-running nature of transcription jobs reliably.  
   (You can create a diagram using a tool like diagrams.net or CloudCraft and embed it here.)

# Workflow:

  1. A user uploads a video/audio file (e.g., .mp4, .mp3) to the Input S3 Bucket.
  2. The S3 upload triggers an event notification, sending a message to an SQS Queue.
  3. The SQS message triggers the Start Transcription Lambda (start-transcription-lambda).
  4. This Lambda function starts a transcription job with Amazon Transcribe, specifying the input file location and the Output S3 Bucket for the results.
  5. Amazon Transcribe processes the file and saves the resulting transcript (.json) to the Output S3 Bucket.
  6. The new .json file in the output bucket triggers the Process Results Lambda (process-results-lambda).
  7. This second Lambda function reads the transcript, sends it to Amazon Bedrock for analysis, stores the transcript and AI summary in DynamoDB, and publishes a completion message to an SNS Topic.
  8. The SNS Topic sends a final notification email to all subscribed users.

# Technology Stack
  - Compute: AWS Lambda
  - Storage: Amazon S3 (for media files and transcripts), Amazon DynamoDB (for storing final results)
  - AI/ML: Amazon Transcribe, Amazon Bedrock
  - Messaging & Notifications: Amazon SQS, Amazon SNS
  - Identity & Access Management: AWS IAM
  - Language: Python 3.11 with Boto3 SDK

# Project Setup and Deployment
  Follow these steps to deploy the entire pipeline in your AWS account.

# Prerequisites
  - An AWS Account.
  - AWS CLI configured with appropriate permissions.
  - Python 3.11+ and Boto3 installed locally (if you plan to use local scripts).
  - You have enabled access to foundation models (e.g., Anthropic Claude) in Amazon Bedrock.

# Step 1: Create AWS Resources
  1. S3 Buckets:
  2. your-meeting-videos-bucket: For uploading media files.
  3. your-meeting-transcripts-bucket: To store the JSON output from Amazon Transcribe.
  4. SQS Queue:
  6. Create a Standard queue named transcription-job-queue.
  7. DynamoDB Table:
  8. Table Name: MeetingAnalysis
  9. Partition Key: meetingId (Type: String)
  10. SNS Topic:
  11. Create a Standard topic named TranscriptionReady.
  12. Create an email subscription to this topic using your email address and confirm it via the link sent to your inbox.

# Step 2: Create IAM Roles
  1. Create two IAM roles for the Lambda functions.
  2. Role: start-transcription-lambda-role
  3. Trusted Entity: Lambda
  4. Permissions (AWS Managed Policies):
  5. AWSLambdaSQSQueueExecutionRole
  6. AmazonS3ReadOnlyAccess
  7. AmazonTranscribeFullAccess
  8. Role: process-results-lambda-role
  9. Trusted Entity: Lambda
  10. Permissions (AWS Managed Policies):
  11. AWSLambdaBasicExecutionRole
  12. AmazonS3ReadOnlyAccess
  13. AmazonDynamoDBFullAccess
  14. AmazonSNSFullAccess
  15. Inline Policy for Bedrock: Create an inline policy named BedrockInvokePolicy with the given JSON:


# Step 3: Create Lambda Functions
  1. Function #1: start-transcription-lambda
  2. Runtime: Python 3.11
  3. Role: Use the existing start-transcription-lambda-role.
  4. Code: Use the code from the lambda-start-transcription/ directory.
  5. Environment Variables:
  6. OUTPUT_BUCKET: your-meeting-transcripts-bucket
  7. Function #2: process-results-lambda
  8. Runtime: Python 3.11
  9. Role: Use the existing process-results-lambda-role.
  10. Code: Use the code from the lambda-process-results/ directory.
  11. General Configuration: Increase the timeout to at least 1 minute.
  12. Environment Variables:
  13. DYNAMODB_TABLE: MeetingAnalysis
  14. SNS_TOPIC_ARN: The ARN of your TranscriptionReady SNS topic.

# Step 4: Configure Event Triggers
  1. S3 to SQS:
  2. In your input S3 bucket (your-meeting-videos-bucket), go to Properties > Event notifications.
  3. Create a notification that triggers on s3:ObjectCreated:Put.
  4. Set the destination to the transcription-job-queue SQS queue.
  5. SQS to Lambda #1:
  6. In the start-transcription-lambda function configuration, add a trigger.
  7. Select SQS as the source and choose the transcription-job-queue.
  8. S3 to Lambda #2:
  9. In the process-results-lambda function configuration, add a trigger.
  10. Select S3 as the source and choose the your-meeting-transcripts-bucket.
  11. Set the event type to s3:ObjectCreated:*.

Important: Set the Suffix filter to .json to ensure it only triggers on Transcribe output files.

# Usage
  - Navigate to your input S3 bucket (your-meeting-videos-bucket) in the AWS console.
  - Upload a meeting recording file (e.g., .mp4, .wav, .mp3).
  - The pipeline will start automatically. Processing time depends on the length of the recording.
  - Once complete, you will receive an email notification.
  - Check the MeetingAnalysis DynamoDB table to view the full transcript and the AI-generated summary.
