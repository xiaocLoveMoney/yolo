from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.core.settings import settings
from src.api.routes import datasets, annotations, train, logs, models, infer

app = FastAPI(title="YOLO Training Platform API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（用于访问图片等）
app.mount("/static", StaticFiles(directory=str(settings.DATA_DIR)), name="static")

# 路由
app.include_router(datasets.router)
app.include_router(annotations.router)
app.include_router(train.router)
app.include_router(logs.router)
app.include_router(models.router)
app.include_router(infer.router)

@app.get("/")
async def root():
    return {"message": "YOLO Training Platform API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
