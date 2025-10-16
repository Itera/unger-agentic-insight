"""
Tests for maintenance service functions (mock tests).
"""

import unittest
from unittest.mock import patch, MagicMock
from services.maintenance_service import MaintenanceAPIService, WorkOrder, AssetKPI


class TestMaintenanceService(unittest.TestCase):
    """Test cases for maintenance service functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        with patch.dict('os.environ', {
            'MAINTENANCE_API_BASE_URL': 'https://test-api.com',
            'MAINTENANCE_API_USERNAME': 'test_user',
            'MAINTENANCE_API_PASSWORD': 'test_pass'
        }):
            self.service = MaintenanceAPIService()
    
    @patch('services.maintenance_service.requests.post')
    def test_get_auth_token(self, mock_post):
        """Test getting authentication token."""
        # Mock successful token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'test_token_123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        token = self.service._get_auth_token()
        
        self.assertEqual(token, 'test_token_123')
        mock_post.assert_called_once()
    
    @patch('services.maintenance_service.requests.request')
    def test_get_asset_kpi(self, mock_request):
        """Test getting asset KPI information."""
        # Mock the auth token
        self.service._token = 'test_token'
        
        # Mock successful KPI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'assetID': 1283,
            'name': 'Test Sensor',
            'workOrderExpired': 1,
            'workOrderExpiredUrl': 'https://test.com/expired',
            'workerOrderExpiresThisWeek': 0,
            'workerOrderExpiresThisWeekUrl': 'https://test.com/thisweek',
            'unreadActionsFromWorkOrders': 0,
            'unreadActionsFromWorkOrdersUrl': 'https://test.com/actions'
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        kpi = self.service.get_asset_kpi('740-38-LI-329')
        
        self.assertIsInstance(kpi, AssetKPI)
        self.assertEqual(kpi.asset_id, 1283)
        self.assertEqual(kpi.name, 'Test Sensor')
        self.assertEqual(kpi.work_order_expired, 1)
    
    @patch('services.maintenance_service.requests.request')
    def test_get_work_orders_by_asset_id(self, mock_request):
        """Test getting work orders by asset ID."""
        # Mock the auth token
        self.service._token = 'test_token'
        
        # Mock successful work orders response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'id': 28612,
                'nr': 30608,
                'projectId': 1,
                'assetId': 1200,
                'shortDescription': 'Test work order',
                'description': 'Test description',
                'comment': 'Test comment',
                'status': 8,
                'from': '2018-09-26T00:00:00',
                'to': '2018-09-26T00:00:00',
                'createdAt': '2018-09-27T00:00:00',
                'finishedDate': '2018-09-27T00:00:00',
                'priority': 1,
                'url': 'https://test.com/workorder',
                'isReactiveMaintenance': False
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        work_orders = self.service.get_work_orders_by_asset_id(1283)
        
        self.assertEqual(len(work_orders), 1)
        self.assertIsInstance(work_orders[0], WorkOrder)
        self.assertEqual(work_orders[0].id, 28612)
        self.assertEqual(work_orders[0].nr, 30608)
        self.assertEqual(work_orders[0].short_description, 'Test work order')
    
    @patch('services.maintenance_service.MaintenanceAPIService.get_asset_kpi')
    @patch('services.maintenance_service.MaintenanceAPIService.get_work_orders_by_asset_id')
    def test_get_work_orders_by_sensor(self, mock_get_work_orders, mock_get_kpi):
        """Test getting work orders by sensor name."""
        # Mock KPI response
        mock_kpi = AssetKPI(
            asset_id=1283,
            name='Test Sensor',
            work_order_expired=1,
            work_order_expired_url='https://test.com',
            worker_order_expires_this_week=0,
            worker_order_expires_this_week_url='https://test.com',
            unread_actions_from_work_orders=0,
            unread_actions_from_work_orders_url='https://test.com'
        )
        mock_get_kpi.return_value = mock_kpi
        
        # Mock work orders response
        mock_work_order = WorkOrder(
            id=28612,
            nr=30608,
            project_id=1,
            asset_id=1283,
            short_description='Test work order',
            description='Test description',
            comment='Test comment',
            status=8,
            from_date='2018-09-26T00:00:00',
            to_date='2018-09-26T00:00:00',
            created_at='2018-09-27T00:00:00',
            finished_date='2018-09-27T00:00:00',
            priority=1,
            url='https://test.com/workorder',
            is_reactive_maintenance=False
        )
        mock_get_work_orders.return_value = [mock_work_order]
        
        work_orders = self.service.get_work_orders_by_sensor('4038LI329.DACA.PV')
        
        self.assertEqual(len(work_orders), 1)
        self.assertEqual(work_orders[0].id, 28612)
        
        # Verify that the sensor name was transformed correctly
        mock_get_kpi.assert_called_once_with('740-38-LI-329')
        mock_get_work_orders.assert_called_once_with(1283)


if __name__ == '__main__':
    unittest.main()