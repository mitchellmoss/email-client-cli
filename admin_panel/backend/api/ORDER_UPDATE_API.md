# Order Update API Documentation

## PATCH /api/orders/{order_id}

Updates an existing order with validation and audit logging.

### Authentication
- **Required**: Yes
- **Type**: Bearer token
- **Permissions**: Any authenticated user can update orders

### Path Parameters
- `order_id` (string, required): The ID of the order to update

### Request Body
All fields are optional. Only include fields you want to update.

```json
{
  "order_id": "string",           // New order ID (validated for uniqueness)
  "email_subject": "string",      // Email subject line
  "sent_to": "string",           // Recipient email address
  "customer_name": "string",      // Customer name
  "tileware_products": [          // Array of products
    {
      "name": "string",
      "sku": "string",
      "quantity": 0,
      "price": "string"
    }
  ],
  "order_total": "string",        // Order total amount
  "formatted_content": "string",  // Formatted email content
  "order_data": {},              // Complete order data (JSON object)
  "original_html": "string"       // Original HTML email content
}
```

### Response

#### Success (200 OK)
Returns the updated order details:

```json
{
  "id": 123,
  "order_id": "43060",
  "email_subject": "Updated subject",
  "sent_at": "2024-01-15T10:30:00Z",
  "sent_to": "cs@company.com",
  "customer_name": "John Doe",
  "tileware_products": [...],
  "order_total": "$155.20",
  "created_at": "2024-01-15T10:30:00Z",
  "formatted_content": "...",
  "email_uid": "12345",
  "history": [
    {
      "id": 456,
      "order_id": "43060",
      "action": "updated",
      "details": "{\"user\": \"admin@example.com\", ...}",
      "timestamp": "2024-01-15T11:00:00Z"
    }
  ]
}
```

#### Error Responses

- **400 Bad Request**: Validation error
  ```json
  {
    "detail": "Order ID 43058 already exists"
  }
  ```

- **404 Not Found**: Order not found
  ```json
  {
    "detail": "Order not found"
  }
  ```

- **500 Internal Server Error**: Server error
  ```json
  {
    "detail": "Internal server error updating order"
  }
  ```

### Features

1. **Partial Updates**: Only fields included in the request are updated
2. **Validation**: 
   - Order ID uniqueness check when changing order_id
   - Field type validation
   - JSON structure validation for complex fields
3. **Audit Logging**: All updates are logged with:
   - User email who made the change
   - Timestamp of the change
   - Before and after values for each changed field
   - Stored in order_processing_log table
4. **Data Integrity**:
   - Transactional updates (all or nothing)
   - Automatic JSON serialization for complex fields
   - Preserves unmodified fields

### Example Usage

```bash
# Update simple fields
curl -X PATCH http://localhost:8000/api/orders/43060 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Jane Smith",
    "order_total": "$200.00"
  }'

# Update products
curl -X PATCH http://localhost:8000/api/orders/43060 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tileware_products": [
      {
        "name": "TileWare Product",
        "sku": "TW-001",
        "quantity": 2,
        "price": "$100.00"
      }
    ]
  }'

# Change order ID
curl -X PATCH http://localhost:8000/api/orders/43060 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "43060-REVISED"
  }'
```

### Implementation Notes

- The endpoint preserves backward compatibility with existing order structure
- JSON fields (tileware_products, order_data) accept both string and object formats
- Audit log entries are never deleted, even if the order is deleted
- When order_id is changed, all related log entries are updated to maintain referential integrity