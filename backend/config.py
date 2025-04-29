import os

basedir = os.path.abspath(os.path.dirname(__file__))

def env(key: str, default: str | None = None):
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Environment variable '{key}' not set and no default provided")
    return val

class Config:
    SQLALCHEMY_DATABASE_URI = env("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'candidate_verification.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = env("SECRET_KEY", "dev-secret-change-me")
    CORS_ORIGINS = env("CORS_ORIGINS", "*")
