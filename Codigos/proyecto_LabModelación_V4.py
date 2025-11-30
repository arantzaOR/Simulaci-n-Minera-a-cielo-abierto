import salabim as sim
import math
sim.reset()

####### Zona estética ########
env = sim.Environment()
env.background_color("90%gray")
env.width(900); env.height(700)
env.position((1000,0))
env.width3d(900); env.height3d(700)
env.position3d((0,100))

env.animate(True)
env.animate3d(True)

# ====== ESTRUCTURAS FIJAS ====== #
# Botadero
sim.Animate3dRectangle(x0=-6, y0=7, x1=-4, y1=9, z=10, color="brown")
# sim.Animate3dBox(x_len=1, y_len=1, z_len=1, color='brown', x=-5, y=9, z=10)

# Planta
sim.Animate3dRectangle(x0=-1, y0=7, x1=1, y1=9, z=10, color="green")
# Stock
sim.Animate3dRectangle(x0=3, y0=7, x1=5, y1=9, z=10, color="blue")
# Pala (cubo estático)
sim.Animate3dBox(x_len=1, y_len=1, z_len=1, color='gray', x=0, y=1, z=0)

# Grilla que representa el suelo (z=0)
sim.Animate3dGrid(x_range=range(-10,11), y_range=range(-10,11), z_range=[10], color="lightgray")

# ====== Dibujar la ruta planificada (puntos pequeños rojos) ======
# T_total = 100
# n_points = 500
# for i in range(n_points):
#     t_sample = i * (T_total) / (n_points - 1)
#     sim.Animate3dBox(
#         x_len=0.06, y_len=0.06, z_len=0.06, color="red",
#         x=spiral_pos(t_sample)[0] if t_sample <= T_espiral else (bot_x if t_sample > T_espiral else 0),
#         y=spiral_pos(t_sample)[1] if t_sample <= T_espiral else (y_end_spiral + ( (t_sample - T_espiral)/ (T_left+T_up) )*(bot_y - y_end_spiral) if t_sample > T_espiral else 0),
#         z=z_truck(t_sample)
#     )


'''
-colas en destino (check pero ta feo)
-multiples descarga y carga
-camino (check)
-chancador (transportabilidad) y sreportabilidad de los estados CSV (estadísticas)
- cambio de turnos y colaciones
'''

######## Zona de movimiento ########
# ====== PARÁMETROS Y RECURSOS ====== #
omega = 2 * math.pi / 5
R_max = 5
z_min, z_max = 0.0, 10.0
T_carga = 3.50
T_espiral = 10.0
T_espera_destino = 5.0
T_regreso = 8.0

# RECURSO PALA (solo lógico, no visual)
# pala = sim.Resource("Pala")

# ====== CONFIGURACIÓN VARIABLE ====== #
num_camiones = 5
# destinos_camiones = ["botadero", "planta", "stock"]
destinos_camiones = ['botadero']
# destinos_camiones = ['botadero', 'botadero', 'botadero', 'botadero', 'botadero', 'botadero', 'botadero', 'planta', 'planta', 'planta', 'stock', 'planta', 'planta',
                    #  'stock', 'botadero']
velocidad_camion = 1.0
destino_coords = {
    "botadero": (-5.0, 8.0),
    "planta": (0.0, 8.0),
    "stock": (4.0, 8.0)
}

cola_pala = sim.Queue("cola_pala")
espacio_camiones = 1.0
cola_destino = sim.Queue('cola_destino')

