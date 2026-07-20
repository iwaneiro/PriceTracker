from pydantic import BaseModel

class ProductRequest(BaseModel):
    url: str