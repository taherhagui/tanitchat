from pydantic import BaseModel, Field, model_validator
from typing import Literal
import json


class System(BaseModel):
    tags: list
    categorie: str
    personalization: bool
    description: str
    language: list
    name: str
    image_url: str | None = None
    avatar_url: str | None = None
    draft: bool = True
    is_active: bool | None = None
    variables: list | None = None

class NewSystem(System):
    ia: Literal['vertexia','openia']
    max_token: int | None = None
    openia_model_name: str | None = None
    prompt_sys: str
    temperature : float = Field(None,gt=0,lt=1)
    owner_id : str | None  =None
    created_at: str =Field('')
    updated_at: str = Field('')
    is_active: bool = True
    personalization : bool = Field(False)

    

    

class UpdateSystem(NewSystem):
    tags: list | None = None
    categorie: str | None = None
    personalization: bool | None = None
    description: str | None = None
    language: list | None = None
    name: str | None = None
    image_url: str | None = None
    avatar_url: str | None = None
    draft: bool  | None = None
    ia: Literal['vertexia','openia'] | None = None
    max_token: int | None = None
    openia_model_name: str | None = None
    prompt_sys: str | None = None
    temperature : float | None = Field(None,gt=0,lt=1)
    updated_at: str = ''
    is_active : bool | None = None
    
        
