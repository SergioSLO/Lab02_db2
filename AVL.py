import csv
import struct
import time
import matplotlib.pyplot as plt


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
        if name[-4:] == ".csv": # si es un csv
            self.name = name[:-4] + ".dat" # creamos a parte un archivo .dat
            open(self.name, 'wb').close() # crea el archivo si no existe
            with open(self.name, 'wb') as file:
                self.root = 0
                header = struct.pack(self.HEADER_FORMAT, self.root) # cabecera
                file.write(header)
            self.open_csv(name)

        else:
            open(name, 'ab').close() # crea el archivo si no existe
            self.name = name
            with open(self.name, 'rb+') as file:
                header = file.read(self.HEADER_SIZE)
                if not header:
                    self.root = 0
                    header = struct.pack(self.HEADER_FORMAT, self.root) # escribimos la cabecera
                    file.write(header)
                else:
                    self.root = struct.unpack(self.HEADER_FORMAT, header)[0] # leemos la cabecera

    def open_csv(self, name:str):
        """
        Abre el archivo csv y lo carga a la base de datos
        """
        with open(name, "r", encoding='utf-8') as file:
            csv_data = csv.reader(file)
            next(csv_data) # saltar cabecera
            for row in csv_data:
                data = Venta(int(row[0]),row[1],int(row[2]),float(row[3]),row[4]) # cada fila es una tupla
                self.add(data) # lo añadimos a la bd

    def get(self, pos:int)->Venta | None:
        if pos < 0: # no acepta posiciones negativas
            return None
        with (open(self.name, 'rb') as file):
            tupla = Venta()
            file.seek(self.HEADER_SIZE + (pos * tupla.RECORD_SIZE)) # nos movemos a la posicion
            data = file.read(tupla.RECORD_SIZE)
            if not data: # si no hay datos
                return None
            tupla.unpack(data)
            return tupla

    def post(self, data: Venta) -> int:
        """
        Añade una tupla a la base de datos
        """
        with open(self.name, 'ab') as file:
            pos = (file.tell() - self.HEADER_SIZE) // data.RECORD_SIZE # guardamos el nro de tupla que añadiremos
            file.write(data.pack())
            return pos

    def patch(self, pos, data:Venta):
        """
        Actualiza una tupla en la base de datos
        """
        with open(self.name, 'rb+') as file:
            file.seek(self.HEADER_SIZE + (pos * data.RECORD_SIZE))
            file.write(data.pack())

    def put_header(self, root:int):
        """
        Actualiza la cabecera de la base de datos
        """
        self.root = root # en memoria ram
        with open(self.name, 'rb+') as file:
            file.write(struct.pack('i', root)) # en memoria secundaria

    def seek(self, id_venta:int, pos:int):
        """
        Busca una tupla en la base de datos
        """
        if pos == -1:
            return pos
        punt = self.get(pos) # obtenemos la tupla y realizamos busqueda binaria
        if punt is None:
            return -1
        if id_venta == punt.id_venta:
            return pos
        if id_venta > punt.id_venta:
            return self.seek(id_venta, punt.der)
        if id_venta < punt.id_venta:
            return self.seek(id_venta, punt.izq)

    def load(self):
        """
        carga toda la informacion en el archivo
        """
        r = []
        ite = 0
        now = self.get(ite)
        while now:
            r.append(now)
            ite+=1
            now = self.get(ite)
        return r

    def load_order(self)-> list:
        """
        Carga todas las tuplas de la base de datos en orden
        """
        ret = []
        self.load_aux(self.root, ret)
        return ret

    def load_aux(self, pos:int, ret:list):
        """
        in-order search
        """
        punt = self.get(pos)
        if punt is None:
            return
        self.load_aux(punt.izq, ret)
        ret.append(punt)
        self.load_aux(punt.der, ret)


    def update_height(self, nodo: Venta) -> int:
        if not nodo:
            return -1
        if nodo.izq == -1 and nodo.der == -1:
            return 0
        else:
            d_h = 0 if nodo.der == -1 else self.get(nodo.der).height # si tiene nodo derecho, tomamos su altura
            i_h = 0 if nodo.izq == -1 else self.get(nodo.izq).height # si tiene nodo izquierdo, tomamos su altura
            return max(d_h,i_h) + 1

    def get_balance(self, nodo: Venta) -> int:
        if not nodo:
            return 0
        d = 0 if nodo.der == -1 else 1 + self.get(nodo.der).height # si tiene nodo derecho, tomamos su altura + 1
        i = 0 if nodo.izq == -1 else 1 + self.get(nodo.izq).height # si tiene nodo izquierdo, tomamos su altura + 1

        return i - d

    def right_rotate(self,y:Venta, pos_y:int, x:Venta, pos_x:int):
        """
        Rotacion a la derecha
        input: y: Venta, pos_y: int, x: Venta, pos_x: int
            donde x = y->izq
        """
        t2 = x.der
        x.der = pos_y
        y.izq = t2
        y.height = self.update_height(y)
        self.patch(pos_y,y) # actualizamos la tupla en el archivo
        x.height = self.update_height(x)
        self.patch(pos_x,x) # actualizamos la tupla en el archivo
        return pos_x


    def left_rotate(self,x:Venta, pos_x:int, y:Venta, pos_y:int):
        """
        Rotacion a la izquierda
        input: x: Venta, pos_x: int, y: Venta, pos_y: int
            donde y = x->der
        """
        t2 = y.izq
        y.izq = pos_x
        x.der = t2
        x.height = self.update_height(x)
        self.patch(pos_y,y) # actualizamos la tupla en el archivo
        y.height = self.update_height(y)
        self.patch(pos_x,x) # actualizamos la tupla en el archivo
        return pos_y

    def balancear(self, punt:Venta, pos:int):
        # una vez insertado, actualizamos la altura y balance del nodo
        punt.height = self.update_height(punt)
        balance = self.get_balance(punt)

        if balance > 1:
            izq = self.get(punt.izq)
            # Caso 1
            if self.get_balance(izq) >= 0:
                if pos == self.root:  # Si es la raíz, actualizamos la raíz
                    self.put_header(punt.izq)
                return self.right_rotate(punt, pos, izq, punt.izq)

            # Caso 2
            else:
                punt.izq = self.left_rotate(izq, punt.izq, self.get(izq.der),
                                            izq.der)
                return self.right_rotate(punt, pos, izq, punt.izq)

        elif balance < -1:
            der = self.get(punt.der)
            # Caso 1
            if self.get_balance(der) <= 0:
                if pos == self.root:  # Si es la raíz, actualizamos la raíz
                    self.put_header(punt.der)
                return self.left_rotate(punt, pos, der, punt.der)

            # Caso 2
            else:
                punt.der = self.right_rotate(der, punt.der, self.get(der.izq),
                                             der.izq)
                return self.left_rotate(punt, pos, der, punt.der)

        # else
        self.patch(pos, punt)
        return pos


    def addaux(self, venta: Venta, pos: int):
        """
        Añade una tupla a la base de datos
        """
        if pos == -1:
            return self.post(venta)
        punt = self.get(pos)
        if punt is None:
            return self.post(venta)

        # si existe, buscamos recursivamente una hoja donde insertarlo
        if venta.id_venta > punt.id_venta:
            punt.der = self.addaux(venta, punt.der)
        elif venta.id_venta < punt.id_venta:
            punt.izq = self.addaux(venta, punt.izq)

        return self.balancear(punt, pos)


    def add(self, record:Venta):
        """
        Añade una tupla a la base de datos
        """
        if self.seek(record.id_venta, self.root) != -1:
            print("id repetido")
            return
        self.addaux(record, self.root)



    def read_record(self, id_venta:int):
        """
        Busca una tupla en la base de datos
        """
        return self.get(self.seek(id_venta, 0))

    def seek_aux(self, id_venta:int, pos:int, ant:int)->():
        """
        Busca una tupla en la base de datos y retorna la posicion, y su anterior
        """
        if pos == -1:
            return ant,-1
        punt = self.get(pos)
        if punt is None:
            return ant,-1
        if id_venta == punt.id_venta:
            return ant,pos
        if id_venta > punt.id_venta:
            return self.seek_aux(id_venta, punt.der, pos)
        if id_venta < punt.id_venta:
            return self.seek_aux(id_venta, punt.izq, pos)

    def delete_record(self, id_venta:int):
        ant, pos = self.seek_aux(id_venta, self.root,-1)
        if pos == -1:
            print("no existe el elemento")
            return
        punt = self.get(pos)
        punt_ant = self.get(ant)
        # caso 1
        if punt.der == -1 and punt.izq == -1:
            if not punt_ant: # si es la raiz
                self.root = -1
                self.patch(pos, Venta())

            if punt_ant.der == pos:
                punt_ant.der = -1
            else:
                punt_ant.izq = -1

            self.patch(pos, Venta())
            self.patch(ant, punt_ant)

        # caso 2
        elif punt.der == -1:
            if not punt_ant: # si es la raiz
                self.root = punt.izq
                self.patch(pos, Venta())

            if punt_ant.der == pos:
                punt_ant.der = punt.izq
            else:
                punt_ant.izq = punt.izq

            self.patch(pos, Venta())
            self.patch(ant, punt_ant)

        elif punt.izq == -1:
            if not punt_ant: # si es la raiz
                self.root = punt.der
                self.patch(pos, Venta())

            if punt_ant.der == pos:
                punt_ant.der = punt.der
            else:
                punt_ant.izq = punt.der

            self.patch(pos, Venta())
            self.patch(ant, punt_ant)

        # caso 3
        else:
            # buscamos el sucesor
            pos_scsr = punt.der
            scsr = self.get(pos_scsr)
            pos_ant_scsr = pos
            while scsr.izq != -1:
                pos_ant_scsr = pos_scsr
                pos_scsr = scsr.izq
                scsr = self.get(pos_scsr)

            if pos_ant_scsr != pos: # si no es el sucesor directo
                ant_scsr = self.get(pos_ant_scsr)
                ant_scsr.izq = scsr.der
                self.patch(pos_ant_scsr, ant_scsr)
            else:
                punt.der = scsr.der

            punt.id_venta = scsr.id_venta
            punt.nombre = scsr.nombre
            punt.cant = scsr.cant
            punt.precio_u = scsr.precio_u
            punt.fecha = scsr.fecha
            self.patch(pos_scsr, Venta())
            self.patch(pos, punt)

        return self.balancear(punt_ant, ant) if punt_ant else self.balancear(self.get(self.root), self.root)

    def range_search(self, inf:int, sup:int):
        r = []
        self.range_search_aux(self.root, inf, sup, r)
        return r

    def range_search_aux(self,pos:int, inf:int, sup:int, ret:list):
        punt = self.get(pos)
        if punt is None:
            return
        if inf <= punt.id_venta <= sup:
            ret.append(punt)

        if inf < punt.id_venta:
            self.range_search_aux(punt.izq, inf, sup, ret)

        if sup > punt.id_venta:
            self.range_search_aux(punt.der, inf, sup, ret)



