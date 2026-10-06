from pydantic import BaseModel, ConfigDict


class PetResponse(BaseModel):
    id: int
    name: str
    species: str | None = None
    breed: str | None = None
    age: int
    gender: str | None = None
    color: str | None = None
    health: str | None = None
    description: str | None = None
    img: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class PetCreateRequest(BaseModel):
    name: str
    species: str | None = None
    breed: str | None = None
    age: int = 0
    gender: str | None = None
    color: str | None = None
    health: str | None = None
    description: str | None = None
    img: str | None = None
    status: int = 1


class PetUpdateRequest(BaseModel):
    name: str | None = None
    species: str | None = None
    breed: str | None = None
    age: int | None = None
    gender: str | None = None
    color: str | None = None
    health: str | None = None
    description: str | None = None
    img: str | None = None
    status: int | None = None
