"""Call management endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from shared.auth import get_current_user
from shared.database import get_db
from shared.models.user import User
from shared.schemas.call import CallCreate, CallListResponse, CallResponse, CallUpdate

from app.services.call_service import (
    create_call,
    get_call,
    list_calls,
    update_call,
)

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.get("", response_model=CallListResponse)
def list_calls_endpoint(
    shop_id: int | None = Query(None, description="Filter by shop ID"),
    direction: str | None = Query(None, description="Filter by direction (inbound/outbound)"),
    call_status: str | None = Query(None, alias="status", description="Filter by call status"),
    start_date: date | None = Query(None, description="Filter calls on or after this date"),
    end_date: date | None = Query(None, description="Filter calls on or before this date"),
    search: str | None = Query(None, description="Search caller name or phone number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List calls with pagination and filters.

    Non-admin users are scoped to their own shop.
    """
    # Non-admin users can only see their own shop's calls.
    effective_shop_id = shop_id
    if current_user.role != "admin":
        effective_shop_id = current_user.shop_id

    return list_calls(
        db=db,
        shop_id=effective_shop_id,
        direction=direction,
        call_status=call_status,
        start_date=start_date,
        end_date=end_date,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{call_id}", response_model=CallResponse)
def get_call_endpoint(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single call by ID, including its participants."""
    call = get_call(db, call_id)
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    # Non-admin users can only view their own shop's calls.
    if current_user.role != "admin" and call.shop_id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return call


@router.post("", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
def create_call_endpoint(
    payload: CallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new outbound call record."""
    # Non-admin users can only create calls for their own shop.
    if current_user.role != "admin" and payload.shop_id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return create_call(db, payload)


@router.patch("/{call_id}", response_model=CallResponse)
def update_call_endpoint(
    call_id: int,
    payload: CallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update fields on an existing call."""
    call = get_call(db, call_id)
    if not call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call not found")

    if current_user.role != "admin" and call.shop_id != current_user.shop_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return update_call(db, call, payload)
