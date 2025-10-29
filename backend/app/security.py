from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    # For demo, accept only test-token
    if token != "test-token":
        raise HTTPException(status_code=403, detail="Invalid token")
