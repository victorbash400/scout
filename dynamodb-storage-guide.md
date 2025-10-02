# Scout DynamoDB Storage for AgentCore (Session-Based)

## Why DynamoDB for Scout?

Perfect choice! DynamoDB is ideal for session-based storage:
- **Fast**: Sub-millisecond response times
- **Serverless**: No infrastructure management
- **Session-based**: TTL (Time To Live) for automatic cleanup
- **Cost-effective**: Pay per request, not storage time
- **AgentCore native**: Built-in integration

## Storage Strategy

### Session-Based Architecture
```
Session ID (Primary Key) → {
  reports: {
    market_report: "markdown content",
    competition_report: "markdown content", 
    price_report: "markdown content",
    legal_report: "markdown content",
    final_report: "markdown content"
  },
  job_data: {...},
  uploaded_files: {...},
  created_at: timestamp,
  ttl: timestamp (expires after 24 hours)
}
```

## Step 1: Create DynamoDB Storage Implementation

Create `scout-backend/storage/dynamodb.py`:

```python
"""
DynamoDB storage implementation for session-based AgentCore deployment
"""
import boto3
import json
import time
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from .base import BaseStorage

class DynamoDBStorage(BaseStorage):
    """DynamoDB storage client for session-based data."""

    def __init__(self, table_name: str = None, region: str = "eu-north-1"):
        self.table_name = table_name or "scout-sessions"
        self.region = region
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)
        
        # Ensure table exists
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create table if it doesn't exist"""
        try:
            self.table.load()
            print(f"✅ DynamoDB table exists: {self.table_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table()

    def _create_table(self):
        """Create the DynamoDB table with TTL"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'session_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'session_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'  # On-demand pricing
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            
            # Enable TTL for automatic cleanup (24 hours)
            self.dynamodb.meta.client.update_time_to_live(
                TableName=self.table_name,
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                }
            )
            
            print(f"✅ Created DynamoDB table: {self.table_name} with TTL")
            
        except ClientError as e:
            raise Exception(f"Failed to create DynamoDB table: {str(e)}")

    def save_file(self, file_name: str, content: bytes, session_id: str = "default") -> str:
        """
        Saves file content to DynamoDB session.
        
        :param file_name: The name of the file
        :param content: The file content in bytes
        :param session_id: Session identifier
        :return: Reference to the saved file
        """
        try:
            # Convert bytes to base64 for storage
            import base64
            content_b64 = base64.b64encode(content).decode('utf-8')
            
            # Update the session with the file
            current_time = int(time.time())
            ttl_time = current_time + (24 * 60 * 60)  # 24 hours from now
            
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET uploaded_files.#fn = :content, created_at = if_not_exists(created_at, :time), ttl = :ttl',
                ExpressionAttributeNames={
                    '#fn': file_name
                },
                ExpressionAttributeValues={
                    ':content': content_b64,
                    ':time': current_time,
                    ':ttl': ttl_time
                }
            )
            
            return f"dynamodb://{self.table_name}/{session_id}/files/{file_name}"
            
        except ClientError as e:
            raise Exception(f"Failed to save file to DynamoDB: {str(e)}")

    def save_report(self, report_name: str, content: str, session_id: str = "default") -> str:
        """
        Saves a report to the session.
        
        :param report_name: Name of the report (e.g., 'market_report')
        :param content: Report content as markdown string
        :param session_id: Session identifier
        :return: Reference to the saved report
        """
        try:
            current_time = int(time.time())
            ttl_time = current_time + (24 * 60 * 60)  # 24 hours from now
            
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET reports.#rn = :content, created_at = if_not_exists(created_at, :time), ttl = :ttl',
                ExpressionAttributeNames={
                    '#rn': report_name
                },
                ExpressionAttributeValues={
                    ':content': content,
                    ':time': current_time,
                    ':ttl': ttl_time
                }
            )
            
            return f"dynamodb://{self.table_name}/{session_id}/reports/{report_name}"
            
        except ClientError as e:
            raise Exception(f"Failed to save report to DynamoDB: {str(e)}")

    def get_report(self, report_name: str, session_id: str = "default") -> Optional[str]:
        """Get a specific report from the session"""
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            
            if 'Item' in response:
                reports = response['Item'].get('reports', {})
                return reports.get(report_name)
            
            return None
            
        except ClientError as e:
            raise Exception(f"Failed to get report from DynamoDB: {str(e)}")

    def get_all_reports(self, session_id: str = "default") -> Dict[str, str]:
        """Get all reports for a session"""
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            
            if 'Item' in response:
                return response['Item'].get('reports', {})
            
            return {}
            
        except ClientError as e:
            raise Exception(f"Failed to get reports from DynamoDB: {str(e)}")

    def save_job_data(self, job_id: str, data: Dict[str, Any]) -> None:
        """
        Saves structured job data to DynamoDB.
        Note: job_id becomes the session_id for session-based storage
        """
        try:
            current_time = int(time.time())
            ttl_time = current_time + (24 * 60 * 60)  # 24 hours from now
            
            self.table.update_item(
                Key={'session_id': job_id},
                UpdateExpression='SET job_data = :data, created_at = if_not_exists(created_at, :time), ttl = :ttl',
                ExpressionAttributeValues={
                    ':data': data,
                    ':time': current_time,
                    ':ttl': ttl_time
                }
            )
            
        except ClientError as e:
            raise Exception(f"Failed to save job data to DynamoDB: {str(e)}")

    def load_job_data(self, job_id: str) -> Dict[str, Any]:
        """
        Loads structured job data from DynamoDB.
        """
        try:
            response = self.table.get_item(Key={'session_id': job_id})
            
            if 'Item' in response:
                return response['Item'].get('job_data', {})
            
            return {}
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return {}
            raise Exception(f"Failed to load job data from DynamoDB: {str(e)}")

    def cleanup_expired_sessions(self):
        """Manual cleanup (TTL handles this automatically)"""
        # TTL handles automatic cleanup, but you can implement manual cleanup if needed
        pass
```

