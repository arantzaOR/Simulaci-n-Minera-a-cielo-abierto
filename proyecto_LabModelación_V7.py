import salabim as sim
import math
import csv
import os

curr_path = os.path.dirname(os.path.abspath(__file__))

class LoggerCamiones:
    def __init__(self):
        self.archivo = os.path.join(curr_path, 'log_camiones.csv')
        self.encabezados = [
            "id_camion", "ciclo", 
            "tiempo_en_cola_punto_carga", "tiempo_cargando", 
            "tiempo_yendo", "tiempo_cola_destino", "tiempo_descargando",
            "tiempo_regresando", "tiempo_total_ciclo"
        ]
        self.inicializar_archivo()

    def inicializar_archivo(self):
        with open(self.archivo, 'w', newline='', encoding = 'utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.encabezados)
    
    def escribir_fila(self, datos):
        with open(self.archivo, 'a', newline='', encoding ='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(datos)
            f.flush()
            os.fsync(f.fileno())

logger = LoggerCamiones()

sim.reset()

####### Inicio de animación ########
env = sim.Environment()
env.background_color("90%gray")
env.width(900); env.height(700)
env.position((1000,0))
env.width3d(900); env.height3d(700)
env.position3d((0,100))

env.animate(True)
env.animate3d(True)

# ====== ESTRUCTURAS FIJAS ====== #
sim.Animate3dGrid(x_range=range(-10,11), y_range=range(-10,11), z_range=[10], color="lightgray")
sim.Animate3dBox(x_len=1, y_len=1, z_len=1, color='gray', x=0, y=2, z=0.0)

# ====== CONFIGURACIÓN PUNTOS DE CARGA ====== #
PUNTOS_CARGA = {
    "punto_1": {"x": -1.5, "y": 2, "z": 0},
    "punto_2": {"x": 0, "y": 1, "z": 0},
    "punto_3": {"x": 1.5, "y": 2, "z": 0}
}

# Configuración de destinos
dest_confg = {
    "botadero": {
        "x0": -8, "y0": 7, "x1": -5, "y1": 10,
        "color": "brown",
        "punto_llegada": "centro"
    },
    "planta": {
        "x0": -2, "y0": 7, "x1": 1, "y1": 10,
        "color": "green", 
        "punto_llegada": "centro"
    },
    "stock": {
        "x0": 4, "y0": 7, "x1": 7, "y1": 10,
        "color": "blue",
        "punto_llegada": "centro"
    }
}

destino_coords = {}

for nombre, config in dest_confg.items():
    x0, y0, x1, y1 = config["x0"], config["y0"], config["x1"], config["y1"]
    color = config["color"]
    
    sim.Animate3dRectangle(x0=x0, y0=y0, x1=x1, y1=y1, z=10, color=color)
    
    if config["punto_llegada"] == "centro":
        x_llegada = (x0 + x1) / 2
        y_llegada = (y0 + y1) / 2
    elif config["punto_llegada"] == "frente":
        x_llegada = (x0 + x1) / 2
        y_llegada = y0
    
    destino_coords[nombre] = (x_llegada, y_llegada)

for nombre in dest_confg.keys():
    x_llegada, y_llegada = destino_coords[nombre]
    color = dest_confg[nombre]["color"]
    sim.Animate3dBox(x_len=0.5, y_len=0.5, z_len=1, color=color, x=x_llegada, y=y_llegada, z=10)

# Puntos de chancador
chanc_x0 = dest_confg['planta']['x0']
chanc_x1 = dest_confg['planta']['x1']
chanc_y0 = dest_confg['planta']['y0']
chanc_y1 = dest_confg['planta']['y1']

PUNTOS_CHANCADOR = {
    "chancadora_1": {"x": chanc_x0, "y": (chanc_y0+chanc_y1)/2, "z": 10},
    "chancadora_2": {"x": (chanc_x0+chanc_x1)/2, "y": chanc_y1, "z": 10},
    "chancadora_3": {"x": chanc_x1, "y": (chanc_y0+chanc_y1)/2, "z": 10}
}

######## Zona de movimiento ########
# ====== PARÁMETROS Y RECURSOS ====== #
omega = 2 * math.pi / 5
R_max = 5
z_min, z_max = 0.0, 10.0
T_carga = 2.51
T_espiral = 10.0
# T_descarga = 1.25
T_descarga = 5 # para forzar la cola

# ====== CONFIGURACIÓN VARIABLE ====== #
num_camiones = 10
destinos_camiones = ['planta']
# destinos_camiones = ['botadero', 'planta', 'stock']
# se comenta a favor de ejemplos para presentación puesto que es muy lento
# velocidad_camion_cargado_horizontal = 0.37  # kpm/h
# velocidad_camion_cargado_horizontal = 0.47  # kpm/h
velocidad_camion_descargado_horizontal = 2.0  # SÓLO PARA DEMOSTRACIÓN RÁPIDA
velocidad_camion_cargado_horizontal = 1.0  # SÓLO PARA DEMOSTRACIÓN RÁPIDA

# ====== CAMINOS DE LOS CAMIONES ====== #
def dibujar_caminos():
    spiral_points = 100
    y_points = 20
    x_points = 40
    
    x_end_spiral = R_max * math.cos(omega * T_espiral)
    y_end_spiral = R_max * math.sin(omega * T_espiral)
    
    for i in range(spiral_points):
        t = i * (T_espiral) / (spiral_points - 1)
        z = z_min + (z_max - z_min) * (t / T_espiral)
        r = (z / z_max) * R_max
        theta = omega * t
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        sim.Animate3dSphere(radius=0.08, color="red", x=x, y=y, z=z)
    
    for i in range(x_points):
        alpha = i / (x_points - 1)
        x = x_end_spiral + alpha * (-5.0 - x_end_spiral-1)
        z = z_max
        sim.Animate3dSphere(radius=0.08, color="red", x=x, y=y_end_spiral, z=z)

    for i in range(y_points):
        alpha = i / (y_points - 1)
        for dest in ['botadero', 'planta', "stock"]:
            dest_x, dest_y = destino_coords[dest]
            x = dest_x
            y = y_end_spiral + alpha * (dest_y - y_end_spiral)
            z = z_max
            sim.Animate3dSphere(radius=0.08, color="red", x=x, y=y, z=z)

dibujar_caminos()

# ====== RECURSOS Y COLAS ====== #
cola_puntos_carga = sim.Queue("cola_puntos_carga")
recurso_pala = sim.Resource("Pala", capacity=1)
recurso_espera_pala = sim.Resource("Posiciones_pala", capacity=3)
recurso_descarga_chancador = sim.Resource("Chancador", capacity=1)
# recurso_espera_chancador = sim.Resource("Posiciones_chancador", capacity=3)

# Sistema de destinos
cola_destino = {
    "botadero": sim.Queue("cola_botadero"),
    "planta": sim.Queue("cola_planta"), 
    "stock": sim.Queue("cola_stock")
}
recursos_destino = {
    "botadero": sim.Resource("Botadero", capacity=1),
    "stock": sim.Resource("Stock", capacity=1),
    "planta": sim.Resource("Posiciones_chancador", capacity=3)
}
espacio_camiones = 1.0

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
        self.posicion_en_cola = None
        self.punto_carga_asignado = None
        self.cola_actual = None
        self.punto_chancador_asignado = None

        self.ciclo_actual = 0
        self.tiempo_inicio_ciclo = env.now()
        self.tiempos_ciclo = {
            'en_cola_punto_carga': 0,
            'esperando_en_pala': 0,
            'cargando': 0,
            'yendo': 0,
            'cola_destino': 0,
            'en_cola_destino': 0,
            'en_chancador': 0,
            'descargando': 0,
            'regresando': 0
        }
        self.estado_anterior = None
        self.tiempo_entrada_estado = env.now()

        self.x_end_spiral, self.y_end_spiral = self.spiral_pos(T_espiral)
        self.calcular_tiempos_destino(self.current_destino)
        self.calcular_tiempos_regreso(self.current_destino)
        
        self.animacion = sim.Animate3dBox(
            x_len=0.6, y_len=0.6, z_len=0.6, 
            color=self.color_camion,
            x=self.x_truck, y=self.y_truck, z=self.z_truck
        )

    def cambiar_estado(self, nuevo_estado):
        if self.estado in self.tiempos_ciclo:
            tiempo_en_estado = env.now() - self.tiempo_entrada_estado
            self.tiempos_ciclo[self.estado] += tiempo_en_estado
        
        self.estado_anterior = self.estado
        self.estado = nuevo_estado
        self.tiempo_entrada_estado = env.now()

    def finalizar_ciclo(self, tiempo_regreso):
        if self.estado in self.tiempos_ciclo:
            tiempo_en_estado = env.now() - self.tiempo_entrada_estado
            self.tiempos_ciclo[self.estado] += tiempo_en_estado
        
        tiempo_total_ciclo = env.now() - self.tiempo_inicio_ciclo
        
        datos = [
            self.id,
            self.ciclo_actual,
            self.tiempos_ciclo['en_cola_punto_carga']+self.tiempos_ciclo['esperando_en_pala'],
            self.tiempos_ciclo['cargando'],
            self.tiempos_ciclo['yendo'],
            self.tiempos_ciclo['cola_destino']+self.tiempos_ciclo['en_cola_destino']+self.tiempos_ciclo['en_chancador'],
            self.tiempos_ciclo['descargando'],
            tiempo_regreso,
            tiempo_total_ciclo
        ]
        
        # Escribir en CSV
        logger.escribir_fila(datos)
        
        self.ciclo_actual += 1
        self.tiempo_inicio_ciclo = env.now()
        for estado in self.tiempos_ciclo:
            self.tiempos_ciclo[estado] = 0

    def color_camion(self, t):
        if self.estado in ['yendo', 'cola_destino', 'en_cola_destino', 'en_chancador']:
            return 'mediumorchid'
        elif self.estado in ['descargando', 'cargando']:
            return 'hotpink'
        elif self.estado in ['en_cola_punto_carga', 'yendo_punto_carga', 'esperando_en_pala', "regresando"]:
            return 'lavenderblush'
        else:
            # esto es para ver posibles errores 
            return 'orange'

        
    def calcular_tiempos_destino(self, destino):
        dest_x, dest_y = destino_coords[destino]
        dist_x = abs(dest_x - self.x_end_spiral)
        dist_y = abs(dest_y - self.y_end_spiral)
        
        self.T_left = dist_x / velocidad_camion_cargado_horizontal if dist_x > 0 else 0.1
        self.T_up = dist_y / velocidad_camion_cargado_horizontal if dist_y > 0 else 0.1
        self.T_total_ida = T_espiral + self.T_left + self.T_up

    def calcular_tiempos_regreso(self, destino):
        dest_x, dest_y = destino_coords[destino]
        x_end_spiral, y_end_spiral = self.spiral_pos(T_espiral)
    
        dist_x = abs(dest_x - x_end_spiral)
        dist_y = abs(dest_y - y_end_spiral)
    
        velocidad_descargado_horizontal = velocidad_camion_cargado_horizontal * (23.8 / 11.7)
    
        self.T_left_regreso = dist_x / velocidad_descargado_horizontal if dist_x > 0 else 0.1
        self.T_up_regreso = dist_y / velocidad_descargado_horizontal if dist_y > 0 else 0.1
    
        self.T_total_regreso = self.T_up_regreso + self.T_left_regreso + T_espiral

    def calcular_posicion_cola_puntos_carga(self):
        if self.posicion_en_cola is None:
            return 0, 0, z_min
        distancia = (self.posicion_en_cola + 1) * espacio_camiones
        return -distancia, -2, z_min 
    
    def actualizar_posiciones_cola_puntos_carga(self):
        for i, camion in enumerate(cola_puntos_carga):
            camion.posicion_en_cola = i

    def asignar_punto_carga(self):
        puntos_disponibles = list(PUNTOS_CARGA.keys())
        if not hasattr(env, 'contador_asignaciones'):
            env.contador_asignaciones = 0
        punto_asignado = puntos_disponibles[env.contador_asignaciones % len(puntos_disponibles)]
        env.contador_asignaciones += 1
        return punto_asignado
    
    def asignar_punto_chancador(self):
        puntos = list(PUNTOS_CHANCADOR.keys())
        if not hasattr(env, 'contador_chancador'):
            env.contador_chancador = 0
        punto_asignado = puntos[env.contador_chancador % len(puntos)]
        env.contador_chancador += 1
        return punto_asignado

    def get_cola_destino(self, destino):
        return cola_destino[destino]
    
    def get_recurso_destino(self, destino):
        return recursos_destino[destino]

    def calcular_posicion_cola_destino(self, destino):
        dest_x, dest_y = destino_coords[destino]
    
        # Si está en PLANTA con punto asignado -> está en posición de chancador (esperando o descargando)
        if (self.current_destino == 'planta' and 
            self.punto_chancador_asignado and
            self.estado in ['en_chancador', 'descargando']):
            punto = PUNTOS_CHANCADOR[self.punto_chancador_asignado]
            return punto['x'], punto['y'], z_max
    
        # Si está en COLA de planta (esperando posición)
        elif (self.current_destino == 'planta' and 
              self.estado in ['cola_destino', 'en_cola_destino']):
            if self.posicion_en_cola is None:
                return dest_x, dest_y+2, z_max
            else:
                distancia = (self.posicion_en_cola + 1) * espacio_camiones
                return dest_x + 3, dest_y + distancia, z_max
    
        # Para otros destinos
        if self.posicion_en_cola is None:
            return dest_x, dest_y, z_max
        
        distancia = (self.posicion_en_cola + 1) * espacio_camiones
        return dest_x, dest_y + distancia, z_max

    def actualizar_posiciones_cola_destino(self, destino):
        cola = self.get_cola_destino(destino)
        for i, camion in enumerate(cola):
            camion.posicion_en_cola = i
            camion.cola_actual = cola

    def x_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
    
        if self.estado == 'en_cola_punto_carga':
            x, y, z = self.calcular_posicion_cola_puntos_carga()
            return x
        elif self.estado in ['esperando_en_pala', 'cargando']:
            punto = PUNTOS_CARGA[self.punto_carga_asignado]
            return punto["x"]
        elif self.estado == "yendo_punto_carga" and self.punto_carga_asignado:
            punto = PUNTOS_CARGA[self.punto_carga_asignado]
            return punto["x"]
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
        elif self.estado in ['cola_destino', 'en_cola_destino', 'descargando', 'en_chancador']:
            x, y, z = self.calcular_posicion_cola_destino(self.current_destino)
            return x
        elif self.estado == "regresando":
            if t_rel <= self.T_up_regreso:
                alpha = t_rel / self.T_up_regreso
                return dest_x
            elif t_rel <= self.T_up_regreso + self.T_left_regreso:
                alpha = (t_rel - self.T_up_regreso) / self.T_left_regreso
                return dest_x + alpha * (self.x_end_spiral - dest_x)
            else:
                alpha = (t_rel - (self.T_up_regreso + self.T_left_regreso)) / T_espiral
                t_espiral_inv = T_espiral * (1 - alpha)
                r = self.r_func(t_espiral_inv)
                theta = omega * t_espiral_inv
                return r * math.cos(theta)
        return 0

    def y_truck(self, t):
        t_rel = t - self.start_time
        dest_x, dest_y = destino_coords[self.current_destino]
        
        if self.estado == 'en_cola_punto_carga':
            x, y, z = self.calcular_posicion_cola_puntos_carga()
            return y
        elif self.estado in ['esperando_en_pala', 'cargando']:
            punto = PUNTOS_CARGA[self.punto_carga_asignado]
            return punto["y"]
        elif self.estado == "yendo_punto_carga" and self.punto_carga_asignado:
            punto = PUNTOS_CARGA[self.punto_carga_asignado]
            return punto["y"]
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
        elif self.estado in ['cola_destino','en_cola_destino', 'descargando','en_chancador']:
            x, y, z = self.calcular_posicion_cola_destino(self.current_destino)
            return y
        elif self.estado == "regresando":
            if t_rel <= self.T_up_regreso:
                alpha = t_rel / self.T_up_regreso
                return dest_y + alpha * (self.y_end_spiral - dest_y)
            elif t_rel <= self.T_up_regreso + self.T_left_regreso:
                return self.y_end_spiral
            else:
                alpha = (t_rel - (self.T_up_regreso + self.T_left_regreso)) / T_espiral
                t_espiral_inv = T_espiral * (1 - alpha)
                r = self.r_func(t_espiral_inv)
                theta = omega * t_espiral_inv
                return r * math.sin(theta)
        return 0

    def z_truck(self, t):
        t_rel = t - self.start_time
        
        if self.estado == 'en_cola_punto_carga':
            x, y, z = self.calcular_posicion_cola_puntos_carga()
            return z
        elif self.estado in ["yendo_punto_carga", "cargando",'esperando_en_pala']:
            return z_min
        elif self.estado == "yendo":
            if t_rel <= T_espiral:
                return z_min + (z_max - z_min) * (t_rel / T_espiral)
            else:
                return z_max
        elif self.estado in ['cola_destino', 'en_cola_destino', 'descargando','en_chancador']:
            return z_max
        elif self.estado == "regresando":
            if t_rel <= self.T_up_regreso + self.T_left_regreso:
                return z_max
            else:
                return z_max + ((t_rel - (self.T_up_regreso + self.T_left_regreso)) / T_espiral) * (z_min - z_max)
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
                # ====== SISTEMA DE PUNTOS DE CARGA ======
                self.enter(cola_puntos_carga)
                self.actualizar_posiciones_cola_puntos_carga()
            
                # NUEVO: Registrar entrada a cola
                self.cambiar_estado("en_cola_punto_carga")
                while self != cola_puntos_carga[0]:
                    self.passivate()

                self.punto_carga_asignado = self.asignar_punto_carga()
                self.request(recurso_espera_pala)
            
                # Moverse al punto de carga asignado
                self.cambiar_estado("yendo_punto_carga")
                self.start_time = env.now()
                self.hold(2.0)

                self.cambiar_estado('esperando_en_pala')
                self.start_time = env.now()
                self.leave(cola_puntos_carga)
                self.actualizar_posiciones_cola_puntos_carga()
                if cola_puntos_carga:
                    cola_puntos_carga[0].activate()
                self.request(recurso_pala)
                
                # Cargar
                self.cambiar_estado("cargando")
                self.start_time = env.now()
                self.hold(T_carga)
            
                # Liberar pala
                self.release(recurso_pala)
                self.release(recurso_espera_pala)
                self.punto_carga_asignado = None

                # ====== SISTEMA DE DESTINOS ======
                # Ir al destino
                self.cambiar_estado("yendo")
                self.start_time = env.now()
                self.calcular_tiempos_destino(self.current_destino)
                self.hold(self.T_total_ida)

                # ASIGNAR punto de chancador ANTES de entrar a la cola (solo para planta)
                if self.current_destino == 'planta':
                    self.punto_chancador_asignado = self.asignar_punto_chancador()

                # Cola destino
                cola_destino_actual = self.get_cola_destino(self.current_destino)
                recurso_actual = self.get_recurso_destino(self.current_destino)

                self.cambiar_estado("cola_destino")
                self.enter(cola_destino_actual)
                self.actualizar_posiciones_cola_destino(self.current_destino)

                # Esperar turno en cola
                while self != cola_destino_actual[0]:
                    self.cambiar_estado("en_cola_destino")
                    self.passivate()
            
                # Solicitar recurso
                self.request(recurso_actual)
            
                # Salir de cola visual cuando obtiene el recurso
                self.leave(cola_destino_actual)
                self.actualizar_posiciones_cola_destino(self.current_destino)
                if cola_destino_actual:
                    cola_destino_actual[0].activate()

                if self.current_destino == 'planta':
                    self.cambiar_estado("en_chancador")
                    self.start_time = env.now()
                    self.request(recurso_descarga_chancador)

                # Descargar
                self.cambiar_estado("descargando")
                self.start_time = env.now()
                self.hold(T_descarga)

                if self.current_destino == 'planta':
                    self.release(recurso_descarga_chancador)
                    self.release(recurso_actual)
                    self.punto_chancador_asignado = None
                else:
                    self.release(recurso_actual)
            
                # Regresar
                self.cambiar_estado("regresando")
                self.start_time = env.now()
                tiempo_regreso = self.T_up_regreso + self.T_left_regreso + T_espiral
                self.hold(tiempo_regreso)
        
                # NUEVO: Finalizar ciclo actual y escribir en CSV
                self.finalizar_ciclo(tiempo_regreso)
            
                # Actualizar destino
                self.destino_index = (self.destino_index + 1) % len(self.destinos)
                self.current_destino = self.destinos[self.destino_index]
    
# ====== CREACIÓN DE CAMIONES ====== #
for i in range(num_camiones):
    destinos = [destinos_camiones[(i + j) % len(destinos_camiones)] for j in range(3)]
    tiempo_inicio = 0
    camion = Camion(id_camion=i, destinos=destinos, tiempo_inicio=tiempo_inicio)

# ====== CÁMARA ====== #
env.view(
    x_eye=0, y_eye=-15, z_eye=20,
    x_center=-3, y_center=4, z_center=4,
    field_of_view_y=60
)

# ====== RUN ====== #
env.run(till=300)

