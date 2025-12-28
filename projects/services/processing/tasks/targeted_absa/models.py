from sqlalchemy import Column, String, Float, DateTime, Text, Integer, create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class AbsaResultModel(Base):
    __tablename__ = 'targeted_absa_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(255), nullable=False)
    source_text = Column(Text, nullable=True)
    aspect = Column(String(100), nullable=False)
    sentiment = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    correction = Column(String(50), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)

def create_tables(connection_string):
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
