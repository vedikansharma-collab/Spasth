import os
import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

Base = declarative_base()

def get_engine_url_and_args():
    raw_url = settings.DATABASE_URL
    if raw_url.startswith("sqlite"):
        return raw_url, {"check_same_thread": False}

    u = urlparse(raw_url)
    dbname = u.path.lstrip("/")

    # Check if local loopback bridge on 5433 is active
    s = socket.socket()
    s.settimeout(0.5)
    tunnel_active = False
    try:
        tunnel_active = (s.connect_ex(("127.0.0.1", 5433)) == 0)
    except Exception:
        pass
    finally:
        s.close()

    if tunnel_active:
        # Route through local tunnel using pure-Python pg8000 driver
        resolved_url = f"postgresql+pg8000://{u.username}:{u.password}@127.0.0.1:5433/{dbname}"
        return resolved_url, {}

    # Check if remote host is reachable with 1.5s timeout
    host = u.hostname
    port = u.port or 5432
    s2 = socket.socket()
    s2.settimeout(1.5)
    remote_reachable = False
    try:
        remote_reachable = (s2.connect_ex((host, port)) == 0)
    except Exception:
        pass
    finally:
        s2.close()

    if not remote_reachable:
        sqlite_path = os.path.join(settings.BASE_DIR, "fin01.db")
        return f"sqlite:///{sqlite_path}", {"check_same_thread": False}

    # Direct connection fallback using pg8000
    clean_url = raw_url.replace("postgresql://", "postgresql+pg8000://", 1).replace("postgres://", "postgresql+pg8000://", 1)
    if "?" in clean_url:
        clean_url = clean_url.split("?")[0]
    return clean_url, {}

db_url, connect_args = get_engine_url_and_args()

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