ventas = [Venta(0, "Berenjena", 10, 2.5, "2025-15-10"), Venta(1, "Yucas", 30, 3.2, "2025-12-27"),
          Venta(2, "Camotes", 20, 2.2, "2025-12-26"), Venta(3, "Choclo", 40, 4.2, "2025-12-28"),
          Venta(4, "Papas", 10, 1.2, "2025-12-25"), Venta(5, "Arroz", 50, 5.2, "2025-12-29"),
          Venta(6, "Maíz", 60, 3.8, "2025-12-30"), Venta(7, "Frijoles", 70, 6.5, "2025-12-31"),
          Venta(8, "Lentejas", 80, 2.5, "2026-01-01"), Venta(9, "Tomates", 90, 1.9, "2026-01-02"),
          Venta(10, "Cebollas", 100, 4.0, "2026-01-03")]

import statistics

# Listas para almacenar los tiempos
tiempos_insercion = []
tiempos_busqueda_901 = []
tiempos_busqueda_302 = []
tiempos_busqueda_106 = []
tiempos_rango_2_300 = []
tiempos_rango_253_793 = []
tiempos_rango_83_924 = []
tiempos_eliminacion_108 = []
tiempos_eliminacion_302 = []
tiempos_eliminacion_511 = []

for _ in range(10):
    b_ins = time.time()
    bd = AVL_db('sales_dataset_random.csv')
    e_ins = time.time()
    tiempos_insercion.append(e_ins - b_ins)

    b_bus1 = time.time()
    venta901 = bd.read_record(901)
    e1_bus1 = time.time()
    tiempos_busqueda_901.append(e1_bus1 - b_bus1)

    b_bus2 = time.time()
    venta302 = bd.read_record(302)
    e_bus2 = time.time()
    tiempos_busqueda_302.append(e_bus2 - b_bus2)

    b_bus3 = time.time()
    venta106 = bd.read_record(106)
    e_bus3 = time.time()
    tiempos_busqueda_106.append(e_bus3 - b_bus3)

    b_rng1 = time.time()
    ventas = bd.range_search(2, 300)
    e_rng1 = time.time()
    tiempos_rango_2_300.append(e_rng1 - b_rng1)

    b_rng2 = time.time()
    ventas = bd.range_search(253, 793)
    e_rng2 = time.time()
    tiempos_rango_253_793.append(e_rng2 - b_rng2)

    b_rng3 = time.time()
    ventas = bd.range_search(83, 924)
    e_rng3 = time.time()
    tiempos_rango_83_924.append(e_rng3 - b_rng3)

    b_del1 = time.time()
    bd.delete_record(108)
    e_del1 = time.time()
    tiempos_eliminacion_108.append(e_del1 - b_del1)

    b_del2 = time.time()
    bd.delete_record(302)
    e_del2 = time.time()
    tiempos_eliminacion_302.append(e_del2 - b_del2)

    b_del3 = time.time()
    bd.delete_record(511)
    e_del3 = time.time()
    tiempos_eliminacion_511.append(e_del3 - b_del3)

