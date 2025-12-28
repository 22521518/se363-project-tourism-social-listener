from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, AbsaResultModel

class AbsaDAO:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def save_batch(self, results):
        session = self.Session()
        try:
            models = []
            for r in results:
                model = AbsaResultModel(
                    source_id=r.source_id,
                    source_text=r.source_text,
                    aspect=r.aspect,
                    sentiment=r.sentiment,
                    confidence=r.confidence
                )
                models.append(model)
            session.add_all(models)
            session.commit()
            print(f'DAO: Saved {len(models)} records')
        except Exception as e:
            session.rollback()
            print(f'DAO Error: {e}')
        finally:
            session.close()

    def get_all_results(self):
        session = self.Session()
        try:
            return session.query(AbsaResultModel).order_by(AbsaResultModel.processed_at.desc()).limit(200).all()
        finally:
            session.close()

    def update_correction(self, id, new_sentiment):
        session = self.Session()
        try:
            record = session.query(AbsaResultModel).filter_by(id=id).first()
            if record:
                record.correction = new_sentiment
                session.commit()
                return True
            return False
        finally:
            session.close()
