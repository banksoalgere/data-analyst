from pydantic import BaseModel
from typing import Optional

class aiRequest(BaseModel):
    message: str
    user_id: Optional[int]
