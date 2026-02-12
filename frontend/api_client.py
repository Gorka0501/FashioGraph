"""
Backend API Client
Handles communication with the FastAPI backend
"""

import requests
import json
from typing import Dict, Optional, Any, List, Tuple
from pathlib import Path
from PIL import Image
import io
import time
import sys

try:
    from .config import BACKEND_URL, BACKEND_TIMEOUT
except ImportError:
    # Fallback for direct execution
    from config import BACKEND_URL, BACKEND_TIMEOUT


class BackendAPIClient:
    """Client for communicating with the FastAPI backend"""
    
    def __init__(self, base_url: str = BACKEND_URL, timeout: int = BACKEND_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.wardrobe_id = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """Make HTTP request to backend"""
        try:
            url = f"{self.base_url}{endpoint}"
            kwargs['timeout'] = kwargs.get('timeout', self.timeout)
            kwargs['headers'] = self._get_headers()
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return True, response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            return False, {'error': 'Backend server is not reachable'}
        except requests.exceptions.Timeout:
            return False, {'error': 'Backend request timeout'}
        except requests.exceptions.HTTPError as e:
            try:
                return False, e.response.json()
            except:
                return False, {'error': str(e)}
        except Exception as e:
            return False, {'error': str(e)}
    
    # ========== Authentication ==========
    
    def register(self, username: str, password: str) -> Tuple[bool, Dict]:
        """Register a new user"""
        success, data = self._request('POST', '/api/v1/auth/register',
                                     json={'username': username, 'password': password})
        if success:
            self.token = data.get('access_token')
            self.user_id = data.get('user_id')
            self.wardrobe_id = data.get('wardrobe_id')
        return success, data
    
    def login(self, username: str, password: str) -> Tuple[bool, Dict]:
        """Login user"""
        success, data = self._request('POST', '/api/v1/auth/login',
                                     json={'username': username, 'password': password})
        if success:
            self.token = data.get('access_token')
            self.user_id = data.get('user_id')
            self.wardrobe_id = data.get('wardrobe_id')
        return success, data
    
    def logout(self) -> Tuple[bool, Dict]:
        """Logout user"""
        self.token = None
        self.user_id = None
        self.wardrobe_id = None
        return True, {'message': 'Logged out'}
    
    def fetch_storage_config(self) -> Tuple[bool, Dict]:
        """
        Fetch storage configuration from backend.
        Frontend uses these paths to know where backend stores data.
        """
        success, data = self._request('GET', '/api/v1/storage/config')
        if success:
            try:
                from .config import FrontendStorageConfig
            except ImportError:
                from config import FrontendStorageConfig
            FrontendStorageConfig.set_backend_config(data)
        return success, data
    
    # ========== Wardrobe Management ==========
    
    def add_wardrobe_item(self, image_path: Path) -> Tuple[bool, Dict]:
        """Upload image to backend. Backend will predict and save to DB."""
        if not self.wardrobe_id:
            return False, {'error': 'No wardrobe ID available. Please login first.'}
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                headers = {}
                if self.token:
                    headers['Authorization'] = f'Bearer {self.token}'
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/wardrobe/{self.wardrobe_id}/items",
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                # Image bytes are already included in response as base64
                return True, data
        except requests.exceptions.HTTPError as e:
            try:
                return False, e.response.json()
            except:
                return False, {'error': f"HTTP {e.response.status_code}: {str(e)}"}
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_wardrobe_items(self) -> Tuple[bool, List[Dict]]:
        """Get all wardrobe items"""
        if not self.wardrobe_id:
            return False, []
        success, data = self._request('GET', f'/api/v1/wardrobe/{self.wardrobe_id}/items')
        return success, data if success else []
    
    def get_wardrobe(self) -> Tuple[bool, Dict]:
        """Get wardrobe details"""
        if not self.wardrobe_id:
            return False, {}
        success, data = self._request('GET', f'/api/v1/wardrobe/{self.wardrobe_id}')
        return success, data if success else {}
    
    def get_item_image(self, item_id: str) -> Tuple[bool, Optional[bytes]]:
        """Get item image bytes from backend cache"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/wardrobe/{self.wardrobe_id}/items/{item_id}/image",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return True, response.content
        except Exception as e:
            return False, None
    
    def download_item_image_to_local(self, item_id: int, local_path: Path = None) -> Tuple[bool, str]:
        """
        Download item image from backend and save to local device.
        
        Args:
            item_id: Item ID to download
            local_path: Local file path to save image to (user device). If None, uses config default.
        
        Returns:
            (success: bool, message: str)
        """
        try:
            try:
                from .config import FrontendStorageConfig
            except ImportError:
                from config import FrontendStorageConfig
            
            # Use provided path or get from config
            if local_path is None:
                image_dir = FrontendStorageConfig.get_user_image_dir()
                if not image_dir:
                    # Fetch storage config if not already set
                    import sys
                    if 'st' in sys.modules:
                        import streamlit as st
                        st.session_state.api_client.fetch_storage_config()
                        image_dir = FrontendStorageConfig.get_user_image_dir()
                    
                    if not image_dir:
                        return False, "❌ Storage path not configured. Please login first."
                local_path = image_dir
            
            # If path is a directory, generate filename
            if local_path.is_dir() or str(local_path).endswith(('/', '\\')):
                local_path = Path(local_path) / f"item_{item_id}.jpg"
            
            # Get image bytes from backend
            response = self.session.get(
                f"{self.base_url}/api/v1/wardrobe/{self.wardrobe_id}/items/{item_id}/download-image",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Save to local device
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True, f"✅ Image saved to {local_path}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"❌ Failed to save image: {str(e)}"
    
    def delete_wardrobe_item(self, item_id: str) -> Tuple[bool, Dict]:
        """Delete wardrobe item"""
        if not self.wardrobe_id:
            return False, {'error': 'No wardrobe ID available'}
        success, data = self._request('DELETE', f'/api/v1/wardrobe/{self.wardrobe_id}/items/{item_id}')
        return success, data
    
    def update_wardrobe_item(self, item_id: int, 
                            main_category_indices: Optional[List[int]] = None,
                            sub_category_indices: Optional[List[int]] = None,
                            category_indices: Optional[List[int]] = None,
                            related_indices: Optional[List[int]] = None,
                            available: Optional[bool] = None,
                            is_correction: bool = False) -> Tuple[bool, Dict]:
        """Update item attributes and availability, optionally tracking corrections"""
        if not self.wardrobe_id:
            return False, {'error': 'No wardrobe ID available'}
        
        update_data = {}
        if main_category_indices is not None:
            update_data['main_category_indices'] = main_category_indices
        if sub_category_indices is not None:
            update_data['sub_category_indices'] = sub_category_indices
        if category_indices is not None:
            update_data['category_indices'] = category_indices
        if related_indices is not None:
            update_data['related_indices'] = related_indices
        if available is not None:
            update_data['available'] = available
        if is_correction:
            update_data['is_correction'] = is_correction
        
        success, data = self._request('PUT', f'/api/v1/wardrobe/{self.wardrobe_id}/items/{item_id}',
                                     json=update_data)
        return success, data
    
    # ========== ML Model Inference ==========
    
    def classify_image(self, image_path: Path) -> Tuple[bool, Dict]:
        """Send image to backend for classification"""
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                # Don't use _request for file uploads as it adds Content-Type header
                headers = {}
                if self.token:
                    headers['Authorization'] = f'Bearer {self.token}'
                
                response = self.session.post(
                    f"{self.base_url}/ml/classify",
                    files=files,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return True, response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            try:
                return False, e.response.json()
            except:
                return False, {'error': str(e)}
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_personal_model(self) -> Tuple[bool, Optional[bytes]]:
        """
        Download personal model from backend.
        Note: Personal models are stored on backend per-user.
        This downloads the user's fine-tuned model if available.
        """
        try:
            # Backend endpoint: GET /ml/preference-learner-info
            # To get actual model: user needs to request it from backend via dedicated endpoint
            response = self.session.get(
                f"{self.base_url}/ml/preference-learner-info",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return True, response.content if response.content else None
        except Exception as e:
            return False, None
    
    def suggest_outfit(self, main_categories: List[str], 
                      sub_categories: List[str]) -> Tuple[bool, Dict]:
        """Get outfit suggestions from backend"""
        success, data = self._request('POST', '/ml/outfit/suggest',
                                     json={
                                         'main_categories': main_categories,
                                         'sub_categories': sub_categories
                                     })
        return success, data
    
    # ========== Outfit Management ==========
    
    def get_outfits(self) -> Tuple[bool, List[Dict]]:
        """Get all outfits for user"""
        if not self.wardrobe_id:
            return False, []
        success, data = self._request('GET', f'/api/v1/wardrobe/{self.wardrobe_id}/outfits?limit=100')
        return success, data if isinstance(data, list) else []
    
    def get_outfit(self, outfit_id: int) -> Tuple[bool, Dict]:
        """Get a specific outfit"""
        success, data = self._request('GET', f'/api/v1/wardrobe/{self.wardrobe_id}/outfits/{outfit_id}')
        return success, data
    
    def generate_outfits(self) -> Tuple[bool, Dict]:
        """Generate new outfits from available items"""
        success, data = self._request('POST', f'/api/v1/wardrobe/{self.wardrobe_id}/generate-outfits')
        return success, data
    
    def rate_outfit(self, outfit_id: int, rating: float) -> Tuple[bool, Dict]:
        """Rate an outfit (0-5)"""
        success, data = self._request('POST', f'/api/v1/wardrobe/{self.wardrobe_id}/outfits/{outfit_id}/rate?rating={rating}')
        return success, data
    
    def delete_outfit(self, outfit_id: int) -> Tuple[bool, Dict]:
        """Delete an outfit"""
        success, data = self._request('DELETE', f'/api/v1/wardrobe/{self.wardrobe_id}/outfits/{outfit_id}')
        return success, data
    
    def reset_personal_model(self) -> Tuple[bool, Dict]:
        """Reset user's personal preference model back to base model"""
        success, data = self._request('DELETE', '/api/v1/ml/model/reset')
        return success, data
    
    def retrain_personal_model(self) -> Tuple[bool, Dict]:
        """Retrain user's personal preference model from scratch using base model"""
        success, data = self._request('POST', '/api/v1/ml/model/retrain')
        return success, data
    
    # ========== Health Check ==========
    
    def health_check(self) -> Tuple[bool, Dict]:
        """Check backend health"""
        success, data = self._request('GET', '/health')
        return success, data
    
    def is_connected(self) -> bool:
        """Check if backend is accessible"""
        success, _ = self.health_check()
        return success
    
    def get_categories(self) -> Tuple[bool, Dict[str, Any]]:
        """Get all category mappings (main, sub, categories, related)."""
        success, data = self._request('GET', '/api/v1/ml/categories')
        return success, data


class SyncManager:
    """Manages synchronization between frontend local storage and backend"""
    
    def __init__(self, api_client: BackendAPIClient):
        self.api = api_client
        self.last_sync_time = None
        self.sync_queue = []
    
    def sync_models(self) -> Tuple[bool, str]:
        """Sync personal model with backend"""
        try:
            success, data = self.api.get_personal_model()
            if success:
                from .model_manager import PersonalModelManager
                PersonalModelManager.save_model(data)
                self.last_sync_time = time.time()
                return True, "✅ Model synchronized successfully"
            else:
                return False, f"❌ Failed to sync model: {data.get('error', 'Unknown error')}"
        except Exception as e:
            return False, f"❌ Sync error: {str(e)}"
    
    def sync_wardrobe(self) -> Tuple[bool, str]:
        """Sync wardrobe items with backend"""
        try:
            success, items = self.api.get_wardrobe_items()
            if success:
                # Download item images
                for item in items:
                    item_id = item.get('id')
                    if item_id:
                        img_success, img_data = self.api.get_item_image(item_id)
                        if img_success:
                            try:
                                from .config import LocalStorage
                            except ImportError:
                                from config import LocalStorage
                            LocalStorage.save_image(img_data, f"{item_id}.jpg")
                
                self.last_sync_time = time.time()
                return True, f"✅ Synced {len(items)} wardrobe items"
            else:
                return False, f"❌ Failed to sync wardrobe: {items.get('error', 'Unknown error')}"
        except Exception as e:
            return False, f"❌ Sync error: {str(e)}"
    
    def full_sync(self) -> Tuple[bool, str]:
        """Perform full synchronization"""
        results = []
        
        model_success, model_msg = self.sync_models()
        results.append(model_msg)
        
        wardrobe_success, wardrobe_msg = self.sync_wardrobe()
        results.append(wardrobe_msg)
        
        success = model_success and wardrobe_success
        message = "\n".join(results)
        return success, message


if __name__ == "__main__":
    # Test the client
    client = BackendAPIClient()
    success, data = client.health_check()
    if success:
        print("✅ Backend is running")
        print(data)
    else:
        print("❌ Backend is not reachable")
        print(data)

