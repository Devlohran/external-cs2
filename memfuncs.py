import pymem
import struct
from pymem import Pymem
from pymem.process import module_from_name
from ext_types import * 

class memfunc:
    
    def __init__(self):
        # Obtém o identificador do processo e cria uma instância de Pymem
        process = pymem.process.process_from_name("cs2.exe")
        self.pm = Pymem(process.th32ProcessID)
        self.client_dll_base = module_from_name(self.pm.process_handle, "client.dll")
        self.base_address = self.client_dll_base.lpBaseOfDll
        self.matchmaking_dll_base = module_from_name(self.pm.process_handle, "matchmaking.dll")
        self.matchmaking_base_address = self.matchmaking_dll_base.lpBaseOfDll

    def searchcliente(self):
        return self.base_address
    
    def search_matchmaking(self):
        return self.matchmaking_base_address

    def ReadPointer(self, addy, offset=0):
        address = addy + offset
        return self.pm.read_longlong(address)

    def ReadBytes(self, addy, bytes_count):
        return self.pm.read_bytes(addy, bytes_count)

    def WriteBytes(self, address, newbytes):
        return self.pm.write_bytes(address, newbytes, len(newbytes))

    def ReadInt(self, address, offset=0):
        return self.pm.read_int(address + offset)

    def ReadLong(self, address, offset=0):
        return self.pm.read_longlong(address + offset)

    def ReadFloat(self, address, offset=0):
        return self.pm.read_float(address + offset)

    def ReadDouble(self, address, offset=0):
        return self.pm.read_double(address + offset)

    def ReadVec(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 12)
        x, y, z = struct.unpack('fff', bytes_)
        return Vector3(x, y, z)

    def ReadShort(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('h', bytes_)[0]

    def ReadUShort(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('H', bytes_)[0]

    def ReadUInt(self, address, offset=0):
        return self.pm.read_uint(address + offset)

    def ReadULong(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 8)
        return struct.unpack('Q', bytes_)[0]

    def ReadBool(self, address, offset=0):
        return self.pm.read_bool(address + offset)

    def ReadString(self, address, length, offset=0):
        return self.pm.read_string(address + offset, length)

    def ReadChar(self, address, offset=0):
        bytes_ = self.ReadBytes(address + offset, 2)
        return struct.unpack('c', bytes_)[0].decode('utf-8')

    def ReadMatrix(self, address):
        bytes_ = self.ReadBytes(address, 4 * 16)
        matrix = struct.unpack('16f', bytes_)
        return matrix

    def WriteInt(self, address, value, offset=0):
        return self.pm.write_int(address + offset, value)

    def WriteShort(self, address, value, offset=0):
        bytes_ = struct.pack('h', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteUShort(self, address, value, offset=0):
        bytes_ = struct.pack('H', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteUInt(self, address, value, offset=0):
        return self.pm.write_uint(address + offset, value)

    def WriteLong(self, address, value, offset=0):
        return self.pm.write_longlong(address + offset, value)

    def WriteULong(self, address, value, offset=0):
        bytes_ = struct.pack('Q', value)
        return self.WriteBytes(address + offset, bytes_)

    def WriteFloat(self, address, value, offset=0):
        return self.pm.write_float(address + offset, value)

    def WriteDouble(self, address, value, offset=0):
        return self.pm.write_double(address + offset, value)

    def WriteBool(self, address, value, offset=0):
        return self.pm.write_bool(address + offset, value)

    def WriteString(self, address, value, offset=0):
        return self.pm.write_string(address + offset, value)

    def WriteVec(self, address, value, offset=0):
        bytes_ = struct.pack('fff', value.X, value.Y, value.Z)
        return self.WriteBytes(address + offset, bytes_)
