import db

from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine, desc

from config import SHIFT_COEFFICIENTS

WORKER_COLUMNS = ['chat_id', 'username', 'rating', 'message_id', 'is_done']
SHIFT_COLUMNS = ['shift_id', 'name', 'cost', 'has_worker', 'coefficient']
# COMMAND_COLUMNS = ['message_id', 'chat_id', 'start_time', 'end_time', 'step', 'is_done']


class ScheduleDB:
    engine = None

    def __init__(self, db_path):
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)

    def get_worker(self, chat_id):
        session = self.Session()
        try:
            worker = session.query(db.Worker).get(chat_id)
        finally:
            session.close()
        return worker

    def get_worker_by_username(self, username):
        session = self.Session()
        try:
            worker = session.query(db.Worker).filter(
                db.Worker.username == username).first()
        finally:
            session.close()
        return worker

    def get_shift(self, shift_id):
        session = self.Session()
        try:
            shift = session.query(db.Shift).options(
                joinedload(db.Shift.schedule)).get(shift_id)
        finally:
            session.close()
        return shift

    def change_worker(self, chat_id, d):
        session = self.Session()
        try:
            w = session.query(db.Worker).get(chat_id)
            for key in d:
                setattr(w, key, d[key])
            session.add(w)
            session.commit()
        finally:
            session.close()

    def change_command(self, d):
        session = self.Session()
        try:
            command = self.get_command()
            for key in d:
                setattr(command, key, d[key])
            session.add(command)
            session.commit()
        finally:
            session.close()

    def get_all_workers(self):
        session = self.Session()
        try:
            workers = session.query(db.Worker).order_by(
                desc(db.Worker.rating)).all()
        finally:
            session.close()
        return workers

    def get_admins(self):
        session = self.Session()
        try:
            admins = session.query(db.Worker).filter(db.Worker.is_admin == True).all()
        finally:
            session.close()
        return admins

    def get_actual_shifts(self, command_id=None):
        session = self.Session()
        try:
            shifts_query = session.query(db.Shift).filter(
                db.Shift.has_worker == False).order_by(
                db.Shift.shift_id)
            if command_id:
                shifts_query.filter(db.Shift.creation_command_id == command_id)
            shifts = shifts_query.all()
        finally:
            session.close()
        return shifts

    def get_past_shifts(self, time):
        session = self.Session()
        try:
            shifts = session.query(db.Shift).options(
                joinedload(db.Shift.schedule)).filter(
                db.Shift.time_finish < time).order_by(
                db.Shift.time_start).all()
        finally:
            session.close()
        return shifts

    def change_all_worker(self, d):
        session = self.Session()
        try:
            workers = session.query(db.Worker).all()
            for w in workers:
                for key in d:
                    setattr(w, key, d[key])
                session.add(w)
            session.commit()
        finally:
            session.close()

    def clear_shifts(self):
        session = self.Session()
        try:
            shifts = session.query(db.Shift).all()
            for s in shifts:
                session.delete(s)
            session.commit()
        finally:
            session.close()

    def save_shifts(self, shifts):
        session = self.Session()
        try:
            for shift in shifts:
                session.add(shift)
            session.commit()
        finally:
            session.close()

    def update_shift_coefficients(self):
        session = self.Session()
        try:
            shifts = session.query(db.Shift).filter(
                db.Shift.has_worker == False)
            for s in shifts:
                if len(s.workers) in SHIFT_COEFFICIENTS:
                    s.coefficient = SHIFT_COEFFICIENTS[len(s.workers)]
                session.add(s)
            session.commit()
        finally:
            session.close()

    def update_shifts_has_worker(self, shift_ids, has_worker):
        session = self.Session()
        try:
            shifts = session.query(db.Shift).filter(db.Shift.shift_id.in_(shift_ids))

            for shift in shifts:
                shift.has_worker = has_worker
                session.add(shift)
            session.commit()
        finally:
            session.close()

    def save_worker(self, worker):
        session = self.Session()
        try:
            session.add(worker)
            session.commit()
        finally:
            session.close()

    def delete_worker(self, worker_id):
        session = self.Session()
        try:
            w = session.query(db.Worker).get(worker_id)
            session.delete(w)
            session.commit()
        finally:
            session.close()

    def delete_shift(self, shift_id):
        session = self.Session()
        try:
            s = session.query(db.Shift).get(shift_id)
            session.delete(s)
            session.commit()
        finally:
            session.close()

    # def print_all(self, table: str):
    #     d = {
    #         'workers': db.Worker,
    #         'shifts': db.Shift,
    #         'commands': db.Command
    #     }
    #     session = self.Session()
    #     try:
    #         rows = session.query(d[table]).all()
    #
    #         for row in rows:
    #             print(row)
    #     finally:
    #         session.close()

    def save_command(self, command):
        session = self.Session()
        try:
            c = session.query(db.Command).first()
            if c and c.is_done:
                session.delete(c)
                session.commit()
                session.add(command)
            elif c:
                c.step = command.step
                c.is_done = command.is_done
                session.add(c)
            else:
                session.add(command)
            session.commit()
        finally:
            session.close()

    def get_command(self):
        session = self.Session()
        try:
            res = session.query(db.Command).first()
        finally:
            session.close()
        return res

    def add_request_to_admin(self, chat_id, message_id, request_type, worker_chat_id):
        request = db.RequestToAdmin(
            chat_id=chat_id,
            message_id=message_id,
            request_type=request_type,
            new_worker_chat_id=worker_chat_id
        )

        session = self.Session()
        try:
            session.add(request)
            session.commit()
        finally:
            session.close()

    def get_requests_to_admin(self, key):
        session = self.Session()
        try:
            request = session.query(db.RequestToAdmin).filter(
                db.RequestToAdmin.new_worker_chat_id == key)
        finally:
            session.close()
        return request

    def delete_request(self, request_id):
        session = self.Session()
        try:
            r = session.query(db.RequestToAdmin).get(request_id)
            session.delete(r)
            session.commit()
        finally:
            session.close()

    def save_schedule(self, schedule, many=False):
        session = self.Session()
        try:
            if many:
                for s in schedule:
                    session.add(s)
            else:
                session.add(schedule)
            session.commit()
        finally:
            session.close()

    def get_schedule(self, chat_id=None, command_id=None):
        session = self.Session()
        try:
            schedule_query = session.query(db.Schedule).join(db.Shift).order_by(
                db.Schedule.shift_id)
            if chat_id:
                schedule_query = schedule_query.filter(
                    db.Schedule.chat_id == chat_id)
            if command_id:
                schedule_query = schedule_query.filter(
                    db.Shift.creation_command_id == command_id)
            sch = schedule_query.all()
        finally:
            session.close()
        return sch

    def delete_schedule(self, id):
        session = self.Session()
        try:
            sch = session.query(db.Schedule).get(id)
            session.delete(sch)
            session.commit()
        finally:
            session.close()

    def update_command_id_for_shifts(self, shifts, command_id):
        session = self.Session()
        try:
            for shift in shifts:
                shift.creation_command_id = command_id
                session.add(shift)
            session.commit()
        finally:
            session.close()
