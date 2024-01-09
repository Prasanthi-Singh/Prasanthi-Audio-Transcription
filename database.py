from sqlalchemy import create_engine, Column, Integer, String, Sequence , DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Replace the following with your PostgreSQL database URL
# Format: "postgresql://username:password@localhost:5432/your_database"
db_url = "postgresql://postgres:prasanthi@localhost:5433/kyro"

# Create a SQLAlchemy engine
engine = create_engine(db_url)

# # Define the User model
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50))
    age = Column(Integer)
    
class Transcripts(Base):
    __tablename__ = 'transcripts'
    transcript_id = Column(Integer,primary_key=True, autoincrement=True)
    user_id = Column(String)
    transcript = Column(String)
    created_at = Column(DateTime, default=func.now())

    

# Create the table in the database
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

