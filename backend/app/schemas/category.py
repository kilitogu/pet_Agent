from pydantic import BaseModel, ConfigDict


class PetCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    sort: int
    status: int

    model_config = ConfigDict(from_attributes=True)


class PetCategoryCreateRequest(BaseModel):
    name: str
    description: str | None = None
    sort: int = 0
    status: int = 1


class PetCategoryUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    sort: int | None = None
    status: int | None = None
