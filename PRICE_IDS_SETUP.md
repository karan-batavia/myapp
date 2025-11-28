# Stripe Price IDs Configuration

## Overview
All Stripe price IDs have been moved from hardcoded values to environment variables for better configuration management and security.

## Environment Variables

### Development/Test Mode (Current Configuration)
These use placeholder price IDs for testing:

```bash
STRIPE_PRICE_STARTUP_MONTHLY=price_startup_monthly
STRIPE_PRICE_STARTUP_ANNUAL=price_startup_annual
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_professional_monthly
STRIPE_PRICE_PROFESSIONAL_ANNUAL=price_professional_annual
STRIPE_PRICE_GROWTH_MONTHLY=price_growth_monthly
STRIPE_PRICE_GROWTH_ANNUAL=price_growth_annual
STRIPE_PRICE_SCALE_MONTHLY=price_scale_monthly
STRIPE_PRICE_SCALE_ANNUAL=price_scale_annual
STRIPE_PRICE_SALESFORCE_MONTHLY=price_salesforce_monthly
STRIPE_PRICE_SALESFORCE_ANNUAL=price_salesforce_annual
STRIPE_PRICE_SAP_MONTHLY=price_sap_monthly
STRIPE_PRICE_SAP_ANNUAL=price_sap_annual
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_enterprise_monthly
STRIPE_PRICE_ENTERPRISE_ANNUAL=price_enterprise_annual
```

### Production Mode (Before Launch)
Replace these with your real Stripe price IDs from the Stripe dashboard:

1. Go to https://dashboard.stripe.com/prices
2. Find your product prices
3. Note the price ID (starts with `price_`)
4. Update the environment variables with real price IDs

Example:
```bash
STRIPE_PRICE_STARTUP_MONTHLY=price_1234567890abcdef
STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_0987654321fedcba
# ... etc
```

## How It Works

The `_load_price_ids()` function in `services/payment_enhancements.py`:
1. Loads price IDs from environment variables
2. Falls back to placeholder values if not set
3. Returns a dictionary for subscription creation

This allows:
- **Development:** Use placeholder values without changing code
- **Production:** Override with real Stripe price IDs via environment variables
- **Flexibility:** Update prices without deploying code changes

## Usage

```python
from services.payment_enhancements import create_subscription

# Automatically uses environment variables
result = create_subscription(
    customer_email="user@example.com",
    plan_tier="professional",
    billing_cycle="monthly",
    country_code="NL"
)
```

## Migration Path

1. ✅ **Done:** Moved hardcoded values to environment variables
2. **TODO (Before Launch):** 
   - Get real Stripe price IDs from Stripe dashboard
   - Update environment variables in production deployment
   - Test with real price IDs in staging environment
3. **Optional:** Setup CI/CD pipeline to validate price IDs on deployment

## Notes

- All 14 price IDs (7 tiers × 2 billing cycles) are configurable
- Defaults match the old hardcoded values for backward compatibility
- No code changes required to update prices - just update environment variables
- Environment variables can be set via Replit secrets, CI/CD pipelines, or `.env` files
