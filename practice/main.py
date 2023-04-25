from idlelib.query import Query

from fastapi import FastAPI, Path, Query, HTTPException, status
from typing import Optional
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    brand: Optional[str] = None
    name: str
    price: float


class UpdateItem(BaseModel):
    brand: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None


inventory = {
}


@app.post("/create-item/{item_id}")
async def create_item(item: Item, item_id: int):
    if item_id in inventory:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item ID already exists.")
    inventory[item_id] = item



@app.get("/get-item/{item_id}")
async def get_item(item_id: int = Path(description="The ID of the item you'd like to view", gt=0)):
    if item_id in inventory:
        return inventory[item_id]

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item ID not found.")


@app.put("/update-item/{item_id}")
async def update_item(item_id: int, item: UpdateItem):
    if item_id not in inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item ID not found.")

    if item.brand is not None:
        inventory[item_id].brand = item.brand

    if item.name is not None:
        inventory[item_id].name = item.name

    if item.price is not None:
        inventory[item_id].price = item.price

    return inventory[item_id]


@app.delete("/delete-item/{item_id}")
async def delete_item(item_id: int):
    if item_id not in inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item ID not found.")

    del inventory[item_id]
    return {"Success": "Item successfully deleted."}
