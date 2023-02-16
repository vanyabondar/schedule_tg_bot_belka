from enum import Enum


# Logging config
LOG_FILE = 'out.log'
LOG_ROTATION = '1 month'


MAX_SHIFTS_IN_ONE_SCHEDULE = 50
CHECK_END_SCHEDULE_CREATING_TIME = 20

# Worker's coefficient config
MIN_WORKER_COEFF = 1
MAX_WORKER_COEFF = 1.3
WORKER_COEFF_DEGREE = 1  # [0..1]

# Shift's coefficients
SHIFT_COEFFICIENTS = {
    0: 2.0,
    1: 1.4,
    2: 1.2,
    3: 1.1,
    4: 1.04
}


# Enum for types of request
class RequestType(Enum):
    NEW_WORKER = 'NEW_WORKER'
