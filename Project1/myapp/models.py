from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, TIMESTAMP, UniqueConstraint, CheckConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)

class Package(Base):
    __tablename__ = 'packages'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), nullable=False)
    author = Column(String(255))
    repository_id = Column(Integer, ForeignKey('repositories.id', ondelete="CASCADE"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    artifact_path = Column(Text)
    minio_url = Column(Text)
    tag = Column(String(100), nullable=True)  # New 'tag' column

    repository = relationship("Repository", back_populates="packages")

    __table_args__ = (UniqueConstraint('name', 'version', name='_unique_package_version'),)


   
Repository.packages = relationship("Package", order_by=Package.id, back_populates="repository")

class Dependency(Base):
    __tablename__ = 'dependencies'

    package_id = Column(Integer, ForeignKey('packages.id', ondelete="CASCADE"), primary_key=True)
    dependent_package_id = Column(Integer, ForeignKey('packages.id', ondelete="CASCADE"), primary_key=True)

    __table_args__ = (CheckConstraint('package_id <> dependent_package_id', name='prevent_cyclic_dependency'),)

class Config(Base):
    __tablename__ = 'config'

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)

DATABASE_URL = "postgresql://postgres:Os2ZoGMqD0GIoVwD@royally-beautiful-conger.data-1.use1.tembo.io:5432/postgres"

engine = create_engine(DATABASE_URL, echo = True)
SessionLocal = sessionmaker(bind=engine)
