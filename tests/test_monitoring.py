"""
Test suite for monitoring and graceful degradation functionality.
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitoring import (
    HealthMonitor,
    EndpointHealth,
    NetworkHealth,
    get_healthy_rpc_urls,
    record_network_request,
    should_skip_unhealthy_network,
    get_network_health_summary,
    create_github_actions_notification
)


class TestHealthMonitor(unittest.TestCase):
    """Test health monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = HealthMonitor()
        self.test_config = {
            'name': 'Test Network',
            'rpc': 'https://primary.test.com',
            'rpc_fallback': ['https://fallback1.test.com', 'https://fallback2.test.com'],
            'pool': '0x1234567890123456789012345678901234567890'
        }
    
    def test_endpoint_health_creation(self):
        """Test creation of endpoint health records."""
        url = "https://test.com"
        
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            mock_rpc.return_value = {"result": "0x1"}
            
            health = self.monitor.check_endpoint_health(url)
            
            self.assertEqual(health.url, url)
            self.assertTrue(health.is_healthy)
            self.assertEqual(health.success_count, 1)
            self.assertEqual(health.error_count, 0)
            self.assertEqual(health.consecutive_failures, 0)
    
    def test_endpoint_health_failure(self):
        """Test endpoint health failure handling."""
        url = "https://test.com"
        
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = Exception("Network error")
            
            health = self.monitor.check_endpoint_health(url)
            
            self.assertEqual(health.url, url)
            self.assertFalse(health.is_healthy)
            self.assertEqual(health.success_count, 0)
            self.assertEqual(health.error_count, 1)
            self.assertEqual(health.consecutive_failures, 1)
            self.assertIn("Network error", health.last_error)
    
    def test_slow_response_marking(self):
        """Test marking endpoints as unhealthy due to slow response."""
        url = "https://slow.test.com"
        
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            mock_rpc.return_value = {"result": "0x1"}
            
            # Mock time to simulate slow response
            with patch('time.time') as mock_time:
                mock_time.side_effect = [0, 15]  # 15 second response time
                
                health = self.monitor.check_endpoint_health(url)
                
                self.assertFalse(health.is_healthy)
                self.assertIn("Slow response", health.last_error)
                self.assertEqual(health.response_time, 15)
    
    def test_network_health_assessment(self):
        """Test network health assessment with multiple endpoints."""
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            # Primary healthy, one fallback healthy, one unhealthy
            def rpc_side_effect(url, *args, **kwargs):
                if 'primary' in url:
                    return {"result": "0x1"}
                elif 'fallback1' in url:
                    return {"result": "0x1"}
                else:
                    raise Exception("Fallback2 down")
            
            mock_rpc.side_effect = rpc_side_effect
            
            network_health = self.monitor.check_network_health('test', self.test_config)
            
            self.assertEqual(network_health.overall_health, "healthy")
            self.assertTrue(network_health.primary_endpoint.is_healthy)
            self.assertEqual(len(network_health.fallback_endpoints), 2)
            self.assertTrue(network_health.fallback_endpoints[0].is_healthy)
            self.assertFalse(network_health.fallback_endpoints[1].is_healthy)
    
    def test_degraded_network_health(self):
        """Test degraded network health when primary is down."""
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            # Primary down, fallback healthy
            def rpc_side_effect(url, *args, **kwargs):
                if 'primary' in url:
                    raise Exception("Primary down")
                else:
                    return {"result": "0x1"}
            
            mock_rpc.side_effect = rpc_side_effect
            
            network_health = self.monitor.check_network_health('test', self.test_config)
            
            self.assertEqual(network_health.overall_health, "degraded")
            self.assertFalse(network_health.primary_endpoint.is_healthy)
    
    def test_unhealthy_network(self):
        """Test unhealthy network when all endpoints are down."""
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            mock_rpc.side_effect = Exception("All endpoints down")
            
            network_health = self.monitor.check_network_health('test', self.test_config)
            
            # When all endpoints fail, the network should be unhealthy
            # But the current logic marks it as degraded if any endpoint exists
            # Let's check the actual behavior
            self.assertEqual(network_health.overall_health, "unhealthy")
            self.assertFalse(network_health.primary_endpoint.is_healthy)
            for fallback in network_health.fallback_endpoints:
                self.assertFalse(fallback.is_healthy)
    
    def test_healthy_endpoints_ordering(self):
        """Test that healthy endpoints are ordered by preference."""
        with patch('monitoring.rpc_call_with_retry') as mock_rpc:
            # Primary down, fallbacks have different success rates
            def rpc_side_effect(url, *args, **kwargs):
                if 'primary' in url:
                    raise Exception("Primary down")
                else:
                    return {"result": "0x1"}
            
            mock_rpc.side_effect = rpc_side_effect
            
            # Simulate different success rates for fallbacks
            self.monitor.endpoint_health['https://fallback1.test.com'] = EndpointHealth(
                url='https://fallback1.test.com',
                is_healthy=True,
                last_check=datetime.now(),
                response_time=1.0,
                error_count=1,
                success_count=9,  # 90% success rate
                last_error=None,
                consecutive_failures=0
            )
            
            self.monitor.endpoint_health['https://fallback2.test.com'] = EndpointHealth(
                url='https://fallback2.test.com',
                is_healthy=True,
                last_check=datetime.now(),
                response_time=1.0,
                error_count=3,
                success_count=7,  # 70% success rate
                last_error=None,
                consecutive_failures=0
            )
            
            healthy_urls = self.monitor.get_healthy_endpoints('test', self.test_config)
            
            # Should return fallback1 first (higher success rate)
            self.assertEqual(healthy_urls[0], 'https://fallback1.test.com')
            self.assertEqual(healthy_urls[1], 'https://fallback2.test.com')
    
    def test_request_result_recording(self):
        """Test recording of request results."""
        network_key = 'test'
        
        # Create initial network health
        network_health = NetworkHealth(
            network_key=network_key,
            network_name='Test Network',
            primary_endpoint=EndpointHealth(
                url='https://test.com',
                is_healthy=True,
                last_check=datetime.now(),
                response_time=1.0,
                error_count=0,
                success_count=0,
                last_error=None,
                consecutive_failures=0
            ),
            fallback_endpoints=[],
            overall_health='healthy',
            last_successful_call=None,
            total_requests=0,
            failed_requests=0
        )
        
        self.monitor.network_health[network_key] = network_health
        
        # Record successful request
        self.monitor.record_request_result(network_key, True)
        
        updated_health = self.monitor.network_health[network_key]
        self.assertEqual(updated_health.total_requests, 1)
        self.assertEqual(updated_health.failed_requests, 0)
        self.assertIsNotNone(updated_health.last_successful_call)
        
        # Record failed request
        self.monitor.record_request_result(network_key, False, "Test error")
        
        updated_health = self.monitor.network_health[network_key]
        self.assertEqual(updated_health.total_requests, 2)
        self.assertEqual(updated_health.failed_requests, 1)
    
    def test_should_skip_network(self):
        """Test network skipping logic."""
        network_key = 'test'
        
        # Create unhealthy network with old last successful call
        old_time = datetime.now() - timedelta(hours=2)
        network_health = NetworkHealth(
            network_key=network_key,
            network_name='Test Network',
            primary_endpoint=EndpointHealth(
                url='https://test.com',
                is_healthy=False,
                last_check=datetime.now(),
                response_time=None,
                error_count=10,
                success_count=0,
                last_error="Network down",
                consecutive_failures=5
            ),
            fallback_endpoints=[],
            overall_health='unhealthy',
            last_successful_call=old_time,
            total_requests=20,
            failed_requests=18  # 90% failure rate
        )
        
        self.monitor.network_health[network_key] = network_health
        
        should_skip, reason = self.monitor.should_skip_network(network_key)
        
        self.assertTrue(should_skip)
        self.assertIn("No successful calls for", reason)


