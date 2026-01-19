from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    
    # 数据目录
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    DATASETS_DIR: Path = DATA_DIR / "datasets"
    ANNOTATIONS_DIR: Path = DATA_DIR / "annotations"
    JOBS_DIR: Path = DATA_DIR / "jobs"
    
    # 模型目录
    MODELS_DIR: Path = BASE_DIR / "models"
    REGISTRY_DIR: Path = MODELS_DIR / "registry"
    
    # API配置
    API_PREFIX: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        
    def init_directories(self):
        """初始化所有必需的目录"""
        for dir_path in [
            self.DATA_DIR,
            self.UPLOADS_DIR,
            self.DATASETS_DIR,
            self.ANNOTATIONS_DIR,
            self.JOBS_DIR,
            self.MODELS_DIR,
            self.REGISTRY_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.init_directories()
