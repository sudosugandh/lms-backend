from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.core.tenant import resolve_institute_by_host
from app.schemas.auth import LoginRequest, LoginResponse, UserMe
from app.utils.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint. For super admin, no domain required. For admin, domain must resolve."""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # For super admin, no domain check needed
    if user.role == UserRole.SUPER_ADMIN:
        institute_id = None
    else:
        # For admin, must resolve domain
        # Try X-Host header first (for client-side requests), then fall back to Host header
        x_host = request.headers.get("x-host")
        host_header = request.headers.get("host", "")
        host = x_host or host_header
        
        if not host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Host header is required for admin login"
            )
        
        institute = resolve_institute_by_host(db, host)
        if not institute:
            # Get available domains for better error message
            from app.db.models.domain import Domain
            available_domains = db.query(Domain.host_name).filter(Domain.is_active == True).all()
            available = [d.host_name for d in available_domains]
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Institute not found for this domain: '{host}'. Available domains: {', '.join(available) if available else 'None'}. Make sure the domain exists in the database and matches exactly (including port if specified)."
            )
        
        # Validate user's institute matches resolved institute
        if user.institute_id != institute.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Institute mismatch. User belongs to institute {user.institute_id}, but domain resolves to institute {institute.id}"
            )
        
        institute_id = institute.id
    
    # Create JWT token
    token_data = {
        "user_id": user.id,
        "role": user.role.value,
        "institute_id": institute_id
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return LoginResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "institute_id": institute_id
        }
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """Logout endpoint (client-side token removal)."""
    # In a stateless JWT system, logout is handled client-side
    # We could implement token blacklisting here if needed
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserMe)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return UserMe(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
        institute_id=current_user.institute_id,
        is_active=current_user.is_active
    )
