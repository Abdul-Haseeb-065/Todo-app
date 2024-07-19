from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from docker_todoo import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select, Sequence
from fastapi import FastAPI, Depends
from typing import AsyncGenerator


class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(index=True)

# database_url = ("postgresql://neondb_owner:e4WkhBb3uQIr@ep-yellow-violet-a59ee4pe.us-east-2.aws.neon.tech/Todo_app?sslmode=require")

# only needed for psycopg 3 - replace postgresql
# with postgresql+psycopg in settings.DATABASE_URL
connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


# recycle connections after 5 minutes
# to correspond with the compute scale down
engine = create_engine(
    connection_string, connect_args={}, pool_recycle=300
)

#engine = create_engine(
#    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
#)


def create_db_and_tables()->None:
    SQLModel.metadata.create_all(engine)


# The first part of the function, before the yield, will
# be executed before the application starts.
# https://fastapi.tiangolo.com/advanced/events/#lifespan-function
@asynccontextmanager
async def lifespan(app: FastAPI)-> AsyncGenerator[None, None]:
    print("Creating tables..")
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://127.0.0.1:8000", # ADD NGROK URL Here Before Creating GPT Action
            "description": "Development Server"
        }
        ])

def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/todos/", response_model=Todo)
def create_todo(todo: Todo, session: Annotated[Session, Depends(get_session)])->Todo:
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


@app.get("/todos/", response_model=list[Todo])
def read_todos(session: Annotated[Session, Depends(get_session)]):
        todos = session.exec(select(Todo)).all()
        return todos



@app.put("/todos/", response_model=Todo )
def update_todos(todo: Todo, session: Annotated[Session, Depends(get_session)]):
        statement = select(Todo).where(Todo.id == todo.id)
        results = session.exec(statement)
        db_todo = results.one()

        db_todo.content = todo.content
        session.add(db_todo)
        session.commit()
        session.refresh(db_todo)
        return db_todo

@app.delete("/todos/")
def delete_todos(todo: Todo, session: Annotated[Session, Depends(get_session)]):
        statement = select(Todo).where(Todo.id == todo.id)
        results = session.exec(statement)
        db_todo = results.one()
        session.delete(db_todo)
        session.commit()    
        return "Todo Deleted Successfully......"    
        