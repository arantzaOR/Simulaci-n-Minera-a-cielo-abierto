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
# Planta
sim.Animate3dRectangle(x0=-1, y0=7, x1=1, y1=9, z=10, color="green")
# Stock
sim.Animate3dRectangle(x0=3, y0=7, x1=5, y1=9, z=10, color="blue")
# Pala
sim.Animate3dBox(x_len=1, y_len=1, z_len=1, color = 'gray', x=0,y=0,z=0)

# Grilla que representa el suelo (z=0)
sim.Animate3dGrid(x_range=range(-10,11), y_range=range(-10,11), z_range=[10], color="lightgray")

######## Zona de movimiento ########
# ====== PARÁMETROS DE MOVIMIENTO ====== #
omega = 2 * math.pi / 5
R_max = 5
z_min, z_max = 0.0, 10.0

T_carga = 2.0
T_espiral = 10.0
T_left   = 3.0
T_up     = 4.0
T_espera_destino = 1.0  # 1 segundo en el destino
T_regreso = 8.0  # tiempo para regresar a la pala

T_total_ida = T_espiral + T_left + T_up
T_total_vuelta = T_regreso
T_total_ciclo = T_total_ida + T_espera_destino + T_total_vuelta

# ====== CONFIGURACIÓN VARIABLE ====== #
# Definir cantidad de camiones y sus destinos
num_camiones = 5  # Cambia este valor según necesites
destinos_camiones = ["botadero", "planta", "stock"]  # Un destino por camión

# coordenadas destino
destino_coords = {
    "botadero": (-5.0, 8.0),
    "planta": (0.0, 8.0),
    "stock": (4.0, 8.0)
}

# Cola en pala
cola_pala = sim.Queue("cola_pala")
espacio_camiones = 1.0

velocidad_camion = 1.0  # unidades por segundo

# ====== CLASE CAMIÓN ====== #
class Camion(sim.Component):
    def setup(self, id_camion, destinos, tiempo_inicio=0):
        self.id = id_camion
        self.destinos = destinos  # Lista de destinos a recorrer
        self.destino_index = 0
        self.estado = "cargando"  # "cargando", "yendo", "esperando", "regresando"
        self.start_time = env.now()
        self.current_destino = self.destinos[self.destino_index]
        self.tiempo_inicio = tiempo_inicio
        self.posicion_en_cola = None    #0 = pala, 1 = siguiente
        self.calcular_tiempos_destino(self.current_destino)
        
        # Crear animación del camión
        self.animacion = sim.Animate3dBox(
            x_len=0.6, y_len=0.6, z_len=0.6, 
            color=["pink", "yellow", "cyan", "orange", "purple"][id_camion % 5],
            x=self.x_truck, y=self.y_truck, z=self.z_truck
        )
        
    def calcular_tiempos_destino(self, destino):
        dest_x, dest_y = destino_coords[destino]
        x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
        dist_x = abs(dest_x - x_end_spiral)
        dist_y = abs(dest_y - y_end_spiral)        
        self.T_left = dist_x / velocidad_camion if dist_x > 0 else 0.001  # Evitar cero
        self.T_up = dist_y / velocidad_camion if dist_y > 0 else 0.001    # Evitar cero
        self.T_total_ida = T_espiral + self.T_left + self.T_up

