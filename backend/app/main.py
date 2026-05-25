from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router 
from app.api.routes_chat import router as chat_router
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.core.responses import fail

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A portfolio-ready RAG knowledge base API.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
    app.include_router(health_router,prefix="/api",tags=["health"])
    app.include_router(documents_router,prefix="/api/documents",tags=["documents"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    return app

#当业务逻辑抛出AppError时，返回标准错误响应
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(
            code=exc.code,
            message=exc.message,
        ),
    )

#请求参数不符合接口定义时，返回参数错误响应
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=fail(
            code="VALIDATION_ERROR",
            message="请求参数不合法。",
            data=exc.errors(),
        ),
    )

#在出现没有被专门处理的未知异常时调用。
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=fail(
            code="INTERNAL_ERROR",
            message="服务暂时不可用，请稍后重试。",
        ),
    )

app = create_app()
