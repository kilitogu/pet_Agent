from pydantic import BaseModel


class FileRespones(BaseModel):
  original_name: str
  disk_name: str
  size: int
  url: str