## Step 2: Update Agent Report Functions

Update your agent report saving functions to use DynamoDB:

```python
# In each agent file (market_agent.py, competition_agent.py, etc.)
@tool
def save_market_report(content: str, session_id: str = "default") -> str:
    """
    Saves the market report to DynamoDB session storage.
    """
    try:
        from storage.dynamodb import DynamoDBStorage
        storage = DynamoDBStorage()
        
        # Save to DynamoDB session
        report_ref = storage.save_report("market_report", content, session_id)
        
        # Add to shared storage for synthesis (using session-based reference)
        with storage_lock:
            report_filepaths_storage.append(f"session:{session_id}:market_report")
        
        # Send progress event
        event_queue.put_nowait(StreamEvent(
            eventType="tool_call",
            payload={
                "tool_name": "save_market_report",
                "tool_input": {"session_id": session_id},
                "display_message": "Market report saved to session."
            }
        ))
        
        return f"Market report saved successfully to session {session_id}"
        
    except Exception as e:
        return f"Error saving market report: {str(e)}"
```

## Step 3: Update Settings for DynamoDB

Update `scout-backend/config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Storage Configuration
    storage_backend: str = "dynamodb"  # Change to "dynamodb"
    dynamodb_table_name: str = Field(default="scout-sessions", env="DYNAMODB_TABLE_NAME")
    dynamodb_region: str = Field(default="eu-north-1", env="DYNAMODB_REGION")
    session_ttl_hours: int = Field(default=24, env="SESSION_TTL_HOURS")
```

## Step 4: Update AgentCore Configuration

Add DynamoDB permissions to your `agentcore.yaml`:

```yaml
spec:
  # ... existing config ...
  environment:
    AWS_REGION: eu-north-1
    BEDROCK_MODEL_ID: arn:aws:bedrock:eu-north-1:547688237843:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0
    STORAGE_BACKEND: dynamodb
    DYNAMODB_TABLE_NAME: scout-sessions
    DYNAMODB_REGION: eu-north-1
    SESSION_TTL_HOURS: 24
  permissions:
    - service: dynamodb
      actions:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:UpdateItem
        - dynamodb:DeleteItem
        - dynamodb:Query
        - dynamodb:Scan
      resources:
        - arn:aws:dynamodb:eu-north-1:547688237843:table/scout-sessions
```

## Step 5: Create DynamoDB Table

```bash
# Create the DynamoDB table
aws dynamodb create-table \
    --region eu-north-1 \
    --table-name scout-sessions \
    --attribute-definitions AttributeName=session_id,AttributeType=S \
    --key-schema AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Enable TTL for automatic cleanup after 24 hours
aws dynamodb update-time-to-live \
    --region eu-north-1 \
    --table-name scout-sessions \
    --time-to-live-specification Enabled=true,AttributeName=ttl
```

## Step 6: Update API Endpoints for Session Management

Update your FastAPI endpoints to handle sessions:

```python
# In main.py
from uuid import uuid4

@app.post("/api/session/create")
async def create_session():
    """Create a new session for the user"""
    session_id = str(uuid4())
    return {"session_id": session_id}

@app.get("/api/session/{session_id}/reports")
async def get_session_reports(session_id: str):
    """Get all reports for a session"""
    try:
        from storage.dynamodb import DynamoDBStorage
        storage = DynamoDBStorage()
        reports = storage.get_all_reports(session_id)
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Benefits of DynamoDB for Scout

1. **Session-Based**: Perfect for temporary market research sessions
2. **Auto-Cleanup**: TTL automatically deletes old sessions (24 hours)
3. **Fast**: Sub-millisecond response times for report retrieval
4. **Cost-Effective**: Pay only for requests, not storage time
5. **Serverless**: No infrastructure management
6. **AgentCore Native**: Built-in integration and permissions

## Session Flow

1. User starts → Create session ID
2. Upload business plan → Store in session
3. Agents generate reports → Store in session with TTL
4. User downloads reports → Retrieve from session
5. After 24 hours → Automatic cleanup via TTL

This approach is much better for your use case than persistent S3 storage!