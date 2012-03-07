from pypy.interpreter.gateway import unwrap_spec
from pypy.module.struct.formatiterator import PackFormatIterator, UnpackFormatIterator
from pypy.rlib import jit
from pypy.rlib.rstruct.error import StructError
from pypy.rlib.rstruct.formatiterator import CalcSizeFormatIterator


@unwrap_spec(format=str)
def calcsize(space, format):
    return space.wrap(_calcsize(space, format))

def _calcsize(space, format):
    fmtiter = CalcSizeFormatIterator()
    try:
        fmtiter.interpret(format)
    except StructError, e:
        raise e.at_applevel(space)
    return fmtiter.totalsize

@unwrap_spec(format=str)
def pack(space, format, args_w):
    if jit.isconstant(format):
        size = _calcsize(space, format)
    else:
        size = 8
    fmtiter = PackFormatIterator(space, args_w, size)
    try:
        fmtiter.interpret(format)
    except StructError, e:
        raise e.at_applevel(space)
    return space.wrap(fmtiter.result.build())


@unwrap_spec(format=str, input='bufferstr')
def unpack(space, format, input):
    fmtiter = UnpackFormatIterator(space, input)
    try:
        fmtiter.interpret(format)
    except StructError, e:
        raise e.at_applevel(space)
    return space.newtuple(fmtiter.result_w[:])
