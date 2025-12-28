<<<<<<< HEAD
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, create_engine
=======
﻿from sqlalchemy import Column, String, Float, DateTime, Text, Integer, create_engine
>>>>>>> targeted-absa-2
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class AbsaResultModel(Base):
<<<<<<< HEAD
    __tablename__ = "targeted_absa_results"

=======
    __tablename__ = 'targeted_absa_results'
>>>>>>> targeted-absa-2
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(255), nullable=False)
    source_text = Column(Text, nullable=True)
    aspect = Column(String(100), nullable=False)
    sentiment = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
<<<<<<< HEAD
    correction = Column(String(50), nullable=True) # Human-in-the-loop correction
=======
    correction = Column(String(50), nullable=True)
>>>>>>> targeted-absa-2
    processed_at = Column(DateTime, default=datetime.utcnow)

def create_tables(connection_string):
    engine = create_engine(connection_string)
<<<<<<< HEAD
    Base.metadata.create_all(engine)
=======
    Base.metadata.create_all(engine)
>>>>>>> targeted-absa-2
