from fastapi import FastAPI

from src.api.v1.auth import router as auth_router
from src.api.v1.cart import router as cart_router
from src.api.v1.health import router as health_router
from src.api.v1.movies import router as movies_router
from src.api.v1.orders import admin_router as admin_orders_router
from src.api.v1.orders import router as orders_router
from src.api.v1.payments import admin_router as admin_payments_router
from src.api.v1.payments import router as payments_router
from src.api.v1.profiles import router as profiles_router
from src.core.config import get_settings

settings = get_settings()

openapi_tags = [
    {"name": "health", "description": "Service health check endpoint."},
    {
        "name": "auth",
        "description": "Registration, login, tokens, and user account actions.",
    },
    {"name": "movies", "description": "Movie catalog endpoints."},
    {"name": "cart", "description": "Shopping cart endpoints for authenticated users."},
    {"name": "orders", "description": "Order creation and order history endpoints."},
    {
        "name": "admin orders",
        "description": "Administrative order management endpoints.",
    },
    {
        "name": "payments",
        "description": "Payment creation and payment callback endpoints.",
    },
    {
        "name": "admin payments",
        "description": "Administrative payment management endpoints.",
    },
    {"name": "profile", "description": "User profile and avatar endpoints."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Online Cinema API with authentication, movie catalog, shopping cart, "
        "orders, payments, background jobs, and avatar storage."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(movies_router, prefix=settings.API_V1_PREFIX)
app.include_router(cart_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(profiles_router, prefix=settings.API_V1_PREFIX)
