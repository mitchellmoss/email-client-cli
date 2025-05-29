"""
Practical Email Processor with Claude API
========================================

A production-ready example of using Claude API for email processing
with all essential features: parsing, categorization, and response generation.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import anthropic
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailCategory(Enum):
    """Email categories for classification"""
    URGENT = "urgent"
    MEETING = "meeting"
    PROJECT_UPDATE = "project_update"
    SUPPORT = "support"
    NEWSLETTER = "newsletter"
    PERSONAL = "personal"
    SPAM = "spam"
    OTHER = "other"


class EmailProcessor:
    """
    Main class for processing emails with Claude API
    
    Features:
    - Smart email parsing and data extraction
    - Automatic categorization
    - Response generation
    - Cost tracking
    - Error handling with retries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from parameter or environment"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.total_cost = 0.0
        
        # Model selection based on task complexity
        self.models = {
            'fast': 'claude-3-haiku-20240307',      # For simple tasks
            'balanced': 'claude-3-sonnet-20240229',  # For most tasks
            'powerful': 'claude-3-opus-20240229'     # For complex tasks
        }
    
    def process_email(self, email_content: str) -> Dict:
        """
        Process email and return structured data
        
        Args:
            email_content: Raw email text
            
        Returns:
            Dictionary with parsed data, category, priority, and suggested actions
        """
        try:
            # Step 1: Parse and extract data
            parsed_data = self._parse_email(email_content)
            
            # Step 2: Categorize and prioritize
            category, priority = self._categorize_email(email_content, parsed_data)
            
            # Step 3: Generate insights and suggestions
            insights = self._generate_insights(email_content, parsed_data, category)
            
            # Step 4: Create response suggestions if needed
            response_suggestions = None
            if category in [EmailCategory.URGENT, EmailCategory.MEETING, EmailCategory.SUPPORT]:
                response_suggestions = self._generate_response(email_content, category)
            
            return {
                'parsed_data': parsed_data,
                'category': category.value,
                'priority': priority,
                'insights': insights,
                'response_suggestions': response_suggestions,
                'processing_cost': self._get_last_request_cost()
            }
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            raise
    
    def _parse_email(self, email_content: str) -> Dict:
        """Extract structured data from email"""
        prompt = f"""<email>
{email_content}
</email>

Extract the following information from this email and return as JSON:
{{
    "from": "sender email",
    "to": ["recipient emails"],
    "subject": "email subject",
    "date": "date sent",
    "key_points": ["main points discussed"],
    "action_items": ["tasks or actions mentioned"],
    "deadlines": ["dates/deadlines mentioned"],
    "people_mentioned": ["names of people"],
    "attachments": ["attachment names"],
    "sentiment": "positive/neutral/negative",
    "urgency_indicators": ["phrases indicating urgency"]
}}

Return ONLY the JSON object, no other text."""
        
        response = self._make_api_call(
            prompt=prompt,
            model=self.models['balanced'],
            max_tokens=1500,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response}")
            return {}
    
    def _categorize_email(self, email_content: str, parsed_data: Dict) -> Tuple[EmailCategory, str]:
        """Categorize email and determine priority"""
        # Quick heuristic-based categorization first
        if any(word in email_content.lower() for word in ['urgent', 'asap', 'immediately']):
            return EmailCategory.URGENT, 'high'
        
        prompt = f"""Based on this email content and extracted data, categorize it:

Email content: {email_content[:500]}...

Extracted data:
- Subject: {parsed_data.get('subject', 'N/A')}
- Key points: {', '.join(parsed_data.get('key_points', [])[:3])}
- Action items: {', '.join(parsed_data.get('action_items', [])[:3])}

Categories: urgent, meeting, project_update, support, newsletter, personal, spam, other

Respond with: category|priority
Where priority is: high, medium, or low

Example: meeting|high"""
        
        response = self._make_api_call(
            prompt=prompt,
            model=self.models['fast'],  # Use fast model for simple classification
            max_tokens=20,
            temperature=0.1
        )
        
        try:
            category_str, priority = response.strip().split('|')
            category = EmailCategory(category_str)
            return category, priority
        except:
            return EmailCategory.OTHER, 'medium'
    
    def _generate_insights(self, email_content: str, parsed_data: Dict, category: EmailCategory) -> Dict:
        """Generate actionable insights from email"""
        prompt = f"""Analyze this {category.value} email and provide insights:

Email summary:
- Key points: {', '.join(parsed_data.get('key_points', [])[:5])}
- Action items: {', '.join(parsed_data.get('action_items', [])[:5])}
- Deadlines: {', '.join(parsed_data.get('deadlines', []))}

Provide:
1. Main takeaway (1 sentence)
2. Required actions (bullet points)
3. Potential risks or concerns
4. Recommended next steps

Format as JSON."""
        
        response = self._make_api_call(
            prompt=prompt,
            model=self.models['balanced'],
            max_tokens=500,
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except:
            return {"insights": response}
    
    def _generate_response(self, email_content: str, category: EmailCategory) -> Dict:
        """Generate appropriate email response suggestions"""
        templates = {
            EmailCategory.URGENT: "Create a prompt acknowledgment with timeline for action",
            EmailCategory.MEETING: "Confirm availability or suggest alternatives",
            EmailCategory.SUPPORT: "Acknowledge issue and provide solution or escalation path"
        }
        
        prompt = f"""Generate a professional email response for this {category.value} email:

Original email (first 500 chars):
{email_content[:500]}...

Task: {templates.get(category, 'Create appropriate professional response')}

Provide 2 response options:
1. Brief response (2-3 sentences)
2. Detailed response (4-5 sentences)

Format as JSON:
{{
    "brief": "response text",
    "detailed": "response text",
    "subject_line": "suggested subject"
}}"""
        
        response = self._make_api_call(
            prompt=prompt,
            model=self.models['balanced'],
            max_tokens=400,
            temperature=0.7  # Higher temperature for more creative responses
        )
        
        try:
            return json.loads(response)
        except:
            return {"brief": response, "detailed": response}
    
    def _make_api_call(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Make API call with error handling and cost tracking"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Track costs (simplified - you'd get actual token counts from response)
                self._track_cost(model, len(prompt), len(response.content[0].text))
                
                return response.content[0].text
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                else:
                    raise
                    
            except APIConnectionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection error, retrying in {retry_delay}s")
                    time.sleep(retry_delay)
                else:
                    raise
                    
            except APIError as e:
                logger.error(f"API error: {e}")
                raise
    
    def _track_cost(self, model: str, input_chars: int, output_chars: int):
        """Track API usage costs"""
        # Rough approximation: 4 chars = 1 token
        input_tokens = input_chars / 4
        output_tokens = output_chars / 4
        
        # Pricing per million tokens (as of 2024)
        pricing = {
            'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
            'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00},
            'claude-3-opus-20240229': {'input': 15.00, 'output': 75.00}
        }
        
        model_pricing = pricing.get(model, pricing['claude-3-sonnet-20240229'])
        cost = (input_tokens / 1_000_000 * model_pricing['input'] + 
                output_tokens / 1_000_000 * model_pricing['output'])
        
        self.total_cost += cost
        return cost
    
    def _get_last_request_cost(self) -> float:
        """Get approximate cost of last request"""
        # This is simplified - in production, track per-request costs
        return round(self.total_cost, 4)
    
    def get_total_cost(self) -> float:
        """Get total accumulated cost"""
        return round(self.total_cost, 4)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_basic_processing():
    """Basic email processing example"""
    processor = EmailProcessor()
    
    sample_email = """
    From: client@example.com
    To: support@mycompany.com
    Subject: Urgent: System Access Issue
    Date: Mon, 29 Jan 2024 14:30:00 -0500
    
    Hi Support Team,
    
    I'm unable to access the dashboard since this morning. I've tried resetting 
    my password but still getting "Authentication Failed" errors.
    
    This is blocking my team's work on the quarterly report due tomorrow.
    
    Can someone please help ASAP?
    
    Error details:
    - Username: client@example.com  
    - Error code: AUTH_FAIL_403
    - Browser: Chrome 121.0
    
    Thanks,
    Sarah Johnson
    Senior Analyst
    """
    
    try:
        result = processor.process_email(sample_email)
        
        print("Email Analysis Results:")
        print(f"Category: {result['category']}")
        print(f"Priority: {result['priority']}")
        print(f"Key Points: {result['parsed_data'].get('key_points', [])}")
        print(f"Action Items: {result['parsed_data'].get('action_items', [])}")
        print(f"\nSuggested Response:")
        if result['response_suggestions']:
            print(result['response_suggestions'].get('brief', 'N/A'))
        print(f"\nProcessing Cost: ${result['processing_cost']}")
        
    except Exception as e:
        logger.error(f"Failed to process email: {e}")


def example_batch_processing():
    """Process multiple emails efficiently"""
    processor = EmailProcessor()
    
    emails = [
        "Email 1: Meeting request for next Tuesday at 3pm...",
        "Email 2: Newsletter about new product features...",
        "Email 3: Urgent bug report from customer..."
    ]
    
    results = []
    for i, email in enumerate(emails):
        try:
            logger.info(f"Processing email {i+1}/{len(emails)}")
            result = processor.process_email(email)
            results.append({
                'email_id': i,
                'success': True,
                'category': result['category'],
                'priority': result['priority']
            })
        except Exception as e:
            results.append({
                'email_id': i,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\nBatch Processing Complete:")
    print(f"Success: {successful}/{len(emails)}")
    print(f"Total Cost: ${processor.get_total_cost()}")
    
    # Category breakdown
    categories = {}
    for r in results:
        if r['success']:
            cat = r['category']
            categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory Distribution:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")


def example_custom_classification():
    """Example with custom email categories and rules"""
    processor = EmailProcessor()
    
    # Email about invoice
    invoice_email = """
    From: accounting@vendor.com
    To: finance@mycompany.com
    Subject: Invoice #INV-2024-001 - Due February 15
    
    Dear Finance Team,
    
    Please find attached invoice #INV-2024-001 for consulting services 
    provided in January 2024.
    
    Amount Due: $15,750.00
    Due Date: February 15, 2024
    
    Payment instructions are included in the attached PDF.
    
    Thank you for your business!
    """
    
    result = processor.process_email(invoice_email)
    
    # Add custom post-processing for financial emails
    if 'invoice' in result['parsed_data'].get('subject', '').lower():
        # Extract financial data
        import re
        amounts = re.findall(r'\$[\d,]+\.?\d*', invoice_email)
        dates = re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', invoice_email)
        
        result['financial_data'] = {
            'amounts': amounts,
            'dates': dates,
            'requires_approval': float(amounts[0].replace('$', '').replace(',', '')) > 10000
        }
    
    print("Financial Email Analysis:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("Claude API Email Processing Examples")
    print("=" * 50)
    
    # Set your API key as environment variable:
    # export ANTHROPIC_API_KEY='your-key-here'
    
    # Run examples
    example_basic_processing()
    # example_batch_processing()
    # example_custom_classification()