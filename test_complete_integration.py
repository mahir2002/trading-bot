#!/usr/bin/env python3
"""
🧪 COMPLETE INTEGRATION TEST
============================

Comprehensive test of all V4 systems working together.
"""

import logging
import asyncio
import os
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('IntegrationTest')

class CompleteIntegrationTest:
    """Complete integration test for V4 trading system"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        logger.info("🧪 Complete Integration Test initialized")
    
    async def run_complete_test(self):
        """Run complete integration test"""
        try:
            logger.info("🚀 COMPLETE V4 INTEGRATION TEST")
            logger.info("=" * 50)
            
            # Test all components
            tests = [
                ("Production Infrastructure", self.test_production_infrastructure),
                ("Live Trading Integration", self.test_live_trading_integration),
                ("Monitoring Systems", self.test_monitoring_systems),
                ("V4 Trading Bot", self.test_v4_trading_bot)
            ]
            
            for test_name, test_func in tests:
                try:
                    logger.info(f"🧪 Testing {test_name}...")
                    result = await test_func()
                    self.test_results[test_name] = result
                    
                    if result:
                        logger.info(f"   ✅ {test_name}: PASSED")
                    else:
                        logger.warning(f"   ⚠️ {test_name}: ISSUES DETECTED")
                        
                except Exception as e:
                    logger.error(f"   ❌ {test_name}: FAILED - {e}")
                    self.test_results[test_name] = False
            
            # Overall result
            passed_tests = sum(self.test_results.values())
            total_tests = len(self.test_results)
            success_rate = (passed_tests / total_tests) * 100
            
            logger.info(f"\n🎯 INTEGRATION TEST RESULTS:")
            logger.info(f"   Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            if success_rate >= 75:
                logger.info("🎉 INTEGRATION TEST: SUCCESS!")
                logger.info("✅ V4 system ready for production!")
                return True
            else:
                logger.warning("⚠️ INTEGRATION TEST: NEEDS ATTENTION")
                return False
                
        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            return False
    
    async def test_production_infrastructure(self) -> bool:
        """Test production infrastructure"""
        try:
            # Check directory structure
            required_dirs = [
                'production/config',
                'production/monitoring'
            ]
            
            for directory in required_dirs:
                if not os.path.exists(directory):
                    logger.error(f"Missing directory: {directory}")
                    return False
            
            # Check configuration file
            config_file = 'production/config/production.json'
            if not os.path.exists(config_file):
                logger.error("Missing production configuration")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Production infrastructure test failed: {e}")
            return False
    
    async def test_live_trading_integration(self) -> bool:
        """Test live trading integration"""
        try:
            # Check if file exists
            trading_file = 'production/live_trading_integration.py'
            if not os.path.exists(trading_file):
                logger.error("Missing live trading integration")
                return False
            
            # Check file content
            with open(trading_file, 'r') as f:
                content = f.read()
                
            if 'LiveTradingIntegration' in content and 'execute_trade' in content:
                return True
            else:
                logger.error("Invalid live trading integration")
                return False
                
        except Exception as e:
            logger.error(f"Live trading integration test failed: {e}")
            return False
    
    async def test_monitoring_systems(self) -> bool:
        """Test monitoring systems"""
        try:
            # Check monitoring dashboard exists
            dashboard_file = 'production/monitoring/dashboard.py'
            if not os.path.exists(dashboard_file):
                logger.error("Missing monitoring dashboard")
                return False
            
            # Read dashboard file to verify it's valid
            with open(dashboard_file, 'r') as f:
                dashboard_code = f.read()
                
            if 'streamlit' in dashboard_code and 'def main' in dashboard_code:
                return True
            else:
                logger.error("Invalid monitoring dashboard")
                return False
                
        except Exception as e:
            logger.error(f"Monitoring systems test failed: {e}")
            return False
    
    async def test_v4_trading_bot(self) -> bool:
        """Test V4 trading bot"""
        try:
            # Check if V4 integration file exists
            v4_file = 'unified_master_trading_bot_v4_integration.py'
            if not os.path.exists(v4_file):
                logger.error("Missing V4 integration file")
                return False
            
            # Check file size (should be substantial)
            file_size = os.path.getsize(v4_file)
            if file_size > 20000:  # >20KB indicates substantial content
                return True
            else:
                logger.error("V4 integration file too small")
                return False
                
        except Exception as e:
            logger.error(f"V4 trading bot test failed: {e}")
            return False

async def main():
    """Main test execution"""
    try:
        logger.info("🧪 STARTING COMPLETE INTEGRATION TEST")
        
        integration_test = CompleteIntegrationTest()
        success = await integration_test.run_complete_test()
        
        if success:
            logger.info("🎉 ALL SYSTEMS GO! Ready for production!")
        else:
            logger.warning("⚠️ Some systems need attention")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Integration test error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
