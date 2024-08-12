from pydantic import BaseModel


class Person(BaseModel):
    uuid: str
    full_name: str
