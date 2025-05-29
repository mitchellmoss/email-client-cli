# Claude API Integration Guide for Email Processing

## Table of Contents
1. [Authentication and Setup](#1-authentication-and-setup)
2. [Parsing Complex Email Content](#2-parsing-complex-email-content)
3. [Prompt Engineering Best Practices](#3-prompt-engineering-best-practices)
4. [Rate Limiting and Cost Management](#4-rate-limiting-and-cost-management)
5. [Error Handling](#5-error-handling)
6. [Complete Implementation Examples](#6-complete-implementation-examples)

## 1. Authentication and Setup

### Getting Your API Key
1. Create an account at [anthropic.com](https://www.anthropic.com)
2. Navigate to the API section in your console
3. Generate a new API key
4. Store it securely (never commit to version control)

### Basic Setup (Python)
```python
import os
from anthropic import Anthropic

# Option 1: Environment variable (recommended)
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Option 2: Direct initialization (for testing only)
client = Anthropic(api_key='your-api-key-here')
```

### Installation
```bash
pip install anthropic
```

## 2. Parsing Complex Email Content

### Structured Data Extraction
Claude excels at extracting structured data from unstructured email content. Here's an effective approach:

```python
def parse_email(email_content: str) -> dict:
    prompt = f"""<email>
{email_content}
</email>

Extract the following information and return as JSON:
- sender: email address
- recipient: email address
- subject: subject line
- date: date sent
- sentiment: positive/neutral/negative
- priority: high/medium/low
- key_points: list of main points
- action_items: list of tasks mentioned
- entities: {{persons: [], organizations: [], dates: []}}

Output only valid JSON."""

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1500,
        temperature=0.1,  # Low for consistent parsing
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(response.content[0].text)
```

### Best Model Selection for Email Tasks
- **Claude 3 Haiku**: Fast, economical for simple categorization and summaries
- **Claude 3 Sonnet**: Balanced performance for most email processing tasks
- **Claude 3 Opus**: Complex analysis, sensitive content, multi-language emails

## 3. Prompt Engineering Best Practices

### Use XML Tags for Structure
Claude is fine-tuned to pay attention to XML tags:

```python
prompt = """<email>
{email_content}
</email>

<task>
Generate a professional response acknowledging the main points
</task>

<requirements>
- Maximum 3 sentences
- Maintain professional tone
- Include next steps
</requirements>"""
```

### Effective Email Processing Prompts

#### Email Summarization
```python
prompt = """<email>
{email}
</email>

Create a brief executive summary focusing on:
1. Key decisions needed
2. Action items with owners
3. Critical deadlines

Maximum 3 sentences."""
```

#### Entity Extraction with XML Output
```python
prompt = """<email>
{email}
</email>

Extract entities and structure as XML:
<entities>
  <people>
    <person>
      <name>Name</name>
      <role>Role</role>
      <email>Email</email>
    </person>
  </people>
  <dates>
    <date>
      <value>YYYY-MM-DD</value>
      <context>What the date refers to</context>
    </date>
  </dates>
</entities>"""
```

#### Smart Categorization
```python
categories = ["urgent", "meeting", "project_update", "support", "newsletter"]

prompt = f"""Categorize this email into one of: {', '.join(categories)}

Consider:
- Keywords and phrases
- Sender/recipient relationship
- Action requirements
- Time sensitivity

Output: category|confidence_score"""
```

### Force JSON Output
Use prefilling to skip preambles:

```python
messages = [
    {"role": "user", "content": prompt},
    {"role": "assistant", "content": "{"}  # Forces JSON output
]
```

## 4. Rate Limiting and Cost Management

### Current Pricing (as of 2024)
| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3 Haiku | $0.25 | $1.25 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |

### Rate Limits by Tier
- **Free Tier**: Limited requests per minute
- **Tier 1**: 50 requests/minute, 40,000 input tokens/minute
- **Tier 2+**: Higher limits based on usage
- **Enterprise**: Custom limits available

### Cost Optimization Strategies

#### 1. Prompt Caching (90% discount)
```python
# For repetitive system prompts
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1000,
    system="You are an email processing assistant...",  # This gets cached
    messages=[{"role": "user", "content": email}],
    metadata={"cache_control": {"type": "ephemeral"}}
)
```

#### 2. Batch Processing (50% discount)
```python
# For non-real-time processing
batch_responses = client.batch.create(
    requests=[
        {"custom_id": f"email-{i}", "params": {...}}
        for i, email in enumerate(emails)
    ]
)
```

#### 3. Model Selection by Task
```python
def select_model(task_type: str) -> str:
    model_map = {
        'simple_categorization': 'claude-3-haiku-20240307',
        'standard_parsing': 'claude-3-sonnet-20240229',
        'complex_analysis': 'claude-3-opus-20240229'
    }
    return model_map.get(task_type, 'claude-3-sonnet-20240229')
```

### Cost Tracking Implementation
```python
class CostTracker:
    PRICING = {
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00}
    }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = self.PRICING[model]
        return (input_tokens / 1_000_000 * prices["input"] + 
                output_tokens / 1_000_000 * prices["output"])
```

## 5. Error Handling

### Common Error Types and Handling

```python
from anthropic import APIError, APIConnectionError, RateLimitError
import time

def robust_api_call(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        except RateLimitError as e:
            # Error 429: Rate limit exceeded
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.random()
                logger.warning(f"Rate limit hit, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            else:
                raise
                
        except APIConnectionError as e:
            # Network issues
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                raise
                
        except APIError as e:
            # API errors (400, 401, 403, 500, etc.)
            if hasattr(e, 'status_code'):
                if 400 <= e.status_code < 500:
                    # Client error - don't retry
                    logger.error(f"Client error: {e}")
                    raise
                elif e.status_code >= 500:
                    # Server error - retry
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
            raise
```

### Error Response Patterns
```python
# Common error codes
ERROR_HANDLERS = {
    400: "Invalid request - check your prompt format",
    401: "Authentication failed - check your API key",
    403: "Permission denied - check your account permissions",
    404: "Resource not found",
    429: "Rate limit exceeded - implement backoff",
    500: "Internal server error - retry with backoff",
    529: "Service overloaded - retry later"
}
```

## 6. Complete Implementation Examples

### Example 1: Simple Email Processor
```python
class SimpleEmailProcessor:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    def process(self, email: str) -> dict:
        # Parse email
        parsed = self.parse_email(email)
        
        # Generate summary
        summary = self.summarize_email(email)
        
        # Suggest response if needed
        response = None
        if parsed.get('priority') == 'high':
            response = self.generate_response(email)
        
        return {
            'parsed': parsed,
            'summary': summary,
            'suggested_response': response
        }
```

### Example 2: Batch Email Processor with Rate Limiting
```python
import time
from collections import deque

class BatchEmailProcessor:
    def __init__(self, api_key: str, requests_per_minute: int = 50):
        self.client = Anthropic(api_key=api_key)
        self.rpm_limit = requests_per_minute
        self.request_times = deque()
    
    def process_batch(self, emails: List[str]) -> List[dict]:
        results = []
        
        for email in emails:
            # Rate limiting
            self._enforce_rate_limit()
            
            # Process email
            try:
                result = self._process_single(email)
                results.append({'success': True, 'data': result})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        
        return results
    
    def _enforce_rate_limit(self):
        now = time.time()
        
        # Remove requests older than 60 seconds
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Wait if at limit
        if len(self.request_times) >= self.rpm_limit:
            sleep_time = 60 - (now - self.request_times[0]) + 0.1
            time.sleep(sleep_time)
        
        self.request_times.append(now)
```

### Example 3: Advanced Email Analytics Pipeline
```python
class EmailAnalyticsPipeline:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.cost_tracker = CostTracker()
    
    def analyze_email_thread(self, emails: List[str]) -> dict:
        # 1. Parse all emails
        parsed_emails = [self.parse_email(e) for e in emails]
        
        # 2. Extract thread context
        thread_context = self.extract_thread_context(parsed_emails)
        
        # 3. Identify key decisions and action items
        decisions = self.extract_decisions(emails, thread_context)
        
        # 4. Generate thread summary
        summary = self.generate_thread_summary(emails, decisions)
        
        # 5. Suggest next actions
        next_actions = self.suggest_next_actions(summary, decisions)
        
        return {
            'thread_summary': summary,
            'key_decisions': decisions,
            'next_actions': next_actions,
            'total_cost': self.cost_tracker.get_total()
        }
```

## Key Takeaways

1. **Authentication**: Always use environment variables for API keys
2. **Model Selection**: Choose the right model for your task to optimize cost/performance
3. **Prompt Engineering**: Use XML tags and structured prompts for better results
4. **Error Handling**: Implement robust retry logic with exponential backoff
5. **Cost Management**: Use caching, batching, and appropriate models to minimize costs
6. **Rate Limiting**: Implement proper rate limiting to avoid 429 errors

## Additional Resources

- [Official Anthropic Documentation](https://docs.anthropic.com)
- [Claude API Reference](https://docs.anthropic.com/claude/reference)
- [Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [Community Examples](https://github.com/anthropics/anthropic-cookbook)