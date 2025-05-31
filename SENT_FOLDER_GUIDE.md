# Email Sent Folder Solutions Guide

## Why Emails Don't Appear in Sent Folder

When sending emails via SMTP, the emails are not automatically saved to your "Sent" folder. This is because:
- SMTP only handles sending emails, not folder management
- Each email provider has different folder structures
- The sent folder requires IMAP access to save messages

## Solutions

### Option 1: Automatic IMAP Save (Implemented)
The email sender now attempts to save sent emails to your IMAP sent folder automatically. This works if:
- Your monitoring email and sending email are the same account
- You have IMAP credentials configured in your .env file
- Your email provider allows IMAP append operations

### Option 2: Use Gmail-Specific Features
If using Gmail:
1. Gmail automatically saves emails sent from the same account to "Sent Mail"
2. Make sure your SMTP_USERNAME matches your monitoring EMAIL_ADDRESS
3. Gmail handles this automatically when authenticated properly

### Option 3: BCC Yourself
Add a BCC to save copies of sent emails:
```python
# In email_sender.py, add to message headers:
message['Bcc'] = self.from_address
```

### Option 4: Use Email Client Rules
1. Create a folder in your email client called "Sent Orders"
2. Set up a rule to move emails:
   - FROM: your-sending-email@gmail.com
   - TO: cs@company.com OR laticrete-cs@company.com
   - ACTION: Move to "Sent Orders" folder

### Option 5: Local Email Archive
The system already logs all sent emails. You can find them in:
- Log file: `email_processor.log`
- Search for "Successfully sent order email"

## Troubleshooting

### For Gmail Users
1. If using different accounts for monitoring and sending:
   - The sent email will appear in the SENDING account's sent folder
   - Not in the MONITORING account's sent folder

2. Gmail settings to check:
   - Enable "Show in IMAP" for Sent Mail folder
   - Settings → See all settings → Labels → Show in IMAP

### For Other Providers
1. Check your IMAP folder names:
   ```python
   # Run this to see your folder names:
   import imaplib
   imap = imaplib.IMAP4_SSL('your.imap.server')
   imap.login('email', 'password')
   print(imap.list())
   ```

2. Common sent folder names:
   - Gmail: `[Gmail]/Sent Mail`
   - Outlook: `Sent Items`
   - Yahoo: `Sent`
   - Others: `INBOX.Sent` or `Sent`

## Recommended Setup

For best results:
1. Use the same email account for both monitoring (IMAP) and sending (SMTP)
2. Ensure all credentials in .env match:
   ```
   EMAIL_ADDRESS=monitor@gmail.com
   SMTP_USERNAME=monitor@gmail.com  # Same as EMAIL_ADDRESS
   ```
3. The system will automatically try to save to sent folder

## Manual Verification

To verify emails are being sent:
1. Check the recipient's inbox (CS_EMAIL)
2. Check your email provider's sent folder via web interface
3. Review the log file for confirmation
4. Check your SMTP account's sent folder (if different from monitoring account)