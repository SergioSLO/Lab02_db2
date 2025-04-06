import csv
import struct
import time


class Venta:
    FORMAT = 'i30sif10siii'
    STRUCT = struct.Struct(FORMAT)
    RECORD_SIZE = struct.calcsize(FORMAT)
    def __init__(self,
                 id_venta : int = -1,
                 nombre : str = "" ,
                 cant: int = 0,
                 precio_u: float = 0,
                 fecha: str = "",
                 der:int = -1,
                 izq:int = -1,
                 height = 0):
        self.id_venta = id_venta
        self.nombre = nombre
        self.cant = cant
        self.precio_u = precio_u
        self.fecha = fecha
        self.der = der
        self.izq = izq
        self.height = height

    def __str__(self):
        return str(self.__dict__)

    def unpack(self, data: bytes):
        """
        Desempaqueta los datos binarios de una tupla
        input: bytes
        """
        l = self.STRUCT.unpack(data)
        self.id_venta = l[0]
        self.nombre = l[1].decode().strip("\x00")
        self.cant = l[2]
        self.precio_u = round(l[3],2)
        self.fecha = l[4].decode()
        self.der = l[5]
        self.izq = l[6]
        self.height = l[7]

    def pack(self)-> bytes:
        """
        Empaqueta los datos de una tupla a binario
        return: bytes
        """
        return self.STRUCT.pack(self.id_venta,
                               self.nombre.encode(),
                               self.cant,
                               self.precio_u,
                               self.fecha.encode(),
                               self.der,
                               self.izq,
                            self.height)