# ====== CLASE CAMIÓN ====== #
class Camion(sim.Component):
    def setup(self, id_camion, destinos, tiempo_inicio=0):
        self.id = id_camion
        self.destinos = destinos
        self.destino_index = 0
        self.estado = "inicial"
        self.start_time = env.now()
        self.current_destino = self.destinos[self.destino_index]
        self.tiempo_inicio = tiempo_inicio
        
        # Calcular posición final de espiral
        self.x_end_spiral, self.y_end_spiral = self.spiral_pos(T_espiral)
        self.calcular_tiempos_destino(self.current_destino)
        
        self.animacion = sim.Animate3dBox(
            x_len=0.6, y_len=0.6, z_len=0.6, 
            # color=["pink", "yellow", "cyan", "orange", "purple"][id_camion % 5],
            color = self.color_camion,
            x=self.x_truck, y=self.y_truck, z=self.z_truck
        )

    def color_camion(self, t):
        # Cuando está descargado es blanco, cuando está cargado es morado
        if self.estado in ['esperando_cola', 'en_cola', 'cargando', 'regresando']:
            return 'lavenderblush'
        else:
            return 'mediumorchid'
        
    def calcular_tiempos_destino(self, destino):
        dest_x, dest_y = destino_coords[destino]
        dist_x = abs(dest_x - self.x_end_spiral)
        dist_y = abs(dest_y - self.y_end_spiral)
        
        self.T_left = dist_x / velocidad_camion if dist_x > 0 else 0.1
        self.T_up = dist_y / velocidad_camion if dist_y > 0 else 0.1
        self.T_total_ida = T_espiral + self.T_left + self.T_up

    def calcular_posicion_cola_pala(self):
        if self.posicion_en_cola is None:
            return 0,0,z_min
        distancia = (self.posicion_en_cola +1)* espacio_camiones
        return -distancia, 0, z_min
    
    def actualizar_posiciones_cola_pala(self):
        for i, camion in enumerate(cola_pala):
            camion.posicion_en_cola = i

    def calcular_posicion_cola_destino(self, destino):
        dest_x, dest_y = destino_coords[destino]
        if self.posicion_en_cola is None:
            return dest_x,dest_y, z_max
        distancia = (self.posicion_en_cola+1)* espacio_camiones
        return dest_x-distancia, dest_y, z_max
    
    def actualizar_posiciones_cola_destino(self):
        for i, camion in enumerate(cola_destino):
            camion.posicion_en_cola = i


