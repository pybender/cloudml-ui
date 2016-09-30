import numpy
from psycopg2.extensions import register_adapter, AsIs
def addapt_numpy_float32(numpy_float32):
    return AsIs(numpy_float32)

register_adapter(numpy.float32, addapt_numpy_float32)

def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)

register_adapter(numpy.float64, addapt_numpy_float64)