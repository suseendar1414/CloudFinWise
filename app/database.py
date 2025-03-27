from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class InfrastructureData(Base):
    __tablename__ = 'infrastructure_data'
    
    id = Column(Integer, primary_key=True)
    cloud_provider = Column(String)
    scan_timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)

def init_db(database_url: str = "sqlite:///./infrastructure.db"):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

def store_infrastructure_data(session, cloud_provider: str, data: dict):
    infra_data = InfrastructureData(
        cloud_provider=cloud_provider,
        data=data
    )
    session.add(infra_data)
    session.commit()
    return infra_data

def get_latest_infrastructure_data(session):
    """Get the most recent infrastructure data for all cloud providers."""
    latest_data = {}
    for provider in ['aws', 'azure']:
        result = (session.query(InfrastructureData)
                 .filter(InfrastructureData.cloud_provider == provider)
                 .order_by(InfrastructureData.scan_timestamp.desc())
                 .first())
        if result:
            latest_data[provider] = result.data
    return latest_data
