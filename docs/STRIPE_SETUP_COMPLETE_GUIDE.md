# DataGuardian Pro - Complete Stripe Setup Guide

## Your Current Pricing Configuration

Based on your app's pricing config, here are the exact products and prices to create in Stripe:

| Tier | Monthly Price | Annual Price | Description |
|------|---------------|--------------|-------------|
| Startup Essential | €59 | €590 | For 1-25 employees, < €1M revenue |
| Professional Plus | €99 | €990 | For 15-50 employees, €500K-€5M revenue |
| Growth Professional | €179 | €1,790 | For 25-100 employees, €1M-€10M revenue |
| Scale Professional | €499 | €4,990 | For 100-500 employees, €10M-€50M revenue |
| Salesforce Premium | €699 | €6,990 | With Salesforce CRM integration |
| SAP Enterprise | €999 | €9,990 | With SAP ERP integration |
| Enterprise Ultimate | €1,399 | €13,990 | All features + premium connectors |

---

## PART 1: CREATE PRODUCTS IN STRIPE TEST MODE

### Step 1.1: Access Stripe Dashboard
1. Go to https://dashboard.stripe.com
2. Login to your account
3. **IMPORTANT**: Toggle "Test mode" ON (top-right corner, orange banner visible)

### Step 1.2: Create Startup Essential Product
1. Click **Products** in left sidebar (or More → Product catalog)
2. Click **+ Add product** button

3. Fill in:
   - **Name**: `DataGuardian Pro - Startup Essential`
   - **Description**: `Complete GDPR + AI Act compliance for growing startups (1-25 employees). 200 scans/month, 20 data sources, 24h SLA support. 30-day money-back guarantee.`

4. Add Monthly Price:
   - Click **Add a price**
   - Amount: `59.00`
   - Currency: `EUR`
   - Billing period: **Recurring** → **Monthly**
   - Click **Add price**

5. Add Annual Price:
   - Click **Add another price**
   - Amount: `590.00`
   - Currency: `EUR`
   - Billing period: **Recurring** → **Yearly**
   - Click **Add price**

6. Click **Save product**

7. **COPY THE PRICE IDs** (click on the product, scroll to Pricing section):
   - Monthly Price ID: `price_` ___________________________
   - Annual Price ID: `price_` ___________________________

### Step 1.3: Create Professional Plus Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - Professional Plus`
   - **Description**: `Advanced scanning + compliance automation for growing businesses (15-50 employees). 350 scans/month, 35 data sources, 16h SLA. Compliance certificates included.`

3. Add Monthly Price: `99.00 EUR` - Monthly recurring
4. Add Annual Price: `990.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

### Step 1.4: Create Growth Professional Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - Growth Professional` 
   - **Description**: `Enterprise-grade compliance automation with quarterly business reviews (25-100 employees). 750 scans/month, 75 data sources, 8h SLA. Most popular tier.`

3. Add Monthly Price: `179.00 EUR` - Monthly recurring
4. Add Annual Price: `1790.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

### Step 1.5: Create Scale Professional Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - Scale Professional`
   - **Description**: `Unlimited scanning + dedicated support team for mid-size companies (100-500 employees). Unlimited scans, 2h SLA, API access, white-label option.`

3. Add Monthly Price: `499.00 EUR` - Monthly recurring
4. Add Annual Price: `4990.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

### Step 1.6: Create Salesforce Premium Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - Salesforce Premium`
   - **Description**: `Enterprise CRM compliance with Netherlands BSN/KvK specialization. Full Salesforce integration, CRM data mapping, 4h SLA support.`

3. Add Monthly Price: `699.00 EUR` - Monthly recurring
4. Add Annual Price: `6990.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

### Step 1.7: Create SAP Enterprise Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - SAP Enterprise`
   - **Description**: `Complete SAP ERP compliance with HR/Finance BSN scanning. SAP HR Module (PA0002), Finance Module (KNA1/LFA1), custom fields, 2h SLA.`

3. Add Monthly Price: `999.00 EUR` - Monthly recurring
4. Add Annual Price: `9990.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

### Step 1.8: Create Enterprise Ultimate Product
1. Click **+ Add product**

2. Fill in:
   - **Name**: `DataGuardian Pro - Enterprise Ultimate`
   - **Description**: `Complete platform + all premium connectors (Salesforce, SAP, Banking). Unlimited everything, 1h SLA, executive partnership, legal consultation hours.`

3. Add Monthly Price: `1399.00 EUR` - Monthly recurring
4. Add Annual Price: `13990.00 EUR` - Yearly recurring
5. Click **Save product**

6. **COPY THE PRICE IDs**:
   - Monthly: `price_` ___________________________
   - Annual: `price_` ___________________________

---

## PART 2: ENABLE PAYMENT METHODS

### Step 2.1: Enable iDEAL (Netherlands)
1. Click **Settings** (bottom-left gear icon)
2. Click **Payment methods** under Payments
3. Find **iDEAL** and click **Turn on**
4. Click **Save**

### Step 2.2: Enable SEPA Direct Debit (EU Recurring)
1. Still in Payment methods
2. Find **SEPA Direct Debit** and click **Turn on**
3. Click **Save**

### Step 2.3: Enable Bancontact (Belgium - Optional)
1. Find **Bancontact** and click **Turn on**
2. Click **Save**

---

## PART 3: VERIFY WEBHOOKS

Your webhooks are already configured. Verify they're correct:

### Step 3.1: Check Test Mode Webhook
1. Go to **Developers** → **Webhooks**
2. You should see: `DataGuardianPro-Test-Webhook`
   - URL: `https://dataguardianpro.nl/webhook/stripe`
   - Status: Active
   - Events: 10 events

