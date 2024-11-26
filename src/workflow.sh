#!/bin/bash

set -e

# Check if AWS Account ID, region are passed as arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <aws_account_id> <region> [--complete | <function_name>]"
    exit 1
fi

AWS_ACCOUNT_ID=$1
REGION=$2
IMAGE_NAME="fargate-ecr-pretrained"
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${IMAGE_NAME}"
TAG="latest"

build() {
    echo "Building Docker image..."
    sudo docker build -t ${IMAGE_NAME} .
    echo "Tagging Docker image with ECR repository URI..."
    sudo docker tag ${IMAGE_NAME}:${TAG} ${ECR_REPOSITORY}:${TAG}
}

authenticate_and_create_ecr_repo() {
    echo "Authenticating Docker to ECR..."
    aws ecr get-login-password --region ${REGION} | sudo docker login --username AWS --password-stdin ${ECR_REPOSITORY}
    aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${REGION}
}

push_build_to_ecr() {
    echo "Pushing Docker image to ECR..."
    sudo docker push ${ECR_REPOSITORY}:${TAG}
    echo "Docker image pushed successfully to ${ECR_REPOSITORY}:${TAG}"
}

# Check for --complete flag
if [ "$3" == "--complete" ]; then
    build
    authenticate_and_create_ecr_repo
    push_build_to_ecr
    exit 0
fi


# Check if a function name is passed;
# Call fn if it exists.
FUNCTION_NAME=$3
if [ -n "$FUNCTION_NAME" ]; then
    if declare -f "$FUNCTION_NAME" > /dev/null; then
        "$FUNCTION_NAME"
    else
        echo "Function '$FUNCTION_NAME' not found."
        exit 1
    fi
else
    echo "Please provide a function name or --complete."
    exit 1
fi
