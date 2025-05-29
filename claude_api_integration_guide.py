"""
Claude API Integration Guide for Email Processing
================================================

This guide demonstrates how to integrate Claude API for intelligent email processing,
including authentication, parsing, prompt engineering, rate limiting, and error handling.
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import anthropic
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. AUTHENTICATION AND SETUP
# ============================================================================

class ClaudeEmailProcessor:
    """Main class for processing emails with Claude API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client
        
        Args:
            api_key: Your Anthropic API key. If not provided, will look for
                    ANTHROPIC_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        self.client = Anthropic(api_key=self.api_key)
        
        # Rate limiting configuration
        self.requests_per_minute = 50  # Adjust based on your tier
        self.last_request_time = 0
        self.request_count = 0
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# ============================================================================
# 2. EMAIL PARSING WITH CLAUDE
# ============================================================================

@dataclass
class EmailData:
    """Structured email data extracted by Claude"""
    sender: str
    recipient: str
    subject: str
    date: str
    sentiment: str
    priority: str
    category: str
    key_points: List[str]
    action_items: List[str]
    entities: Dict[str, List[str]]  # persons, organizations, locations, etc.
    attachments: List[str]
    summary: str


class EmailParser:
    """Parse and extract structured data from emails using Claude"""
    
    def __init__(self, claude_processor: ClaudeEmailProcessor):
        self.processor = claude_processor
    
    def parse_email(self, raw_email: str) -> EmailData:
        """
        Parse raw email content and extract structured data
        
        Args:
            raw_email: Raw email content including headers and body
            
        Returns:
            EmailData object with extracted information
        """
        prompt = self._create_parsing_prompt(raw_email)
        
        try:
            response = self.processor.client.messages.create(
                model="claude-3-sonnet-20240229",  # Good balance of speed and quality
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent parsing
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the JSON response
            content = response.content[0].text
            parsed_data = json.loads(content)
            
            return EmailData(**parsed_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            raise
    
    def _create_parsing_prompt(self, raw_email: str) -> str:
        """Create a structured prompt for email parsing"""
        return f"""<email>
{raw_email}
</email>

Please analyze this email and extract the following information in JSON format:
- sender: Email address of the sender
- recipient: Email address of the recipient
- subject: Email subject line
- date: Date when the email was sent
- sentiment: Overall sentiment (positive/neutral/negative)
- priority: Priority level (high/medium/low)
- category: Email category (business/personal/newsletter/spam/etc.)
- key_points: List of main points discussed
- action_items: List of action items or tasks mentioned
- entities: Dictionary with lists of mentioned persons, organizations, locations
- attachments: List of attachment filenames if any
- summary: Brief 2-3 sentence summary

Output only valid JSON without any additional text or formatting."""
    
    def _get_system_prompt(self) -> str:
        """System prompt for email parsing"""
        return """You are an expert email analysis assistant. Your task is to parse emails 
and extract structured information. Always output valid JSON format. Be accurate and 
concise. Extract only information that is explicitly present in the email."""


# ============================================================================
# 3. PROMPT ENGINEERING FOR EMAIL PROCESSING
# ============================================================================

class EmailPromptTemplates:
    """Collection of optimized prompts for different email processing tasks"""
    
    @staticmethod
    def summarization_prompt(email: str, style: str = "executive") -> str:
        """Generate email summary with different styles"""
        styles = {
            "executive": "Create a brief executive summary focusing on key decisions and actions",
            "technical": "Provide a technical summary highlighting implementation details",
            "casual": "Write a friendly, conversational summary of the main points"
        }
        
        return f"""<email>
{email}
</email>

Task: {styles.get(style, styles['executive'])}

Requirements:
- Maximum 3 sentences
- Focus on actionable information
- Maintain professional tone
- Include any deadlines mentioned"""
    
    @staticmethod
    def reply_generation_prompt(email: str, context: str = "", tone: str = "professional") -> str:
        """Generate email reply suggestions"""
        return f"""<original_email>
{email}
</original_email>

<context>
{context if context else "No additional context provided"}
</context>

Generate a {tone} email reply that:
1. Acknowledges the main points
2. Provides clear responses to any questions
3. Suggests next steps if applicable
4. Maintains appropriate tone and professionalism

Output format:
- Subject line suggestion
- Email body
- Any follow-up actions needed"""
    
    @staticmethod
    def classification_prompt(email: str, categories: List[str]) -> str:
        """Classify email into predefined categories"""
        return f"""<email>
{email}
</email>

<categories>
{json.dumps(categories)}
</categories>

Classify this email into one or more of the provided categories.
Also provide a confidence score (0-1) for each classification.

Output as JSON:
{{
    "primary_category": "category_name",
    "all_categories": [
        {{"category": "name", "confidence": 0.95}},
        ...
    ],
    "reasoning": "Brief explanation of classification"
}}"""
    
    @staticmethod
    def entity_extraction_prompt(email: str) -> str:
        """Extract entities and important information"""
        return f"""<email>
{email}
</email>

Extract all important entities and information:

1. People (names, roles, email addresses)
2. Organizations (companies, departments)
3. Dates and times (meetings, deadlines)
4. Locations (addresses, meeting rooms)
5. Financial information (amounts, budgets)
6. Product/Project names
7. URLs and links
8. Phone numbers

Use XML tags to structure the output:
<entities>
  <people>
    <person>
      <name>John Doe</name>
      <role>Project Manager</role>
      <email>john@example.com</email>
    </person>
  </people>
  <dates>
    <date>
      <value>2024-03-15</value>
      <context>Project deadline</context>
    </date>
  </dates>
  <!-- Continue for other entity types -->
</entities>"""


# ============================================================================
# 4. RATE LIMITING AND COST MANAGEMENT
# ============================================================================

class RateLimiter:
    """Handle rate limiting for Claude API calls"""
    
    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
    
    def wait_if_needed(self):
        """Wait if necessary to avoid hitting rate limits"""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            # Calculate wait time
            oldest_request = self.request_times[0]
            wait_time = 60 - (now - oldest_request) + 0.1  # Add small buffer
            
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
        
        self.request_times.append(time.time())


class CostCalculator:
    """Calculate and track API usage costs"""
    
    # Pricing as of 2024 (in USD per million tokens)
    # Update these based on current Anthropic pricing
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }
    
    def __init__(self):
        self.usage_history: List[Dict[str, Any]] = []
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a single API call"""
        if model not in self.PRICING:
            logger.warning(f"Unknown model {model}, using Sonnet pricing")
            model = "claude-3-sonnet-20240229"
        
        input_cost = (input_tokens / 1_000_000) * self.PRICING[model]["input"]
        output_cost = (output_tokens / 1_000_000) * self.PRICING[model]["output"]
        
        total_cost = input_cost + output_cost
        
        # Track usage
        self.usage_history.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_cost
        })
        
        return total_cost
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of API usage and costs"""
        if not self.usage_history:
            return {"total_cost": 0, "total_calls": 0, "total_tokens": 0}
        
        total_cost = sum(u["cost"] for u in self.usage_history)
        total_input = sum(u["input_tokens"] for u in self.usage_history)
        total_output = sum(u["output_tokens"] for u in self.usage_history)
        
        return {
            "total_cost": round(total_cost, 4),
            "total_calls": len(self.usage_history),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "average_cost_per_call": round(total_cost / len(self.usage_history), 4)
        }


# ============================================================================
# 5. ERROR HANDLING AND RETRY LOGIC
# ============================================================================

class RetryHandler:
    """Handle retries with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
                
            except RateLimitError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = self.base_delay * (2 ** attempt) + (time.time() % 1)
                    logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached for rate limit error")
                    
            except APIConnectionError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached for connection error")
                    
            except APIError as e:
                last_exception = e
                # Don't retry for client errors (4xx)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500:
                    logger.error(f"Client error (not retrying): {e}")
                    raise
                    
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached for API error")
        
        # If we've exhausted retries, raise the last exception
        if last_exception:
            raise last_exception


# ============================================================================
# 6. COMPLETE EMAIL PROCESSING PIPELINE
# ============================================================================

class EmailProcessingPipeline:
    """Complete pipeline for processing emails with Claude"""
    
    def __init__(self, api_key: str):
        self.processor = ClaudeEmailProcessor(api_key)
        self.parser = EmailParser(self.processor)
        self.rate_limiter = RateLimiter()
        self.cost_calculator = CostCalculator()
        self.retry_handler = RetryHandler()
    
    def process_email_batch(self, emails: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of emails with rate limiting and error handling"""
        results = []
        
        for i, email in enumerate(emails):
            try:
                logger.info(f"Processing email {i+1}/{len(emails)}")
                
                # Rate limiting
                self.rate_limiter.wait_if_needed()
                
                # Process with retry logic
                result = self.retry_handler.execute_with_retry(
                    self._process_single_email, email
                )
                
                results.append({
                    "success": True,
                    "data": result,
                    "error": None
                })
                
            except Exception as e:
                logger.error(f"Failed to process email {i+1}: {str(e)}")
                results.append({
                    "success": False,
                    "data": None,
                    "error": str(e)
                })
        
        # Log usage summary
        usage = self.cost_calculator.get_usage_summary()
        logger.info(f"Batch processing complete. Total cost: ${usage['total_cost']:.4f}")
        
        return results
    
    def _process_single_email(self, email: str) -> Dict[str, Any]:
        """Process a single email"""
        # Parse email
        parsed = self.parser.parse_email(email)
        
        # Generate summary
        summary_response = self.processor.client.messages.create(
            model="claude-3-haiku-20240307",  # Use cheaper model for summaries
            max_tokens=500,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": EmailPromptTemplates.summarization_prompt(email)
            }]
        )
        
        # Track costs
        # Note: You'll need to get actual token counts from the response
        # This is a simplified example
        self.cost_calculator.calculate_cost(
            "claude-3-haiku-20240307",
            input_tokens=1000,  # Get from response.usage
            output_tokens=200   # Get from response.usage
        )
        
        return {
            "parsed_data": parsed.__dict__,
            "summary": summary_response.content[0].text,
            "processed_at": datetime.now().isoformat()
        }


