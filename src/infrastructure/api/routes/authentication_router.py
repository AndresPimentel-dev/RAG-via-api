from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.infrastructure.api.dependencies.auth_dependencies import get_user_use_cases
from src.infrastructure.api.schemas import TokenResponse, UserCreate
from src.use_cases.authentication_cases import UserUseCases

router = APIRouter()


@router.post("/register", status_code=201, response_model=TokenResponse)
def sign_up(
    data: UserCreate, use_case: UserUseCases = Depends(get_user_use_cases)
) -> TokenResponse:
    new = use_case.create_user(data.username, str(data.email), data.password)

    return {"access_token": new, "token_type": "bearer"}


@router.post("/login", status_code=200, response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: UserUseCases = Depends(get_user_use_cases),
) -> TokenResponse:
    user = use_case.login(username=form.username, plain_password=form.password)

    return {"access_token": user, "token_type": "bearer"}
