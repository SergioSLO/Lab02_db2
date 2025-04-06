import struct

class Venta:
    FORMAT = 'i30sif10sii'
    STRUCT = struct.Struct(FORMAT)
    RECORD_SIZE = struct.calcsize(FORMAT)
    def __init__(self,
                 id_venta : int = -1,
                 nombre : str = "" ,
                 cant: int = 0,
                 precio_u: float = 0,
                 fecha: str = "",
                 der:int = -1,
                 izq:int = -1):
        self.id_venta = id_venta
        self.nombre = nombre
        self.cant = cant
        self.precio_u = precio_u
        self.fecha = fecha
        self.der = der
        self.izq = izq

    def __bool__(self):
        return self.id_venta != -1

    def __str__(self):
        return str(self.__dict__)

    def unpack(self, data: bytes):
        l = self.STRUCT.unpack(data)
        self.id_venta = l[0]
        self.nombre = l[1].decode().strip("\x00")
        self.cant = l[2]
        self.precio_u = round(l[3],2)
        self.fecha = l[4].decode()
        self.der = l[5]
        self.izq = l[6]

    def pack(self):
        return self.STRUCT.pack(self.id_venta,
                               self.nombre.encode(),
                               self.cant,
                               self.precio_u,
                               self.fecha.encode(),
                               self.der,
                               self.izq)


class BST_db:
    def __init__(self, name:str):
        open(name, 'ab').close()
        self.name = name

    def get(self, pos:int)->Venta | None:
        if pos < 0:
            return None
        with (open(self.name, 'rb') as file):
            tupla = Venta()
            file.seek(pos * tupla.RECORD_SIZE)
            data = file.read(tupla.RECORD_SIZE)
            if not data:
                return None
            tupla.unpack(data)
            return tupla

    def post(self, data: Venta):
        with open(self.name, 'ab') as file:
            pos = file.tell()
            file.write(data.pack())
            return pos

    def patch(self, pos, data:Venta):
        with open(self.name, 'rb+') as file:
            file.seek(pos * data.RECORD_SIZE)
            file.write(data.pack())

    def search(self, id_venta:int, pos:int):
        if pos == -1:
            return pos
        punt = self.get(pos)
        if not punt or punt is None:
            return -1
        if id_venta == punt.id_venta:
            return pos
        if id_venta > punt.id_venta:
            return self.search(id_venta,punt.der)
        if id_venta < punt.id_venta:
            return self.search(id_venta,punt.izq)



    def load(self):
        ret = []
        ite = 0
        now = self.get(ite)
        while now:
            ret.append(now)
            ite+=1
            now = self.get(ite)
        return ret

    def addaux(self, venta: Venta, pos: int):
        punt = self.get(pos)
        if not punt:
            self.post(venta)
            return
        if venta.id_venta == punt.id_venta:
            print("id repetido")
            return
        if venta.id_venta > punt.id_venta:
            if punt.der == -1:
                punt.der = (self.post(venta) // venta.RECORD_SIZE)
                self.patch(pos,punt)
                return
            return self.addaux(venta, punt.der)
        if venta.id_venta < punt.id_venta:
            if punt.izq == -1:
                punt.izq = (self.post(venta) // venta.RECORD_SIZE)
                self.patch(pos,punt)
                return
            return self.addaux(venta, punt.izq)

    def add(self, record:Venta):
        self.addaux(record, 0)



    def read_record(self, id_venta:int):
        return self.get(self.search(id_venta,0))




venta1 = Venta(3,"Yucas",30,3.2,"2025-12-27")
venta2 = Venta(2,"Camotes",20,2.2,"2025-12-26")
venta3 = Venta(4,"Choclo",40,4.2,"2025-12-28")
venta4 = Venta(1,"Papas",10,1.2,"2025-12-25")
venta5 = Venta(5,"Arroz",50,5.2,"2025-12-29")
venta6 = Venta(6, "Maíz", 60, 3.8, "2025-12-30")
venta7 = Venta(7, "Frijoles", 70, 6.5, "2025-12-31")
venta8 = Venta(8, "Lentejas", 80, 2.5, "2026-01-01")
venta9 = Venta(9, "Tomates", 90, 1.9, "2026-01-02")
venta10 = Venta(10, "Cebollas", 100, 4.0, "2026-01-03")
bd = BST_db('data.dat')
bd.add(venta1)
bd.add(venta2)
bd.add(venta3)
bd.add(venta4)
bd.add(venta5)
bd.add(venta6)
bd.add(venta7)
bd.add(venta8)
bd.add(venta9)
bd.add(venta10)
r = bd.load()

for i in r:
    print(i)
print("-"*100)
print(bd.read_record(4))