### Step 3.2: Check Live Mode Webhook
1. Toggle **Test mode OFF** (top-right)
2. Go to **Developers** → **Webhooks**
3. You should see: `DataguardianproWebhook`
   - URL: `https://dataguardianpro.nl/webhook/stripe`
   - Status: Active

---

## PART 4: UPDATE YOUR APP WITH PRICE IDs

### Step 4.1: Update Environment Variables

After creating all products, update your environment variables with the real Price IDs.

Replace the placeholder values with your actual Stripe Price IDs:

```
STRIPE_PRICE_STARTUP_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_STARTUP_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_PROFESSIONAL_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_GROWTH_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_GROWTH_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SCALE_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SCALE_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SALESFORCE_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SALESFORCE_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SAP_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_SAP_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_1Qxxxxxxxxxxxxxxxx
STRIPE_PRICE_ENTERPRISE_ANNUAL=price_1Qxxxxxxxxxxxxxxxx
```

---

## PART 5: TEST CHECKOUT FLOW

### Step 5.1: Test in Test Mode
1. Make sure Stripe is in **Test mode** (orange banner)
2. Go to your app: https://dataguardianpro.nl
3. Navigate to **Pricing & Plans**
4. Select a plan and click Subscribe
5. Use test card: `4242 4242 4242 4242`
6. Expiry: Any future date (e.g., `12/28`)
7. CVC: Any 3 digits (e.g., `123`)
8. Complete payment

### Step 5.2: Test iDEAL Payment
1. In the checkout, select iDEAL
2. Select any test bank
3. Click "Authorize test payment" on the redirect page
4. Verify webhook received the event

### Step 5.3: Verify Webhook Delivery
1. In Stripe Dashboard: **Developers** → **Webhooks**
2. Click on your test webhook
3. Check **Event deliveries** tab
4. You should see `checkout.session.completed` with 200 status

---

## PART 6: GO LIVE (PRODUCTION)

### Step 6.1: Copy Products to Live Mode
1. Toggle **Test mode OFF** (no more orange banner)
2. Go to **Products**
3. Click on each product
4. Click **Copy to live mode** button (or recreate manually)

### Step 6.2: Get Live API Keys
1. Go to **Developers** → **API keys**
2. Copy your **Publishable key** (starts with `pk_live_`)
3. Copy your **Secret key** (starts with `sk_live_`)

### Step 6.3: Update Live Secrets
Update your secrets with live keys:
- `STRIPE_SECRET_KEY` = your live secret key
- `STRIPE_PUBLISHABLE_KEY` = your live publishable key

### Step 6.4: Update Live Price IDs
Get the Price IDs from your LIVE products (they're different from test) and update your environment variables.

---

## QUICK REFERENCE: YOUR PRICE IDs

Fill in after creating products in Stripe:

### TEST MODE PRICE IDs
| Tier | Monthly Price ID | Annual Price ID |
|------|-----------------|-----------------|
| Startup Essential | price_____________ | price_____________ |
| Professional Plus | price_____________ | price_____________ |
| Growth Professional | price_____________ | price_____________ |
| Scale Professional | price_____________ | price_____________ |
| Salesforce Premium | price_____________ | price_____________ |
| SAP Enterprise | price_____________ | price_____________ |
| Enterprise Ultimate | price_____________ | price_____________ |

### LIVE MODE PRICE IDs
| Tier | Monthly Price ID | Annual Price ID |
|------|-----------------|-----------------|
| Startup Essential | price_____________ | price_____________ |
| Professional Plus | price_____________ | price_____________ |
| Growth Professional | price_____________ | price_____________ |
| Scale Professional | price_____________ | price_____________ |
| Salesforce Premium | price_____________ | price_____________ |
| SAP Enterprise | price_____________ | price_____________ |
| Enterprise Ultimate | price_____________ | price_____________ |

---

## TROUBLESHOOTING

### Payment Fails
- Check webhook logs: Developers → Webhooks → Click endpoint → Event deliveries
- Verify webhook secret matches `STRIPE_WEBHOOK_SECRET` in your app

### iDEAL Not Showing
- Ensure iDEAL is enabled: Settings → Payment methods
- iDEAL only works for EUR payments

### Subscription Not Updating
- Check webhook events are being received
- Look for `customer.subscription.created` event
- Check your app's webhook handler logs

---

**Document Updated**: January 2026
**Stripe API Version**: 2025-03-31.basil