# Calcular promedios y desviaciones estándar
print("RESULTADOS PROMEDIO Y DESVIACIÓN ESTÁNDAR:")
print("Tiempo de inserción: Promedio =", statistics.mean(tiempos_insercion),
      "Desviación estándar =", statistics.stdev(tiempos_insercion))
print(tiempos_insercion)
print("Tiempo de búsqueda 901: Promedio =", statistics.mean(tiempos_busqueda_901),
      "Desviación estándar =", statistics.stdev(tiempos_busqueda_901))
print(tiempos_busqueda_901)
print("Tiempo de búsqueda 302: Promedio =", statistics.mean(tiempos_busqueda_302),
      "Desviación estándar =", statistics.stdev(tiempos_busqueda_302))
print(tiempos_busqueda_302)
print("Tiempo de búsqueda 106: Promedio =", statistics.mean(tiempos_busqueda_106),
      "Desviación estándar =", statistics.stdev(tiempos_busqueda_106))
print(tiempos_busqueda_106)
print("Tiempo de búsqueda rango 2-300: Promedio =", statistics.mean(tiempos_rango_2_300),
      "Desviación estándar =", statistics.stdev(tiempos_rango_2_300))
print(tiempos_rango_2_300)
print("Tiempo de búsqueda rango 253-793: Promedio =", statistics.mean(tiempos_rango_253_793),
      "Desviación estándar =", statistics.stdev(tiempos_rango_253_793))
