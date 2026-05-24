import httpx
import time
from sqlalchemy.orm import Session
from config import settings
from database import UserTokenStore

class ZohoClient:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.token_record = db.query(UserTokenStore).filter(UserTokenStore.user_id == user_id).first()

    async def get_valid_access_token(self) -> str:
        """Ensures token lifecycle validity. Auto-refreshes if within buffer boundary."""
        if not self.token_record:
            raise Exception("User session unauthorized. Authenticate via OAuth flow.")

        # Refresh token 5 minutes before absolute expiry boundary
        if time.time() >= (self.token_record.expires_at - 300):
            await self.refresh_access_token()
            
        return self.token_record.access_token

    async def refresh_access_token(self):
        """Asynchronously triggers token exchange loop via Zoho Account Gateways."""
        refresh_payload = {
            "refresh_token": self.token_record.refresh_token,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/token", params=refresh_payload)
            data = response.json()
            
            if "access_token" not in data:
                raise Exception(f"Token refresh cycle failure: {data}")
                
            self.token_record.access_token = data["access_token"]
            self.token_record.expires_at = int(time.time()) + int(data.get("expires_in", 3600))
            self.db.commit()
            self.db.refresh(self.token_record)

    async def get_projects(self):
        """Standard encapsulated Query Tool utilizing non-blocking token delivery."""
        token = await self.get_valid_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            # Note: Zoho Projects requests require a dynamic portal ID configuration
            response = await client.get(f"{settings.ZOHO_BASE_API_URL}/portals/", headers=headers)
            return response.json()