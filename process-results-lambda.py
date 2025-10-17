import json
import boto3
import os
import urllib.parse

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1') # Bedrock is in specific regions
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Get environment variables
table_name = os.environ['DYNAMODB_TABLE']
sns_topic_arn = os.environ['SNS_TOPIC_ARN']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    # Get the S3 bucket and key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    # Get the meetingId from the file name (e.g., 'my-video.mp4.json' -> 'my-video.mp4')
    meeting_id = object_key.replace(".json", "") 

    try:
        # 1. Get transcript from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        transcript_data = json.loads(response['Body'].read().decode('utf-8'))
        transcript_text = transcript_data['results']['transcripts'][0]['transcript']

        # 2. Call Amazon Bedrock for analysis
        prompt = f"""
        Human: Based on the following meeting transcript, please identify the key decisions made and summarize the main topics discussed.
        Provide your answer in a JSON format with two keys: "key_decisions" (a list of strings) and "main_topics" (a list of strings).
        Do not include any text outside of the JSON object.

        Transcript:
        {transcript_text}

        Assistant:
        """

        bedrock_body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 2000,
            "temperature": 0.1,
        })

        modelId = 'anthropic.claude-v2' # Or another model like claude-3-sonnet-20240229-v1:0
        accept = 'application/json'
        contentType = 'application/json'

        bedrock_response = bedrock_client.invoke_model(
            body=bedrock_body, 
            modelId=modelId, 
            accept=accept, 
            contentType=contentType
        )

        response_body = json.loads(bedrock_response.get('body').read())
        analysis_result = json.loads(response_body.get('completion'))

        # 3. Store results in DynamoDB
        table.put_item(
            Item={
                'meetingId': meeting_id,
                'transcript': transcript_text,
                'key_decisions': analysis_result.get('key_decisions', []),
                'main_topics': analysis_result.get('main_topics', [])
            }
        )

        # 4. Send SNS notification
        message = f"Analysis for meeting '{meeting_id}' is complete. Results are stored in the '{table_name}' DynamoDB table."
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject='Meeting Analysis Complete'
        )

        return {'statusCode': 200, 'body': json.dumps('Processing complete!')}

    except Exception as e:
        print(f"Error processing transcript: {e}")
        raise e
