#!/bin/bash

BASE_REQUEST="http://127.0.0.1:8000/v1"
API_KEY="mykeyishere"
MODEL="Qwen/Qwen3-Coder-30B-A3B-Instruct-GGU"
USER_QUESTION=$1

if [[ ${USER_QUESTION} == "" ]]
then
   echo "Usage:  $0 \"ask a question to the LLM...\""
   exit 255
fi

OUTPUT=$(curl -sS ${BASE_REQUEST}/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"${MODEL}\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"You are a helpful assistant.\"},
      {\"role\": \"user\", \"content\": \"${USER_QUESTION}\"}
    ]
  }")

echo $OUTPUT | jq

