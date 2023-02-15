import enum
from sqlalchemy import Table, Column, ForeignKey, create_engine
from sqlalchemy import DateTime, String, BigInteger, Integer, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session, backref
from sqlalchemy import Enum
from dotenv import dotenv_values

Base = declarative_base()

worker_shift = Table(
    'worker_shift', Base.metadata,
    Column('worker_shift_id', Integer(), primary_key=True),
    Column('worker_id', BigInteger(), ForeignKey('workers.chat_id')),
    Column('shift_id', Integer(), ForeignKey('shifts.shift_id'))
)


class Worker(Base):
    __tablename__ = 'workers'
    chat_id = Column(BigInteger(), primary_key=True, autoincrement=False)
    username = Column(String(50), nullable=False)
    rating = Column(Float(), nullable=False)
    message_id = Column(Integer())
    is_done = Column(Boolean(), default=False)
    is_admin = Column(Boolean(), default=False)
    coefficient = Column(Float(), default=1)

    shifts = relationship(
        'Shift',
        lazy='subquery',
        secondary=worker_shift,
        backref='workers'
    )


class Shift(Base):
    __tablename__ = 'shifts'
    shift_id = Column(Integer(), primary_key=True)
    name = Column(String(50), nullable=False)
    cost = Column(Float(), nullable=False)
    has_worker = Column(Boolean(), default=False)
    coefficient = Column(Float(), default=1)
    time_start = Column(DateTime(), nullable=False)
    time_finish = Column(DateTime(), nullable=False)

    def __str__(self):
        return f'{self.name} has_worker: {self.has_worker}'


class Command(Base):
    __tablename__ = 'commands'
    message_id = Column(Integer(), primary_key=True)
    chat_id = Column(BigInteger(), ForeignKey('workers.chat_id'))
    name = Column(String(50), nullable=False)
    start_time = Column(DateTime())
    end_time = Column(DateTime())
    step = Column(Integer())
    is_done = Column(Boolean(), default=False)


class RequestToAdmin(Base):

    class RequestType(enum.Enum):
        NEW_WORKER = 1

    __tablename__ = 'requests_to_admin'
    request_id = Column(Integer(), primary_key=True)
    chat_id = Column(BigInteger(), ForeignKey('workers.chat_id'))
    message_id = Column(Integer(), nullable=False)
    request_type = Column(Enum(RequestType), nullable=False)
    new_worker_chat_id = Column(BigInteger(), default=None)


class Schedule(Base):
    __tablename__ = 'schedule'
    schedule_id = Column(Integer(), primary_key=True)
    shift_id = Column(Integer(), ForeignKey('shifts.shift_id'))
    chat_id = Column(BigInteger(), ForeignKey('workers.chat_id'))
    rating = Column(Float(), nullable=False)
    is_notified = Column(Boolean(), default=False)
    confirm_by_admin = Column(Boolean(), default=False)

    shift = relationship(
        'Shift',
        backref=backref('schedule', uselist=False, cascade="all,delete"),
        lazy='joined',
        uselist=False,)
    worker = relationship(
        'Worker',
        backref='schedule',
        lazy='subquery',
        uselist=False)


def init_db():
    session = Session(bind=engine)

    w0 = Worker(
        chat_id=372805049,
        username='@elohssa',
        rating=50,
        is_admin=True
    )
    session.add(w0)
    w1 = Worker(
        chat_id=5018287782,
        username='@test',
        rating=20
    )
    session.add(w1)

    # w2 = Worker(
    #     chat_id=469094520,
    #     username='@Pingvinopitek',
    #     rating=35
    # )
    session.add(w2)

    # w3 = Worker(
    #     chat_id=395920445,
    #     username='@jetraid',
    #     rating=0
    # )
    # session.add(w3)

    session.add_all([w0, w1])
    # session.add_all([w0, w1, w2, w3])
    session.commit()
    session.close()


if __name__ == "__main__":
    config = dotenv_values()
    engine = create_engine(
        config['DB_CONF'],
        echo=True
    )
    Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    # init_db()
