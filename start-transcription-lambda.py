import json
import boto3
import os
import urllib.parse
import uuid

# Initialize AWS clients
transcribe_client = boto3.client('transcribe')
output_bucket = os.environ['OUTPUT_BUCKET']

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    for record in event['Records']:
        # The actual message is a JSON string in the 'body'
        message_body = json.loads(record['body'])

        # S3 event messages have a 'Records' list, even if it's just one
        s3_record = message_body['Records'][0]

        bucket_name = s3_record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(s3_record['s3']['object']['key'])

        # Generate a unique job name
        job_name = f"transcription-job-{uuid.uuid4()}"
        media_uri = f"s3://{bucket_name}/{object_key}"

        print(f"Starting transcription job: {job_name} for {media_uri}")

        try:
            response = transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode='en-US',  # Change if needed
                Media={'MediaFileUri': media_uri},
                OutputBucketName=output_bucket,
                OutputKey=f'{job_name}.json', # Save output with job name
                Settings={
                    'ShowSpeakerLabels': True, # To identify different speakers
                    'MaxSpeakerLabels': 2 # Adjust as needed
                }
            )
            print("Transcription job started successfully:", response)

        except Exception as e:
            print(f"Error starting transcription job: {e}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully started transcription jobs.')
    }