# RESERVA PORQUE ESTÁ FUNCIONANDO MAL
    # def calcular_tiempos_destino(self, destino):
    #     dest_x, dest_y = destino_coords[destino]
    #     x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
    #     dist_x = abs(dest_x - x_end_spiral)
    #     dist_y = abs(dest_y - y_end_spiral)
    #     self.T_left = dist_x / velocidad_camion if dist_x>0 else 0
    #     self.T_up = dist_y / velocidad_camion if dist_y>0 else 0
    #     self.T_total_ida = T_espiral + self.T_left + self.T_up
                 
    def calcular_posicion_cola(self):
        if self.posicion_en_cola is None:
            return 0,0,z_min
        distancia = (self.posicion_en_cola +1)* espacio_camiones
        return -distancia, 0, z_min
    
    def actualizar_posiciones_cola(self):
        for i, camion in enumerate(cola_pala):
            camion.posicion_en_cola = i


    def x_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
        
        if self.estado == "cargando":
            return 0  # En la pala
            
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                r = self.r_func(t_rel)
                theta = omega * t_rel
                return r * math.cos(theta)
            elif t_rel <= T_espiral + self.T_left:
                if self.T_left > 0:
                    alpha = (t_rel - T_espiral) / self.T_left
                    x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
                    return x_end_spiral + alpha * (dest_x - x_end_spiral)
                else:
                    x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
                    return x_end_spiral
            # elif t_rel <= T_espiral + self.T_left + self.T_up:
            #     return dest_x
            else:
                return dest_x
                
        elif self.estado == "esperando":
            return dest_x
            
        elif self.estado == "regresando":
            alpha = t_rel / T_regreso
            return dest_x + alpha * (0 - dest_x)  # Regresar a x=0 (pala)
    def process(self):
        self.hold(self.tiempo_inicio)
        
        while True:
            # Entrar a la cola de la pala
            self.estado = "esperando_cola"
            self.enter(cola_pala)
            self.actualizar_posiciones_cola()
            
            # Esperar turno en la cola
            while self != cola_pala[0]:
                self.estado = "en_cola"
                self.passivate()
            self.estado = "cargando"
            self.start_time = env.now()
            self.hold(T_carga)
            
            # Salir de la cola y actualizar posiciones de los demás
            self.leave(cola_pala)
            self.actualizar_posiciones_cola()
            if cola_pala:  # Activar al siguiente en cola
                cola_pala[0].activate()
    def y_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
        
        if self.estado == "cargando":
            return 0  # En la pala
            
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                #Fase espiral
                r = self.r_func(t_rel)
                theta = omega * t_rel
                return r * math.sin(theta)
            elif t_rel <= T_espiral + self.T_left:
                #Mantener y fijo, mover solo en x
                x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
                return y_end_spiral
            elif t_rel <= T_espiral + self.T_left + self.T_up:
                #Mover en y hacia el destino, x fijo
                if self.T_up > 0:
                    alpha = (t_rel - (T_espiral + self.T_left)) / self.T_up
                    x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
                    y_pos = y_end_spiral + alpha * (dest_y - y_end_spiral)
                    return y_pos
                    # return y_end_spiral + alpha * (dest_y - y_end_spiral)
                else:
                    x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
                    return y_end_spiral
            else:
                return dest_y
                
        elif self.estado == "esperando":
            return dest_y
            
        elif self.estado == "regresando":
            alpha = t_rel / T_regreso
            return dest_y + alpha * (0 - dest_y)  # Regresar a y=0 (pala)

    def z_truck(self, t):
        t_rel = t - self.start_time
        
        if self.estado == "cargando":
            return z_min
            
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                return z_min + (z_max - z_min) * (t_rel / T_espiral)
            else:
                return z_max
                
        elif self.estado == "esperando":
            return z_max
            
        elif self.estado == "regresando":
            alpha = t_rel / T_regreso
            # Descender gradualmente durante el regreso
            return z_max + alpha * (z_min - z_max)

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

# ====== CREACIÓN DE CAMIONES ====== #
for i in range(num_camiones):
    # Asignar destinos cíclicos a cada camión
    destinos = [destinos_camiones[(i + j) % len(destinos_camiones)] for j in range(3)]
    # Espaciar el inicio de los camiones (3 segundos entre cada uno)
    tiempo_inicio = i * 3
    camion = Camion(id_camion=i, destinos=destinos, tiempo_inicio=tiempo_inicio)

# ====== CÁMARA ====== #
env.view(
    x_eye=0, y_eye=-15, z_eye=20,
    x_center=-3, y_center=4, z_center=4,
    field_of_view_y=60
)

# ====== RUN ====== #
env.run(till=150)  # Tiempo suficiente para múltiples ciclos
