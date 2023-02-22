from sqlalchemy import Table, Column, ForeignKey, create_engine
from sqlalchemy import DateTime, String, BigInteger, Integer, Boolean, Float
from sqlalchemy.orm import relationship, Session, backref, declarative_base
from dotenv import dotenv_values
from sqlalchemy_enum34 import EnumType
from config import RequestType

Base = declarative_base()

worker_shift = Table(
    'worker_shift', Base.metadata,
    Column('worker_shift_id', BigInteger(), primary_key=True),
    Column('worker_id', BigInteger(), ForeignKey('workers.chat_id')),
    Column('shift_id', BigInteger(), ForeignKey('shifts.shift_id'))
)


class WorkerCommand(Base):
    __tablename__ = 'worker_commands'
    worker_id = Column(ForeignKey('workers.chat_id'), primary_key=True),
    command_id = Column(ForeignKey('command.command_id'), primary_key=True),
    message_id = Column(BigInteger(), nullable=False),
    coefficient = Column(Float(), default=1)

    worker = relationship('Worker', back_populates='commands')
    command = relationship('Command', back_populates='workers')


command = relationship("Command", cascade="all,delete", backref="shift")


class Worker(Base):
    __tablename__ = 'workers'
    chat_id = Column(BigInteger(), primary_key=True, autoincrement=False)
    username = Column(String(50), nullable=False)
    rating = Column(Float(), nullable=False)
    is_admin = Column(Boolean(), default=False)

    shifts = relationship(
        'Shift',
        lazy='subquery',
        secondary=worker_shift,
        backref='workers'
    )
    commands = relationship('WorkerCommand', back_populates='worker')


class Shift(Base):
    __tablename__ = 'shifts'
    shift_id = Column(BigInteger(), primary_key=True)
    name = Column(String(50), nullable=False)
    cost = Column(Float(), nullable=False)
    has_worker = Column(Boolean(), default=False)
    coefficient = Column(Float(), default=1)
    time_start = Column(DateTime(), nullable=False)
    time_finish = Column(DateTime(), nullable=False)
    creation_command_id = Column(Integer(), ForeignKey('commands.command_id'))

    def __str__(self):
        return f'{self.name} has_worker: {self.has_worker}'


class Command(Base):
    __tablename__ = 'commands'
    command_id = Column(Integer(), primary_key=True)
    message_id = Column(BigInteger())
    chat_id = Column(BigInteger(), ForeignKey('workers.chat_id'))
    name = Column(String(50), nullable=False)
    start_time = Column(DateTime())
    end_time = Column(DateTime())
    step = Column(Integer())
    is_done = Column(Boolean(), default=False)

    workers = relationship('WorkerCommand', back_populates='command')


class RequestToAdmin(Base):

    # https://medium.com/uncountable-engineering/coherent-python-and-postgresql-enums-using-sqlalchemy-3bb23d9d369a
    # SqlRequestType = Enum(
    #     RequestType,
    #     name='request_type',
    #     values_callable=lambda obj: [e.value for e in obj]
    # )

    __tablename__ = 'requests_to_admin'
    request_id = Column(Integer(), primary_key=True)
    chat_id = Column(BigInteger(), ForeignKey('workers.chat_id'))
    message_id = Column(BigInteger(), nullable=False)
    request_type = Column(EnumType(RequestType, name='request_type'), nullable=False)
    new_worker_chat_id = Column(BigInteger(), default=None)


class Schedule(Base):
    __tablename__ = 'schedule'
    schedule_id = Column(BigInteger(), primary_key=True)
    shift_id = Column(BigInteger(), ForeignKey('shifts.shift_id'))
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

    def __str__(self):
        return f'shift_id = {self.shift_id} worker_id = {self.chat_id}'


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
    # session.add(w2)

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


def create_db(eng):
    Base.metadata.drop_all(eng)
    # Base.metadata.create_all(engine)


if __name__ == "__main__":
    config = dotenv_values()
    engine = create_engine(
        config['DB_CONF'],
        echo=True
    )

    create_db(engine)
    # init_db()
