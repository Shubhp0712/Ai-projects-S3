import boto3
import json

# Initialize Bedrock client
client = boto3.client(
    service_name="bedrock-runtime",
    region_name="eu-north-1"
)

# Nova Pro inference profile ARN
MODEL_ID = "arn:aws:bedrock:eu-north-1:054522427975:inference-profile/eu.amazon.nova-pro-v1:0"

def ask_bedrock(user_input):
    body = {
        "messages": [
            {"role": "user", "content": [{"text": user_input}]}
        ]
    }

    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body)
    )

    response_body = json.loads(response["body"].read())
    output_text = response_body["output"]["message"]["content"][0]["text"]

    return output_text


def chatbot():
    print("💬 Bedrock Nova Pro Chatbot (type 'exit' to quit)\n")
    while True:
        user_input = input("You> ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot> BYE from chatbot")
            break

        try:
            reply = ask_bedrock(user_input)
            print(f"Chatbot> {reply}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    chatbot()