# ============================================================================
# 7. USAGE EXAMPLES
# ============================================================================

def example_basic_usage():
    """Basic usage example"""
    # Initialize processor
    processor = ClaudeEmailProcessor(api_key="your-api-key-here")
    
    # Simple email analysis
    email_content = """
    From: john.doe@company.com
    To: jane.smith@company.com
    Subject: Project Update - Q4 Deliverables
    Date: Mon, 15 Jan 2024 10:30:00 -0500
    
    Hi Jane,
    
    I wanted to update you on our Q4 project deliverables. We've completed 
    the initial design phase and are moving into development. The team has 
    identified a few technical challenges that might impact our timeline.
    
    Key points:
    - Design phase: 100% complete
    - Development: 30% complete
    - Testing scheduled for Feb 15
    - Go-live date: March 1 (at risk)
    
    Action items:
    1. Schedule technical review meeting this week
    2. Update stakeholders on timeline risks
    3. Prepare contingency plan
    
    Let me know if you need any additional information.
    
    Best regards,
    John
    """
    
    try:
        response = processor.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"Analyze this email and extract key information:\n\n{email_content}"
            }]
        )
        
        print("Analysis:", response.content[0].text)
        
    except Exception as e:
        logger.error(f"Error processing email: {e}")


def example_advanced_pipeline():
    """Advanced pipeline example with batch processing"""
    # Initialize pipeline
    pipeline = EmailProcessingPipeline(api_key="your-api-key-here")
    
    # Sample emails
    emails = [
        "Email 1 content...",
        "Email 2 content...",
        "Email 3 content..."
    ]
    
    # Process batch
    results = pipeline.process_email_batch(emails)
    
    # Analyze results
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"Processed {successful} emails successfully, {failed} failed")
    
    # Get cost summary
    usage = pipeline.cost_calculator.get_usage_summary()
    print(f"Total cost: ${usage['total_cost']:.4f}")
    print(f"Average cost per email: ${usage['average_cost_per_call']:.4f}")


def example_streaming_response():
    """Example with streaming responses for real-time processing"""
    processor = ClaudeEmailProcessor(api_key="your-api-key-here")
    
    email = "Your email content here..."
    
    try:
        # Create streaming response
        with processor.client.messages.stream(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"Analyze this email in real-time:\n\n{email}"
            }]
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                
    except Exception as e:
        logger.error(f"Streaming error: {e}")


if __name__ == "__main__":
    # Example usage
    print("Claude API Email Processing Examples")
    print("=" * 50)
    
    # Note: Set your API key as environment variable or pass directly
    # export ANTHROPIC_API_KEY='your-key-here'
    
    # Uncomment to run examples:
    # example_basic_usage()
    # example_advanced_pipeline()
    # example_streaming_response()