class AVL_db:
    HEADER_FORMAT = 'i'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    def __init__(self, name:str):
        """
        Inicializa la base de datos AVL
        input: name: str
        """
        if name[-4:] == ".csv": # si es un csv
            self.name = name[:-4] + ".dat" # creamos a parte un archivo .dat
            open(self.name, 'ab').close() # crea el archivo si no existe
            with open(self.name, 'wb') as file:
                self.root = 0
                header = struct.pack(self.HEADER_FORMAT, self.root) # escribimos la cabecera
                file.write(header)
            self.open_csv(name) # ahora si abrimos el csv

        else:
            open(name, 'ab').close() # crea el archivo si no existe
            self.name = name # asignamos el nombre
            with open(self.name, 'rb+') as file:
                header = file.read(self.HEADER_SIZE)
                if not header: # si existe el archivo pero no tiene cabecera
                    self.root = 0
                    header = struct.pack(self.HEADER_FORMAT, self.root) # escribimos la cabecera
                    file.write(header)
                else:
                    self.root = struct.unpack(self.HEADER_FORMAT, header)[0] # leemos la cabecera

    def open_csv(self, name:str):
        """
        Abre el archivo csv y lo carga a la base de datos
        input: name: str del archivo .csv, el archivo .dat esta en self.name
        """
        with open(name, "r", encoding='utf-8') as file:
            csv_data = csv.reader(file)
            next(csv_data) # saltar cabecera
            for row in csv_data:
                data = Venta(int(row[0]),row[1],int(row[2]),float(row[3]),row[4]) # cada fila es una tupla
                self.add(data) # lo añadimos a la bd

    def get(self, pos:int)->Venta | None:
        """
        Obtiene una tupla de la base de datos
        input: pos: int
        return: Venta | None: la tupla o None si no existe
        """
        if pos < 0: # si la posicion es negativa
            return None
        with (open(self.name, 'rb') as file):
            tupla = Venta()
            file.seek(self.HEADER_SIZE + (pos * tupla.RECORD_SIZE)) # nos movemos a la posicion
            data = file.read(tupla.RECORD_SIZE)
            if not data: # si no hay datos
                return None
            tupla.unpack(data) # desempaquetamos
            return tupla # devuelve la tupla

    def post(self, data: Venta) -> int:
        """
        Añade una tupla a la base de datos
        input: data: Venta
        return: int: la posicion de la tupla añadida
        """
        with open(self.name, 'ab') as file:
            pos = (file.tell() - self.HEADER_SIZE) // data.RECORD_SIZE # guardamos el nro de tupla que añadiremos
            file.write(data.pack()) # escribimos la tupla
            return pos

    def patch(self, pos, data:Venta):
        """
        Actualiza una tupla en la base de datos
        input: pos: int, data: Venta: el nro de tupla y la tupla a actualizar
        """
        with open(self.name, 'rb+') as file:
            file.seek(self.HEADER_SIZE + (pos * data.RECORD_SIZE))
            file.write(data.pack())

    def put_header(self, root:int):
        """
        Actualiza la cabecera de la base de datos
        input: root: int: la nueva raiz del árbol
        """
        self.root = root # en memoria ram
        with open(self.name, 'rb+') as file:
            file.write(struct.pack('i', root)) # en memoria secundaria

    def search(self, id_venta:int, pos:int):
        """
        Busca una tupla en la base de datos
        input: id_venta: int, pos: int
        return: int: la posicion de la tupla o -1 si no existe
        """
        if pos == -1:
            return pos
        punt = self.get(pos) # obtenemos la tupla y realizamos busqueda binaria
        if punt is None:
            return -1
        if id_venta == punt.id_venta:
            return pos
        if id_venta > punt.id_venta:
            return self.search(id_venta,punt.der)
        if id_venta < punt.id_venta:
            return self.search(id_venta,punt.izq)

    def load(self)-> list[Venta]:
        """
        Carga todas las tuplas de la base de datos
        return: list: lista de tuplas
        """
        ret = []
        ite = 0
        now = self.get(ite)
        while now:
            ret.append(now)
            ite += 1
            now = self.get(ite)
        return ret

    def update_height(self, nodo: Venta) -> int:
        """
        Actualiza la altura de un nodo
        input: nodo: Venta
        return: int: la altura del nodo
        """
        if nodo:
            if nodo.izq == -1 and nodo.der == -1:
                return 0
            else:
                d_h = 0 if nodo.der == -1 else self.get(nodo.der).height # si tiene nodo derecho, tomamos su altura
                i_h = 0 if nodo.izq == -1 else self.get(nodo.izq).height # si tiene nodo izquierdo, tomamos su altura
                return max(d_h,i_h) + 1

    def get_balance(self, nodo: Venta) -> int:
        """
        Calcula el balance de un nodo
        input: nodo: Venta
        return: int: el balance del nodo
        """
        d = 0 if nodo.der == -1 else 1 + self.get(nodo.der).height # si tiene nodo derecho, tomamos su altura + 1
        i = 0 if nodo.izq == -1 else 1 + self.get(nodo.izq).height # si tiene nodo izquierdo, tomamos su altura + 1

        return i - d

    def right_rotate(self,y:Venta, pos_y:int, x:Venta, pos_x:int):
        """
        Rotacion a la derecha
        input: y: Venta, pos_y: int, x: Venta, pos_x: int
            donde x = y->izq
        return: int: la nueva posicion de la raiz
        """
        t2 = x.der # guardamos el nodo derecho de x
        x.der = pos_y # x se convierte en la raiz
        y.izq = t2 # el nodo derecho de x se convierte en el izquierdo de y
        y.height = self.update_height(y) # actualizamos la altura de y
        self.patch(pos_y,y) # actualizamos la tupla en el archivo
        x.height = self.update_height(x) # actualizamos la altura de x
        self.patch(pos_x,x) # actualizamos la tupla en el archivo
        return pos_x


    def left_rotate(self,x:Venta, pos_x:int, y:Venta, pos_y:int):
        """
        Rotacion a la izquierda
        input: x: Venta, pos_x: int, y: Venta, pos_y: int
            donde y = x->der
        return: int: la nueva posicion de la raiz
        """
        t2 = y.izq # guardamos el nodo izquierdo de y
        y.izq = pos_x # y se convierte en la raiz
        x.der = t2 # el nodo izquierdo de y se convierte en el derecho de x
        x.height = self.update_height(x) # actualizamos la altura de x
        self.patch(pos_y,y) # actualizamos la tupla en el archivo
        y.height = self.update_height(y) # actualizamos la altura de y
        self.patch(pos_x,x) # actualizamos la tupla en el archivo
        return pos_y


    def addaux(self, venta: Venta, pos: int):
        """
        Añade una tupla a la base de datos
        input: venta: Venta, pos: int
        return: int: la posicion de la tupla añadida
        """
        if pos == -1: # si la posicion es -1
            return self.post(venta)
        punt = self.get(pos) # obtenemos la tupla
        if punt is None: # si no existe
            return self.post(venta)

        # si existe, buscamos recursivamente una hoja donde insertarlo
        if venta.id_venta > punt.id_venta:
            punt.der = self.addaux(venta, punt.der)
        elif venta.id_venta < punt.id_venta:
            punt.izq = self.addaux(venta, punt.izq)

        # una vez insertado, actualizamos la altura y balance del nodo
        punt.height = self.update_height(punt)
        balance = self.get_balance(punt)

        # si el nodo se desbalancea, hay 4 casos
        der = self.get(punt.der)
        izq = self.get(punt.izq)

        # caso rotacion derecha
        if balance > 1 and venta.id_venta < izq.id_venta:
            if pos == self.root: # si es la raiz, la nueva raiz es el hijo izquierdo
                self.put_header(punt.izq)

            return self.right_rotate(punt, pos, izq, punt.izq)

        # caso rotacion izquierda
        if balance < -1 and venta.id_venta > der.id_venta:
            if pos == self.root: # si es la raiz, la nueva raiz es el hijo derecho
                self.put_header(punt.der)

            return self.left_rotate(punt, pos, der, punt.der)

        # caso rotacion izquierda-derecha
        if balance > 1 and venta.id_venta > izq.id_venta:
            if pos == self.root: # si es la raiz, la nueva raiz es el hijo derecho del izquierdo
                self.put_header(izq.der)

            l_r = self.get(izq.der) # guardamos el nodo derecho del izquierdo
            punt.izq = self.left_rotate(izq, punt.izq, l_r, izq.der) # rotamos el izquierdo
            return self.right_rotate(punt, pos, l_r, punt.izq) # rotamos el padre

        # caso rotacion derecha-izquierda
        if balance < -1 and venta.id_venta < der.id_venta:
            if pos == self.root: # si es la raiz, la nueva raiz es el hijo izquierdo del derecho
                self.put_header(der.izq)

            r_l = self.get(der.izq) # guardamos el nodo izquierdo del derecho
            punt.der = self.right_rotate(der, punt.der, r_l, der.izq) # rotamos el derecho
            return self.left_rotate(punt, pos, r_l, punt.der) # rotamos el padre

        # si no se desbalancea, actualizamos la tupla en el archivo
        self.patch(pos, punt)
        return pos


    def add(self, record:Venta):
        """
        Añade una tupla a la base de datos
        input: record: Venta
        """
        if self.search(record.id_venta, self.root) != -1:
            print("id repetido")
            return
        self.addaux(record, self.root)



    def read_record(self, id_venta:int):
        """
        Busca una tupla en la base de datos
        input: id_venta: int
        """
        return self.get(self.search(id_venta,0))


ventas = [Venta(0, "Berenjena", 10, 2.5, "2025-15-10"), Venta(1, "Yucas", 30, 3.2, "2025-12-27"),
          Venta(2, "Camotes", 20, 2.2, "2025-12-26"), Venta(3, "Choclo", 40, 4.2, "2025-12-28"),
          Venta(4, "Papas", 10, 1.2, "2025-12-25"), Venta(5, "Arroz", 50, 5.2, "2025-12-29"),
          Venta(6, "Maíz", 60, 3.8, "2025-12-30"), Venta(7, "Frijoles", 70, 6.5, "2025-12-31"),
          Venta(8, "Lentejas", 80, 2.5, "2026-01-01"), Venta(9, "Tomates", 90, 1.9, "2026-01-02"),
          Venta(10, "Cebollas", 100, 4.0, "2026-01-03")]

start_time = time.time()
bd = AVL_db('prueba.dat')
end_time = time.time()
for i in [0, 5, 10, 1, 2, 3, 4, 6, 7, 8]:
    bd.add(ventas[i])


r = bd.load()
ite = 0
for i in r:
    print(ite," : ",i)
    ite += 1

print("Raiz del AVL: ",bd.root)

print("Tiempo de inserción", end_time - start_time)