print(tiempos_rango_253_793)
print("Tiempo de búsqueda rango 83-924: Promedio =", statistics.mean(tiempos_rango_83_924),
      "Desviación estándar =", statistics.stdev(tiempos_rango_83_924))
print(tiempos_rango_83_924)
print("Tiempo de eliminación 108: Promedio =", statistics.mean(tiempos_eliminacion_108),
      "Desviación estándar =", statistics.stdev(tiempos_eliminacion_108))
print(tiempos_eliminacion_108)
print("Tiempo de eliminación 302: Promedio =", statistics.mean(tiempos_eliminacion_302),
      "Desviación estándar =", statistics.stdev(tiempos_eliminacion_302))
print(tiempos_eliminacion_302)
print("Tiempo de eliminación 511: Promedio =", statistics.mean(tiempos_eliminacion_511),
      "Desviación estándar =", statistics.stdev(tiempos_eliminacion_511))
print(tiempos_eliminacion_511)


etiquetas = [
    "Inserción",
    "Búsqueda 901", "Búsqueda 302", "Búsqueda 106",
    "Búsq. Rango 2-300", "Búsq. Rango 253-793", "Búsq. Rango 83-924",
    "Elim. 108", "Elim. 302", "Elim. 511"
]

promedios = [
    statistics.mean(tiempos_insercion),
    statistics.mean(tiempos_busqueda_901), statistics.mean(tiempos_busqueda_302), statistics.mean(tiempos_busqueda_106),
    statistics.mean(tiempos_rango_2_300), statistics.mean(tiempos_rango_253_793), statistics.mean(tiempos_rango_83_924),
    statistics.mean(tiempos_eliminacion_108), statistics.mean(tiempos_eliminacion_302), statistics.mean(tiempos_eliminacion_511)
]

desviaciones = [
    statistics.stdev(tiempos_insercion),
    statistics.stdev(tiempos_busqueda_901), statistics.stdev(tiempos_busqueda_302), statistics.stdev(tiempos_busqueda_106),
    statistics.stdev(tiempos_rango_2_300), statistics.stdev(tiempos_rango_253_793), statistics.stdev(tiempos_rango_83_924),
    statistics.stdev(tiempos_eliminacion_108), statistics.stdev(tiempos_eliminacion_302), statistics.stdev(tiempos_eliminacion_511)
]

resultados = [
    tiempos_insercion,
    tiempos_busqueda_901, tiempos_busqueda_302, tiempos_busqueda_106,
    tiempos_rango_2_300, tiempos_rango_253_793, tiempos_rango_83_924,
    tiempos_eliminacion_108, tiempos_eliminacion_302, tiempos_eliminacion_511
]

# Crear gráficos
fig, axs = plt.subplots(5, 2, figsize=(14, 20))
axs = axs.flatten()

for i, ax in enumerate(axs):
    ax.errorbar(range(1, 11), resultados[i], yerr=desviaciones[i], fmt='o', color='blue', label='Tiempo')
    ax.axhline(promedios[i], color='red', linestyle='--', label='Promedio')
    ax.set_title(etiquetas[i])
    ax.set_xlabel('Iteración')
    ax.set_ylabel('Tiempo (s)')
    ax.legend()

plt.tight_layout()
plt.show()
