from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from fastapi import HTTPException, status, Request
from typing import Optional
from firebase_admin import credentials
firebase_admin.initialize_app()
from firebase_admin import firestore, auth 
db = firestore.client()

def decode_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(status.HTTP_410_GONE, detail='EXPIRED_TOKEN')
    except auth.InvalidIdTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail='INVALID_TOKEN')
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='ACCESS_TOKEN_ERR')
    uid = decoded_token["uid"]
    return uid


class auth_required(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        try:
            #ipdb.set_trace()
            credentials: Optional[
                HTTPAuthorizationCredentials
            ] = await super().__call__(request)
        except:
            raise HTTPException(status.HTTP_403_FORBIDDEN, 'NOT_AUTHENTICATED')
        exception = HTTPException(status.HTTP_400_BAD_REQUEST, 'ACCESS_TOKEN_ERR')
        
        if credentials and credentials.scheme == "Bearer":
            uid = decode_token(credentials.credentials)
            return uid
        raise exception  # No credentials