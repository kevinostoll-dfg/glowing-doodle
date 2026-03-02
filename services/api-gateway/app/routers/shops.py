"""Shop management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.auth import get_current_user
from shared.database import get_db
from shared.models.phone_number import PhoneNumber
from shared.models.shop import Shop
from shared.models.user import User
from shared.schemas.shop import ShopResponse, ShopUpdate

router = APIRouter(prefix="/api/shops", tags=["shops"])


# --- lightweight schema for phone-number list ---
class PhoneNumberResponse(BaseModel):
    id: int
    phone_number: str
    number_type: str | None
    lead_source: str | None
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ShopResponse])
def list_shops(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List shops.

    Admins see all shops; other users see only their own shop.
    """
    if current_user.role == "admin":
        shops = db.query(Shop).order_by(Shop.name).all()
    else:
        shops = db.query(Shop).filter(Shop.id == current_user.shop_id).all()

    return shops


@router.get("/{shop_id}", response_model=ShopResponse)
def get_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a shop by ID."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if current_user.role != "admin" and shop.id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return shop


@router.patch("/{shop_id}", response_model=ShopResponse)
def update_shop(
    shop_id: int,
    payload: ShopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update shop settings and/or business hours."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found")

    if current_user.role != "admin" and shop.id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Only managers and admins may update shop settings.
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shop, field, value)

    db.commit()
    db.refresh(shop)
    return shop


@router.get("/{shop_id}/phone-numbers", response_model=list[PhoneNumberResponse])
def list_phone_numbers(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List phone numbers assigned to a shop."""
    if current_user.role != "admin" and shop_id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    numbers = (
        db.query(PhoneNumber)
        .filter(PhoneNumber.shop_id == shop_id)
        .order_by(PhoneNumber.phone_number)
        .all()
    )
    return numbers
