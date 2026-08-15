import os

import boto3
from dotenv import load_dotenv


# Load secrets from the local .env file
load_dotenv()


# Make sure the key exists without printing it
if not os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
    raise ValueError("Bedrock API key was not found in .env")


# Connect to Amazon Bedrock
client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)


# Send a very small test prompt
response = client.converse(
    modelId="amazon.nova-lite-v1:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "Reply with exactly this sentence: "
                        "ScopeLedger connected to Amazon Bedrock."
                    )
                }
            ],
        }
    ],
    inferenceConfig={
        "maxTokens": 50,
        "temperature": 0,
    },
)


# Read the model's answer
answer = response["output"]["message"]["content"][0]["text"]

print(answer)