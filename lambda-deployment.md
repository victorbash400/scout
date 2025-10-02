# Scout AWS Lambda Deployment (Alternative to AgentCore)

## If AgentCore isn't available, deploy using Lambda + API Gateway

### Step 1: Install Serverless Framework

```bash
npm install -g serverless
npm install serverless-python-requirements
```

### Step 2: Create serverless.yml

```yaml
service: scout-market-intelligence

provider:
  name: aws
  runtime: python3.11
  region: eu-north-1
  timeout: 300
  memorySize: 2048
  environment:
    AWS_REGION: ${self:provider.region}
    BEDROCK_MODEL_ID: arn:aws:bedrock:eu-north-1:547688237843:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0
    TAVILY_API_KEY: ${ssm:/scout/tavily-api-key}
    GOOGLE_PLACES_API_KEY: ${ssm:/scout/google-places-key}
  iamRoleStatements:
    - Effect: Allow
      Action:
        - bedrock:InvokeModel
        - bedrock:InvokeModelWithResponseStream
      Resource: "*"

functions:
  api:
    handler: main.handler
    events:
      - http:
          path: /{proxy+}
          method: ANY
          cors: true
      - http:
          path: /
          method: ANY
          cors: true

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
```

### Step 3: Create Lambda Handler

```python
# lambda_handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

### Step 4: Deploy

```bash
cd scout-backend
serverless deploy
```