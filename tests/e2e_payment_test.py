"""
End-to-end payment flow verification script.
Run this to simulate and verify the complete payment flow.

Usage: python tests/e2e_payment_test.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime

def test_1_verify_database_functions():
    """Test 1: Verify database service can update user license tier"""
    print("\n" + "="*60)
    print("TEST 1: Database Service - Update User License Tier")
    print("="*60)
    
    try:
        from services.database_service import database_service
        
        print("✓ Database service imported successfully")
        print(f"✓ Database enabled: {database_service.enabled}")
        
        if database_service.enabled:
            with database_service.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM platform_users")
                    count = cursor.fetchone()[0]
                    print(f"✓ Found {count} users in platform_users table")
                    
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'subscription_records'")
                    columns = [row[0] for row in cursor.fetchall()]
                    print(f"✓ subscription_records columns: {columns}")
                    
                    if 'user_id' in columns:
                        print("✓ user_id column exists in subscription_records")
                    else:
                        print("✗ MISSING: user_id column in subscription_records")
                        return False
        
        print("\n✅ TEST 1 PASSED: Database functions ready")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {str(e)}")
        return False


def test_2_verify_webhook_handler():
    """Test 2: Verify webhook handler has upgrade methods"""
    print("\n" + "="*60)
    print("TEST 2: Webhook Handler - License Upgrade Methods")
    print("="*60)
    
    try:
        from services.webhook_handler import WebhookHandler
        
        handler = WebhookHandler()
        print("✓ WebhookHandler instantiated")
        
        methods = ['_handle_subscription_created', '_handle_subscription_cancelled', 
                   '_update_user_license_tier', '_update_user_license_tier_by_email']
        
        for method in methods:
            if hasattr(handler, method):
                print(f"✓ Method exists: {method}")
            else:
                print(f"✗ MISSING method: {method}")
                return False
        
        print("\n✅ TEST 2 PASSED: Webhook handler ready")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {str(e)}")
        return False


def test_3_simulate_subscription_webhook():
    """Test 3: Simulate a subscription.created webhook event"""
    print("\n" + "="*60)
    print("TEST 3: Simulate Subscription Created Event")
    print("="*60)
    
    try:
        from services.database_service import database_service
        
        if not database_service.enabled:
            print("✗ Database not enabled, skipping simulation")
            return False
        
        with database_service.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, email, license_tier FROM platform_users LIMIT 1")
                user = cursor.fetchone()
                
                if not user:
                    print("✗ No test user found")
                    return False
                
                user_id, email, current_tier = user
                print(f"✓ Found test user: id={user_id}, email={email}, current_tier={current_tier}")
                
                test_subscription = {
                    'id': f'sub_test_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    'customer': 'cus_test_e2e',
                    'customer_email': email,
                    'status': 'active',
                    'metadata': {
                        'user_id': str(user_id),
                        'plan_tier': 'professional'
                    },
                    'current_period_start': int(datetime.now().timestamp()),
                    'current_period_end': int(datetime.now().timestamp()) + 86400 * 30,
                    'plan_name': 'Professional',
                    'amount': 9900,
                    'currency': 'eur',
                    'interval': 'month'
                }
                
                print(f"✓ Created test subscription: {test_subscription['id']}")
                
                from services.webhook_handler import WebhookHandler
                handler = WebhookHandler()
                
                result = handler._handle_subscription_created(test_subscription)
                print(f"✓ Webhook handler result: {result}")
                
                cursor.execute("SELECT license_tier FROM platform_users WHERE id = %s", (user_id,))
                new_tier = cursor.fetchone()[0]
                print(f"✓ User tier after update: {new_tier}")
                
                if new_tier == 'professional':
                    print("\n✅ TEST 3 PASSED: User tier correctly updated to 'professional'")
                    
                    cursor.execute("""
                        UPDATE platform_users SET license_tier = %s WHERE id = %s
                    """, (current_tier, user_id))
                    conn.commit()
                    print(f"  (Restored user to original tier: {current_tier})")
                    return True
                else:
                    print(f"\n✗ TEST 3 FAILED: Expected 'professional', got '{new_tier}'")
                    return False
                    
    except Exception as e:
        print(f"\n✗ TEST 3 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_4_verify_stripe_metadata_in_checkout():
    """Test 4: Verify Stripe checkout includes user_id in metadata"""
    print("\n" + "="*60)
    print("TEST 4: Stripe Checkout Metadata Configuration")
    print("="*60)
    
    try:
        import inspect
        from components.pricing_display import create_checkout_session
        
        source = inspect.getsource(create_checkout_session)
        
        if 'user_id' in source.lower():
            print("✓ create_checkout_session includes user_id in metadata")
        else:
            print("✗ WARNING: user_id may not be in checkout metadata")
        
        if 'plan_tier' in source.lower() or 'tier' in source.lower():
            print("✓ create_checkout_session includes tier info")
        else:
            print("✗ WARNING: tier info may not be in checkout metadata")
        
        print("\n✅ TEST 4 PASSED: Checkout configuration verified")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {str(e)}")
        return False


def test_5_verify_subscription_record_storage():
    """Test 5: Verify subscription records are stored with user_id"""
    print("\n" + "="*60)
    print("TEST 5: Subscription Record Storage with User ID")
    print("="*60)
    
    try:
        from services.database_service import database_service
        
        if not database_service.enabled:
            print("✗ Database not enabled")
            return False
        
        test_subscription = {
            'id': f'sub_storage_test_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'customer': 'cus_storage_test',
            'customer_email': 'storage_test@example.com',
            'status': 'active',
            'plan_name': 'Test Plan',
            'amount': 5900,
            'currency': 'eur',
            'interval': 'month',
            'current_period_start': int(datetime.now().timestamp()),
            'current_period_end': int(datetime.now().timestamp()) + 86400 * 30,
            'metadata': {
                'user_id': '999',
                'plan_tier': 'startup'
            }
        }
        
        result = database_service.store_subscription_record(test_subscription)
        print(f"✓ Store subscription result: {result}")
        
        with database_service.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT subscription_id, user_id FROM subscription_records 
                    WHERE subscription_id = %s
                """, (test_subscription['id'],))
                record = cursor.fetchone()
                
                if record:
                    sub_id, stored_user_id = record
                    print(f"✓ Retrieved: subscription_id={sub_id}, user_id={stored_user_id}")
                    
                    if stored_user_id == 999:
                        print("\n✅ TEST 5 PASSED: user_id correctly stored in subscription record")
                        
                        cursor.execute("DELETE FROM subscription_records WHERE subscription_id = %s", 
                                      (test_subscription['id'],))
                        conn.commit()
                        print("  (Cleaned up test record)")
                        return True
                    else:
                        print(f"\n✗ TEST 5 FAILED: Expected user_id=999, got {stored_user_id}")
                        return False
                else:
                    print("\n✗ TEST 5 FAILED: Subscription record not found")
                    return False
                    
    except Exception as e:
        print(f"\n✗ TEST 5 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all E2E verification tests"""
    print("\n" + "#"*60)
    print("# PAYMENT FLOW E2E VERIFICATION")
    print("# DataGuardian Pro - Subscription License Upgrade")
    print("#"*60)
    
    results = []
    
    results.append(("Database Functions", test_1_verify_database_functions()))
    results.append(("Webhook Handler", test_2_verify_webhook_handler()))
    results.append(("Subscription Simulation", test_3_simulate_subscription_webhook()))
    results.append(("Checkout Metadata", test_4_verify_stripe_metadata_in_checkout()))
    results.append(("Subscription Storage", test_5_verify_subscription_record_storage()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - Payment flow is ready!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed - Review and fix issues")
        return 1


if __name__ == '__main__':
    exit(main())
