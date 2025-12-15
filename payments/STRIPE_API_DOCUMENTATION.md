# Stripe Payment Gateway API Documentation

> Stripe Connect integration for investor payments to SPVs

---

## Configuration

Add these to your `.env` file:

```env
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
PLATFORM_FEE_PERCENTAGE=2.0
```

---

## API Endpoints

### 1. Connect SPV to Stripe (For SPV Owners)

```http
POST /api/payments/stripe-accounts/connect/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "spv_id": 1,
    "return_url": "https://yourapp.com/stripe/success",
    "refresh_url": "https://yourapp.com/stripe/refresh"
}
```

**Response:**
```json
{
    "message": "Stripe Connect account created",
    "onboarding_url": "https://connect.stripe.com/setup/...",
    "stripe_account": {
        "id": 1,
        "stripe_account_id": "acct_xxx",
        "account_status": "onboarding",
        "charges_enabled": false,
        "payouts_enabled": false
    }
}
```

---

### 2. Check SPV Stripe Status

```http
GET /api/payments/stripe-accounts/status/?spv_id=1
Authorization: Bearer {token}
```

**Response:**
```json
{
    "id": 1,
    "spv": 1,
    "stripe_account_id": "acct_xxx",
    "account_status": "active",
    "charges_enabled": true,
    "payouts_enabled": true,
    "details_submitted": true,
    "is_ready_for_payments": true
}
```

---

### 3. Create Investment Payment (For Investors)

```http
POST /api/payments/create_investment/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "spv_id": 1,
    "amount": 50000,
    "currency": "usd"
}
```

**Response:**
```json
{
    "message": "Payment created",
    "client_secret": "pi_xxx_secret_xxx",
    "payment": {
        "id": 1,
        "payment_id": "PAY-A1B2C3D4",
        "spv": 1,
        "amount": "50000.00",
        "status": "pending",
        "platform_fee": "1000.00",
        "net_amount": "49000.00"
    }
}
```

**Frontend Flow:**
```javascript
// Use client_secret to confirm payment
const stripe = Stripe('pk_test_YOUR_KEY');
const {error} = await stripe.confirmPayment({
    clientSecret: response.client_secret,
    confirmParams: {
        return_url: 'https://yourapp.com/payment/success',
    },
});
```

---

### 4. Confirm Payment

```http
POST /api/payments/confirm/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request:**
```json
{
    "payment_id": "PAY-A1B2C3D4"
}
```

---

### 5. Get Payment History

```http
GET /api/payments/
Authorization: Bearer {token}
```

---

### 6. Get Payment Statistics

```http
GET /api/payments/statistics/
Authorization: Bearer {token}
```

**Response:**
```json
{
    "total_payments": 10,
    "total_amount": "500000.00",
    "successful_payments": 8,
    "pending_payments": 1,
    "failed_payments": 1,
    "total_platform_fees": "10000.00"
}
```

---

### 7. Webhook Endpoint (Configure in Stripe Dashboard)

```
POST /api/payments/webhook/
```

**Events Handled:**
- `payment_intent.succeeded` - Creates Investment record
- `payment_intent.payment_failed` - Updates payment status
- `account.updated` - Updates SPV Stripe account status

---

## Payment Flow Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Investor  │    │   Backend   │    │   Stripe    │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       │ POST /create_investment/            │
       ├─────────────────►│                  │
       │                  │ Create PaymentIntent
       │                  ├─────────────────►│
       │                  │                  │
       │   client_secret  │◄─────────────────┤
       │◄─────────────────┤                  │
       │                  │                  │
       │ stripe.confirmPayment()             │
       ├─────────────────────────────────────►
       │                  │                  │
       │                  │ Webhook: succeeded
       │                  │◄─────────────────┤
       │                  │                  │
       │                  │ Create Investment
       │                  │ Update Portfolio │
       │                  │                  │
       │  Payment Complete │                  │
       │◄─────────────────┤                  │
```
