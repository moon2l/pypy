import struct
from pypy.rpython.memory.simulator import MemorySimulator, MemorySimulatorError
from pypy.rpython.rarithmetic import r_uint


class address(object):
    def __new__(cls, intaddress=0):
        if intaddress == 0:
            null = cls.__dict__.get("NULL")
            if null is not None:
                return null
            cls.NULL = object.__new__(cls)
            return cls.NULL
        else:
            return object.__new__(cls)

    def __init__(self, intaddress=0):
        self.intaddress = intaddress

    def _getintattr(self): #needed to make _accessor easy
        return self.intaddress

    def __add__(self, offset):
        assert isinstance(offset, int)
        return address(self.intaddress + offset)

    def __sub__(self, other):
        if isinstance(other, int):
            return address(self.intaddress - other)
        else:
            return self.intaddress - other.intaddress

    def __cmp__(self, other):
        return cmp(self.intaddress, other.intaddress)

    def __repr__(self):
        return "<addr: %s>" % self.intaddress

    def _load(self, fmt):
        return simulator.getstruct(fmt, self.intaddress)

    def _store(self, fmt, *values):
        simulator.setstruct(fmt, self.intaddress, *values)

    def __nonzero__(self):
        return self.intaddress != 0
    

class _accessor(object):
    def __init__(self, addr):
        if addr == NULL:
            raise MemorySimulatorError("trying to access NULL pointer")
        self.intaddress = addr.intaddress
    def __getitem__(self, offset):
        result = simulator.getstruct(self.format,
                                     self.intaddress + offset * self.size)
        return self.convert_from(result[0])

    def __setitem__(self, offset, value):
        simulator.setstruct(self.format, self.intaddress + offset * self.size,
                            self.convert_to(value))
           
class _signed_accessor(_accessor):
    format = "l"
    size = struct.calcsize("l")
    convert_from = int
    convert_to = int

class _unsigned_accessor(_accessor):
    format = "L"
    size = struct.calcsize("L")
    convert_from = r_uint
    convert_to = long

class _char_accessor(_accessor):
    format = "c"
    size = struct.calcsize("c")
    convert_from = str
    convert_to = str

class _address_accessor(_accessor):
    format = "P"
    size = struct.calcsize("P")
    convert_from = address
    convert_to = address._getintattr


address.signed = property(_signed_accessor)
address.unsigned = property(_unsigned_accessor)
address.char = property(_char_accessor)
address.address = property(_address_accessor)

NULL = address()
simulator = MemorySimulator()

def raw_malloc(size):
    return address(simulator.malloc(size))

def raw_free(addr):
    simulator.free(addr.intaddress)

def raw_memcopy(addr1, addr2, size):
    simulator.memcopy(addr1.intaddress, addr2.intaddress, size)

def get_address_of_object(obj):
    return address(simulator.get_address_of_object(obj))

def get_py_object(address):
    return simulator.get_py_object(address.intaddress)


from pypy.rpython.lltypesystem import lltype
Address = lltype.Primitive("Address", NULL)

address._TYPE = Address

supported_access_types = {"signed":    lltype.Signed,
                          "unsigned":  lltype.Unsigned,
                          "char":      lltype.Char,
                          "address":   Address,
                          }

# sizeof, offsetof

from pypy.rpython.objectmodel import Symbolic

class OffsetOf(Symbolic):

    def __init__(self, TYPE, *fldnames):
        self.TYPE = TYPE
        self.fldnames = fldnames

    def annotation(self):
        from pypy.annotation import model
        return model.SomeOffset()

    def lltype(self):
        return Offset

    def __repr__(self):
        return "<OffsetOf %r %r>" % (self.TYPE, self.fldnames)

    def __add__(self, other):
        if not isinstance(other, OffsetOf):
            return NotImplemented
        t = self.TYPE
        for f in self.fldnames:
            t = t._flds[f]
        assert t == other.TYPE
        return OffsetOf(self.TYPE, *(self.fldnames + other.fldnames))

Offset = lltype.Primitive("Offset", OffsetOf(lltype.Void))

def sizeof(TYPE, n=None):
    pass

def offsetof(TYPE, fldname):
    assert fldname in TYPE._flds
    return OffsetOf(TYPE, fldname)

def itemoffsetof(TYPE, n=None):
    pass

class fakeaddress(object):
    def __init__(self, ob, offset=None):
        self.ob = ob
        if offset is None:
            self.offset = OffsetOf(self.ob._TYPE)
        else:
            self.offset = offset

    def __add__(self, other):
        if not isinstance(other, OffsetOf):
            return NotImplemented
        return fakeaddress(self.ob, self.offset + other)
    
class _fakeaccessor(object):
    def __init__(self, addr):
        self.addr = addr
    def __getitem__(self, index):
        assert index == 0
        ob = self.addr.ob
        for n in self.addr.offset.fldnames:
            ob = getattr(ob, n)
        # XXX will need to do pointers differently!
        assert lltype.typeOf(ob) == self.TYPE 
        return ob
        
class _signed_fakeaccessor(_fakeaccessor):
    TYPE = lltype.Signed

fakeaddress.signed = property(_signed_fakeaccessor)
