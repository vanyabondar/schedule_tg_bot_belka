from typing import Optional

from db import Worker, Shift, Schedule


class WorkerGA:
    id: int
    rating: float
    coefficient: float

    def __init__(self, worker: Optional[Worker] = None):
        if worker:
            self.id = worker.chat_id
            self.rating = worker.rating
            self.coefficient = worker.coefficient
        else:
            self.id = -1
            self.rating = 0
            self.coefficient = 1

    def is_empty(self) -> bool:
        if self.id == -1:
            return True
        return False

    @classmethod
    def get_empty_worker(cls):
        return WorkerGA()


class ShiftGA:
    id: int
    cost: float
    available_workers: list[WorkerGA]
    final_worker: WorkerGA

    def __init__(self, shift: Shift):
        self.id = shift.shift_id
        self.cost = shift.cost * shift.coefficient
        self.available_workers = []
        self.add_worker(WorkerGA.get_empty_worker())
        self.final_worker = None

    def add_worker(self, worker: WorkerGA):
        self.available_workers.append(worker)


def from_db_objects_to_ga(shifts: list[Shift], workers: list[Worker]) -> (list[ShiftGA], list[WorkerGA]):
    shifts_ga = [ShiftGA(shift) for shift in shifts]
    workers_ga = []

    for worker in workers:
        if worker.is_done:
            worker_ga = WorkerGA(worker)
            workers_ga.append(worker_ga)
            shift_ids = [shift.shift_id for shift in worker.shifts]
            for shift in shifts_ga:
                if shift.id in shift_ids:
                    shift.add_worker(worker_ga)

    return shifts_ga, workers_ga


def from_ga_schedule_to_db(ga_schedule: list[ShiftGA]) -> list[Schedule]:
    schedule_db = []
    for ga_shift in ga_schedule:
        schedule_db.append(Schedule(shift_id=ga_shift.id,
                                    chat_id=ga_shift.final_worker.id,
                                    rating=ga_shift.cost * ga_shift.final_worker.coefficient))

    return schedule_db

