# Production Deployment Checklist - DataGuardian Pro
**Status:** Ready for Go-Live

## Critical Before Launch

### 1. Update Company Information
**File:** `services/email_service.py`
```python
"COMPANY_INFO": {
    "name": "DataGuardian Pro BV",  # Update
    "address": "Amsterdam, Netherlands",  # Update
    "postal": "1012 WX",  # Update
    "phone": "+31 (0) 20 XXX XXXX",  # Update
    "email": "billing@dataguardianpro.nl",
    "website": "https://dataguardianpro.nl",
    "VAT_NUMBER": "NL123456789B01",  # REPLACE with real VAT
    "KVK": "12345678",  # REPLACE with real KvK
}
```

### 2. Stripe Configuration
**Get from:** https://dashboard.stripe.com/apikeys
- [ ] Copy Live Secret Key (starts with `sk_live_`)
- [ ] Set as environment variable: `STRIPE_SECRET_KEY`

**Price IDs from:** https://dashboard.stripe.com/products
- [ ] Get 14 price IDs for all tiers:
  - Startup: Monthly, Annual
  - Professional: Monthly, Annual  
  - Growth: Monthly, Annual
  - Scale: Monthly, Annual
  - Salesforce Premium: Monthly, Annual
  - SAP Enterprise: Monthly, Annual
  - Enterprise: Monthly, Annual
  
- [ ] Set environment variables:
  ```
  STRIPE_PRICE_STARTUP_MONTHLY=price_xxx
  STRIPE_PRICE_STARTUP_ANNUAL=price_xxx
  ...etc (14 total)
  ```

**Webhooks:** https://dashboard.stripe.com/webhooks
- [ ] Create new webhook for production URL
  - URL: `https://dataguardianpro.nl/webhooks/stripe`
  - Events: 
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - payment_intent.succeeded
    - charge.dispute.created
- [ ] Copy signing secret to: `STRIPE_WEBHOOK_SECRET`

### 3. Email Configuration (Optional)
Choose ONE:

**Option A: SendGrid (Recommended)**
- [ ] Get API key from https://app.sendgrid.com/settings/api_keys
- [ ] Set: `SENDGRID_API_KEY`
- [ ] Set: `SENDGRID_FROM_EMAIL=billing@dataguardianpro.nl`

**Option B: SMTP (Self-hosted)**
- [ ] Set `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

**Option C: Keep Stripe Default**
- [ ] Use Stripe's automatic receipt emails (no action needed)

### 4. Database
- [ ] Ensure PostgreSQL is configured for production
- [ ] Run migrations: `python -m alembic upgrade head`
- [ ] Verify connection pooling enabled

### 5. Security
- [ ] HTTPS enabled on dataguardianpro.nl
- [ ] SSL certificate valid (auto-renews)
- [ ] All secrets in environment variables (not hardcoded)
- [ ] Rate limiting configured (optional)

### 6. Monitoring
- [ ] Error tracking configured (optional)
- [ ] Payment webhook logs monitored
- [ ] Email delivery verified (if using email)

## Verification Before Launch

```bash
# Run production test
python test_payment_flow.py

# Check all tests pass
# Expected: Results: 8/8 tests passed ✅
```

## After Launch

- [ ] Monitor first 24 hours for errors
- [ ] Test payment flow end-to-end (use test card first)
- [ ] Verify license expiry banner shows correctly
- [ ] Check email delivery (if configured)
- [ ] Monitor Stripe dashboard for webhook failures

## Rollback Plan

If critical issue found:
1. Pause Stripe webhooks
2. Disable payment features
3. Use `suggest_rollback` tool to revert to previous checkpoint
4. Fix issue in development
5. Re-deploy

## Support Contacts

- **Payment Issues:** Stripe support (https://support.stripe.com)
- **Email Issues:** SendGrid support (if using SendGrid)
- **Technical Issues:** Your development team

---

**Ready to Deploy!** 🚀
