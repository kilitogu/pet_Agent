from pydantic import BaseModel


class PetTrendItem(BaseModel):
    date: str
    count: int


class SpeciesItem(BaseModel):
    name: str
    value: int


class RecentPetItem(BaseModel):
    id: int
    name: str
    species: str | None = None
    img: str | None = None
    status: int


class DashboardStats(BaseModel):
    pet_total: int
    pet_waiting: int
    pet_adopted: int
    user_total: int
    pet_trend: list[PetTrendItem] = []
    species_distribution: list[SpeciesItem] = []
    recent_pets: list[RecentPetItem] = []