class TestGracefulDegradation(unittest.TestCase):
    """Test graceful degradation functionality."""
    
    def test_healthy_rpc_urls_function(self):
        """Test get_healthy_rpc_urls function."""
        test_config = {
            'rpc': 'https://primary.test.com',
            'rpc_fallback': ['https://fallback.test.com']
        }
        
        with patch('monitoring.health_monitor') as mock_monitor:
            mock_monitor.get_healthy_endpoints.return_value = [
                'https://primary.test.com',
                'https://fallback.test.com'
            ]
            
            urls = get_healthy_rpc_urls('test', test_config)
            
            self.assertEqual(len(urls), 2)
            self.assertEqual(urls[0], 'https://primary.test.com')
    
    def test_network_request_recording(self):
        """Test network request recording function."""
        with patch('monitoring.health_monitor') as mock_monitor:
            record_network_request('test', True)
            
            mock_monitor.record_request_result.assert_called_once_with('test', True, None)
    
    def test_should_skip_unhealthy_network_function(self):
        """Test should_skip_unhealthy_network function."""
        with patch('monitoring.health_monitor') as mock_monitor:
            mock_monitor.should_skip_network.return_value = (True, "Network down")
            
            should_skip, reason = should_skip_unhealthy_network('test')
            
            self.assertTrue(should_skip)
            self.assertEqual(reason, "Network down")


