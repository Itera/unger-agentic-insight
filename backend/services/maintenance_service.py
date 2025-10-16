"""
Service for interacting with the maintenance API to fetch work orders.
"""

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from .sensor_utils import transform_sensor_to_asset_name


logger = logging.getLogger(__name__)


@dataclass
class WorkOrder:
    """Data class for work order information."""
    id: int
    nr: int
    project_id: int
    asset_id: int
    short_description: str
    description: str
    comment: str
    status: int
    from_date: str
    to_date: str
    created_at: str
    finished_date: Optional[str]
    priority: int
    url: str
    is_reactive_maintenance: bool


@dataclass
class AssetKPI:
    """Data class for asset KPI information."""
    asset_id: int
    name: str
    work_order_expired: int
    work_order_expired_url: str
    worker_order_expires_this_week: int
    worker_order_expires_this_week_url: str
    unread_actions_from_work_orders: int
    unread_actions_from_work_orders_url: str


class MaintenanceAPIService:
    """Service for interacting with maintenance API."""
    
    def __init__(self):
        self.base_url = os.getenv('MAINTENANCE_API_BASE_URL')
        self.username = os.getenv('MAINTENANCE_API_USERNAME')
        self.password = os.getenv('MAINTENANCE_API_PASSWORD')
        self._token = None
        self._token_expires_at = None
        
        if not all([self.base_url, self.username, self.password]):
            raise ValueError("Missing maintenance API configuration in environment variables")
    
    def _get_auth_token(self) -> str:
        """Get or refresh the authentication token."""
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._token
        
        try:
            response = requests.post(
                f"{self.base_url}/api/token",
                json={
                    "username": self.username,
                    "password": self.password
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._token = token_data.get("token") or token_data.get("access_token")
            
            # Assume token expires in 1 hour if not specified
            self._token_expires_at = datetime.now() + timedelta(hours=1)
            
            return self._token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get auth token: {e}")
            raise
    
    def _make_authenticated_request(self, endpoint: str, method: str = "GET", **kwargs) -> requests.Response:
        """Make an authenticated request to the maintenance API."""
        token = self._get_auth_token()
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def get_asset_kpi(self, asset_name: str) -> Optional[AssetKPI]:
        """
        Get asset KPI information by asset name.
        
        Args:
            asset_name: Asset name in format like '740-38-LI-329'
            
        Returns:
            AssetKPI object or None if not found
        """
        try:
            response = self._make_authenticated_request(f"/api/Asset/{asset_name}/KPI")
            data = response.json()
            
            return AssetKPI(
                asset_id=data["assetID"],
                name=data["name"],
                work_order_expired=data["workOrderExpired"],
                work_order_expired_url=data["workOrderExpiredUrl"],
                worker_order_expires_this_week=data["workerOrderExpiresThisWeek"],
                worker_order_expires_this_week_url=data["workerOrderExpiresThisWeekUrl"],
                unread_actions_from_work_orders=data["unreadActionsFromWorkOrders"],
                unread_actions_from_work_orders_url=data["unreadActionsFromWorkOrdersUrl"]
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to get asset KPI for {asset_name}: {e}")
            return None
    
    def get_work_orders_by_asset_id(self, asset_id: int) -> List[WorkOrder]:
        """
        Get all work orders for a specific asset ID.
        
        Args:
            asset_id: Asset ID from the maintenance system
            
        Returns:
            List of WorkOrder objects
        """
        try:
            response = self._make_authenticated_request(f"/api/Asset/{asset_id}/WorkOrder")
            data = response.json()
            
            work_orders = []
            for item in data:
                work_order = WorkOrder(
                    id=item["id"],
                    nr=item["nr"],
                    project_id=item["projectId"],
                    asset_id=item["assetId"],
                    short_description=item["shortDescription"],
                    description=item.get("description", ""),
                    comment=item.get("comment", ""),
                    status=item["status"],
                    from_date=item["from"],
                    to_date=item["to"],
                    created_at=item["createdAt"],
                    finished_date=item.get("finishedDate"),
                    priority=item["priority"],
                    url=item.get("url", ""),
                    is_reactive_maintenance=item.get("isReactiveMaintenance", False)
                )
                work_orders.append(work_order)
            
            return work_orders
            
        except requests.RequestException as e:
            logger.error(f"Failed to get work orders for asset {asset_id}: {e}")
            return []
    
    def get_work_orders_by_sensor(self, sensor_name: str) -> List[WorkOrder]:
        """
        Get work orders for a sensor by transforming sensor name to asset name.
        
        Args:
            sensor_name: Sensor name in format like '4038LI329.DACA.PV'
            
        Returns:
            List of WorkOrder objects
        """
        asset_name = transform_sensor_to_asset_name(sensor_name)
        if not asset_name:
            logger.warning(f"Could not transform sensor name to asset name: {sensor_name}")
            return []
        
        asset_kpi = self.get_asset_kpi(asset_name)
        if not asset_kpi:
            logger.warning(f"Could not find asset KPI for asset: {asset_name}")
            return []
        
        return self.get_work_orders_by_asset_id(asset_kpi.asset_id)
    
    def get_work_orders_for_sensors(self, sensor_names: List[str]) -> Dict[str, List[WorkOrder]]:
        """
        Get work orders for multiple sensors.
        
        Args:
            sensor_names: List of sensor names
            
        Returns:
            Dictionary mapping sensor names to their work orders
        """
        result = {}
        for sensor_name in sensor_names:
            result[sensor_name] = self.get_work_orders_by_sensor(sensor_name)
        return result