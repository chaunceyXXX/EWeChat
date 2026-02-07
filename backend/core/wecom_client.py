import requests
import time
import os
import logging
from typing import Dict, Any, Optional

class WeComClient:
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, corpid: str, secret: str, agentid: str):
        self.corpid = corpid
        self.secret = secret
        self.agentid = agentid
        self._access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> Optional[str]:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        url = f"{self.BASE_URL}/gettoken"
        params = {
            "corpid": self.corpid,
            "corpsecret": self.secret
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data.get("errcode") == 0:
                self._access_token = data.get("access_token")
                # Expire 5 minutes early to be safe
                self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300
                return self._access_token
            else:
                logging.error(f"Failed to get token: {data}")
                return None
        except Exception as e:
            logging.error(f"Error getting token: {e}")
            return None

    def upload_media(self, file_path: str) -> Optional[str]:
        """Upload file and return media_id"""
        token = self._get_access_token()
        if not token:
            return None

        url = f"{self.BASE_URL}/media/upload"
        params = {
            "access_token": token,
            "type": "file"
        }
        
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, params=params, files=files)
                data = response.json()
                if data.get("errcode") == 0:
                    return data.get("media_id")
                else:
                    logging.error(f"Failed to upload media: {data}")
                    return None
        except Exception as e:
            logging.error(f"Error uploading media: {e}")
            return None

    def send_file_message(self, media_id: str, touser: str = "@all", toparty: str = "") -> bool:
        token = self._get_access_token()
        if not token:
            return False

        url = f"{self.BASE_URL}/message/send"
        params = {"access_token": token}
        
        payload = {
            "touser": touser,
            "toparty": toparty,
            "msgtype": "file",
            "agentid": self.agentid,
            "file": {
                "media_id": media_id
            },
            "safe": 0
        }

        try:
            response = requests.post(url, params=params, json=payload)
            data = response.json()
            if data.get("errcode") == 0:
                return True
            else:
                logging.error(f"Failed to send message: {data}")
                return False
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False