# ====== Funciones de posición ====== #
    # Posición x del camión en función del tiempo
    def x_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
        
        if self.estado in ['esperando_cola', 'en_cola']:
            x, y, z = self.calcular_posicion_cola_pala()
            return x
        elif self.estado == "cargando":
            return 0
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                r = self.r_func(t_rel)
                theta = omega * t_rel
                return r * math.cos(theta)
            elif t_rel <= T_espiral + self.T_left:
                alpha = (t_rel - T_espiral) / self.T_left
                return self.x_end_spiral + alpha * (dest_x - self.x_end_spiral)
            else:
                return dest_x
        elif self.estado in ['cola_destino', 'en_cola_destino']:
            x,y,z = self.calcular_posicion_cola_destino(self.current_destino)
            return x
        elif self.estado == "descargando":
            return dest_x
        elif self.estado == "regresando":
            if t_rel <= self.T_up:
                alpha = t_rel / self.T_up
                return dest_x
            elif t_rel <= self.T_up + self.T_left:
                alpha = (t_rel - self.T_up) / self.T_left
                return dest_x + alpha * (self.x_end_spiral - dest_x)
            else:
                alpha = (t_rel - (self.T_up + self.T_left)) / T_espiral
                t_espiral_inv = T_espiral * (1 - alpha)
                r = self.r_func(t_espiral_inv)
                theta = omega * t_espiral_inv
                return r * math.cos(theta)
        return 0

    # Posición y del camión en función del tiempo
    def y_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
        
        if self.estado in ['esperando_cola', 'en_cola']:
            x, y, z = self.calcular_posicion_cola_pala()
            return y
        elif self.estado == "cargando":
            return 0
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                r = self.r_func(t_rel)
                theta = omega * t_rel
                return r * math.sin(theta)
            elif t_rel <= T_espiral + self.T_left:
                return self.y_end_spiral
            elif t_rel <= T_espiral + self.T_left + self.T_up:
                alpha = (t_rel - (T_espiral + self.T_left)) / self.T_up
                return self.y_end_spiral + alpha * (dest_y - self.y_end_spiral)
            else:
                return dest_y
        elif self.estado in ['cola_destino','en_cola_destino']:
            # x,y,z = self.cocular_posicion_cola_destino()
            return dest_y
        elif self.estado == "descargando":
            return dest_y
        elif self.estado == "regresando":
            if t_rel <= self.T_up:
                alpha = t_rel / self.T_up
                return dest_y + alpha * (self.y_end_spiral - dest_y)
            elif t_rel <= self.T_up + self.T_left:
                return self.y_end_spiral
            else:  # Espiral de regreso
                alpha = (t_rel - (self.T_up + self.T_left)) / T_espiral
                t_espiral_inv = T_espiral * (1 - alpha)
                r = self.r_func(t_espiral_inv)
                theta = omega * t_espiral_inv
                return r * math.sin(theta)
        return 0

    # Posición z del camión en función del tiempo
    def z_truck(self, t):
        t_rel = t - self.start_time
        
        if self.estado in ['esperando_cola', 'en_cola']:
            x, y, z = self.calcular_posicion_cola_pala()
            return z
        elif self.estado == "cargando":
            return z_min
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                return z_min + (z_max - z_min) * (t_rel / T_espiral)
            else:
                return z_max
        elif self.estado in ['cola_destino', 'en_cola_destino']:
            return z_max
        elif self.estado == "descargando":
            return z_max
        elif self.estado == "regresando":
            if t_rel <= self.T_up + self.T_left:
                return z_max
            else:
                return z_max + ((t_rel - (self.T_up + self.T_left)) / T_espiral) * (z_min - z_max)
        return z_min

    def z_func(self, t):
        if t <= T_espiral:
            return z_min + (z_max - z_min) * (t / T_espiral)
        else:
            return z_max

    def r_func(self, t):
        return 0.0 if z_max == 0 else (self.z_func(t) / z_max) * R_max

    def spiral_pos(self, t):
        r = self.r_func(t)
        theta = omega * t
        return r * math.cos(theta), r * math.sin(theta)

    def process(self):
        self.hold(self.tiempo_inicio)
        
        while True:
            # Cola pala
            self.estado = "esperando_cola"
            self.enter(cola_pala)
            self.actualizar_posiciones_cola_pala()

            while self!= cola_pala[0]:
                self.estado = "en_cola"
                self.passivate()

            # Pala
            self.estado = "cargando"
            self.start_time = env.now()
            self.hold(T_carga)
            
            # salir de la cola y actualizar posiciones de los demás
            self.leave(cola_pala)
            self.actualizar_posiciones_cola_pala()
            if cola_pala:
                cola_pala[0].activate()
                            
            # Ir al destino
            self.estado = "yendo"
            self.start_time = env.now()
            self.calcular_tiempos_destino(self.current_destino)
            self.hold(self.T_total_ida)
            
            # Cola destino
            self.estado = 'cola_destino'
            self.enter(cola_destino)
            self.actualizar_posiciones_cola_destino()

            while self!= cola_destino[0]:
                self.estado = 'en_cola_destino'
                self.passivate()
            self.leave(cola_destino)
            self.actualizar_posiciones_cola_destino()
            if cola_destino:
                cola_destino[0].activate()

            # Esperar en destino
            self.estado = "descargando"
            self.start_time = env.now()
            self.hold(T_espera_destino)

            # Regresar al origen
            self.estado = "regresando"
            self.start_time = env.now()
            tiempo_regreso = self.T_up + self.T_left + T_espiral
            self.hold(tiempo_regreso)
        
            # Actualizar destino
            self.destino_index = (self.destino_index + 1) % len(self.destinos)
            self.current_destino = self.destinos[self.destino_index]

# ====== CREACIÓN DE CAMIONES ====== #
for i in range(num_camiones):
    destinos = [destinos_camiones[(i + j) % len(destinos_camiones)] for j in range(3)]
    tiempo_inicio = 0 #i * 5
    camion = Camion(id_camion=i, destinos=destinos, tiempo_inicio=tiempo_inicio)

# ====== CÁMARA ====== #
env.view(
    x_eye=0, y_eye=-15, z_eye=20,
    x_center=-3, y_center=4, z_center=4,
    field_of_view_y=60
)

# ====== RUN ====== #
env.run()