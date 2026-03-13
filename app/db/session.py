from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = "sqlite:///movie_recommender.db"

# echo=False keeps startup quieter while still focused on feature work instead of raw SQL logging.
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session