class TestHealthSummaryAndNotifications(unittest.TestCase):
    """Test health summary and notification functionality."""
    
    def test_health_summary_generation(self):
        """Test health summary generation."""
        monitor = HealthMonitor()
        
        # Add some test network health data
        monitor.network_health['test1'] = NetworkHealth(
            network_key='test1',
            network_name='Test Network 1',
            primary_endpoint=EndpointHealth(
                url='https://test1.com',
                is_healthy=True,
                last_check=datetime.now(),
                response_time=1.0,
                error_count=0,
                success_count=10,
                last_error=None,
                consecutive_failures=0
            ),
            fallback_endpoints=[],
            overall_health='healthy',
            last_successful_call=datetime.now(),
            total_requests=10,
            failed_requests=0
        )
        
        monitor.network_health['test2'] = NetworkHealth(
            network_key='test2',
            network_name='Test Network 2',
            primary_endpoint=EndpointHealth(
                url='https://test2.com',
                is_healthy=False,
                last_check=datetime.now(),
                response_time=None,
                error_count=5,
                success_count=0,
                last_error="Network down",
                consecutive_failures=5
            ),
            fallback_endpoints=[],
            overall_health='unhealthy',
            last_successful_call=None,
            total_requests=5,
            failed_requests=5
        )
        
        with patch('monitoring.health_monitor', monitor):
            summary = get_network_health_summary()
            
            self.assertEqual(summary['overall_stats']['total_networks'], 2)
            self.assertEqual(summary['overall_stats']['healthy_networks'], 1)
            self.assertEqual(summary['overall_stats']['unhealthy_networks'], 1)
            
            self.assertIn('test1', summary['networks'])
            self.assertIn('test2', summary['networks'])
            
            self.assertEqual(summary['networks']['test1']['status'], 'healthy')
            self.assertEqual(summary['networks']['test2']['status'], 'unhealthy')
    
    def test_github_notification_creation(self):
        """Test GitHub Actions notification creation."""
        # Test healthy scenario
        healthy_summary = {
            'overall_stats': {
                'healthy_networks': 3,
                'degraded_networks': 0,
                'unhealthy_networks': 0
            },
            'networks': {}
        }
        
        notification = create_github_actions_notification(healthy_summary)
        self.assertIn("All networks are healthy", notification)
        
        # Test mixed scenario
        mixed_summary = {
            'overall_stats': {
                'healthy_networks': 2,
                'degraded_networks': 1,
                'unhealthy_networks': 1
            },
            'networks': {
                'test1': {
                    'name': 'Test Network 1',
                    'status': 'unhealthy',
                    'healthy_fallbacks': 0,
                    'total_fallbacks': 2
                },
                'test2': {
                    'name': 'Test Network 2',
                    'status': 'degraded',
                    'healthy_fallbacks': 1,
                    'total_fallbacks': 2
                }
            }
        }
        
        notification = create_github_actions_notification(mixed_summary)
        self.assertIn("1 networks unhealthy", notification)
        self.assertIn("1 networks degraded", notification)
        self.assertIn("2 networks healthy", notification)
        self.assertIn("Test Network 1: No healthy endpoints", notification)
        self.assertIn("Test Network 2: Primary down", notification)


if __name__ == '__main__':
    unittest.main(verbosity=2)