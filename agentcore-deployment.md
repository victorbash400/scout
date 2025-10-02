# Scout AgentCore Deployment Guide

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **AgentCore CLI** installed: `pip install agentcore-cli`
3. **Docker** for containerization
4. **Your API keys** (Tavily, Google Places) stored in AWS Secrets Manager

## Step 1: Prepare Your Agent Configuration

Create `agentcore.yaml` in your project root:

```yaml
apiVersion: agentcore.aws/v1
kind: Agent
metadata:
  name: scout-market-intelligence
  description: "AI-powered market intelligence platform"
spec:
  runtime: python3.11
  handler: main:app
  memory: 2048
  timeout: 300
  environment:
    AWS_REGION: eu-north-1
    BEDROCK_MODEL_ID: arn:aws:bedrock:eu-north-1:547688237843:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0
  secrets:
    - name: TAVILY_API_KEY
      secretArn: arn:aws:secretsmanager:eu-north-1:547688237843:secret:scout/tavily-api-key
    - name: GOOGLE_PLACES_API_KEY
      secretArn: arn:aws:secretsmanager:eu-north-1:547688237843:secret:scout/google-places-key
    - name: AWS_ACCESS_KEY_ID
      secretArn: arn:aws:secretsmanager:eu-north-1:547688237843:secret:scout/aws-access-key
    - name: AWS_SECRET_ACCESS_KEY
      secretArn: arn:aws:secretsmanager:eu-north-1:547688237843:secret:scout/aws-secret-key
  agents:
    - name: planner
      type: orchestrator
      model: bedrock:eu.anthropic.claude-sonnet-4-20250514-v1:0
    - name: market-research
      type: specialist
      model: bedrock:eu.anthropic.claude-sonnet-4-20250514-v1:0
    - name: competition-analysis
      type: specialist
      model: bedrock:eu.anthropic.claude-sonnet-4-20250514-v1:0
    - name: pricing-intelligence
      type: specialist
      model: bedrock:eu.anthropic.claude-sonnet-4-20250514-v1:0
    - name: legal-compliance
      type: specialist
      model: bedrock:eu.anthropic.claude-sonnet-4-20250514-v1:0
  tools:
    - name: tavily-search
      type: web-search
    - name: google-places
      type: location-api
    - name: pdf-generator
      type: document-generation
```

## Step 2: Create Dockerfile for AgentCore

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY scout-backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY scout-backend/ .

# Expose port for AgentCore
EXPOSE 8080

# AgentCore expects the app to run on port 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Step 3: Store Secrets in AWS Secrets Manager

```bash
# Store your API keys securely in eu-north-1 region
aws secretsmanager create-secret \
    --region eu-north-1 \
    --name "scout/tavily-api-key" \
    --secret-string "your-tavily-api-key"

aws secretsmanager create-secret \
    --region eu-north-1 \
    --name "scout/google-places-key" \
    --secret-string "your-google-places-api-key"

aws secretsmanager create-secret \
    --region eu-north-1 \
    --name "scout/aws-access-key" \
    --secret-string "your-aws-access-key-id"

aws secretsmanager create-secret \
    --region eu-north-1 \
    --name "scout/aws-secret-key" \
    --secret-string "your-aws-secret-access-key"
```

## Step 4: Deploy to AgentCore

```bash
# Initialize AgentCore project
agentcore init scout-market-intelligence

# Build and deploy
agentcore deploy --config agentcore.yaml

# Monitor deployment
agentcore status scout-market-intelligence
```

## Step 5: Configure Frontend for AgentCore

Update your frontend to use the AgentCore endpoint:

```typescript
// In your React app
const AGENTCORE_ENDPOINT = 'https://your-agent-id.agentcore.aws.amazon.com'

// Update API calls
const response = await fetch(`${AGENTCORE_ENDPOINT}/api/chat/stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${agentcoreToken}`
  },
  body: JSON.stringify({ message, mode })
})
```