"module"

# QUEUE ARNs are output when creating the SQS queues via CloudFormation
QUEUE_1_URL: str = "https://sqs.us-east-2.amazonaws.com/891242332196/MyFirstQueue"
QUEUE_2_URL: str = "https://sqs.us-east-2.amazonaws.com/891242332196/MySecondQueue"
QUEUE_1_ARN: str = "arn:aws:sqs:us-east-2:891242332196:MyFirstQueue"
QUEUE_2_ARN: str = "arn:aws:sqs:us-east-2:891242332196:MySecondQueue"

# Role ARN for EventBridge Scheduler to invoke targets
# TODO: Need to add to CloudFormation stack
EXECUTION_ROLE_ARN: str = (
    "arn:aws:iam::891242332196:role/service-role/Amazon_EventBridge_Scheduler_SQS_32652038ad"
)
