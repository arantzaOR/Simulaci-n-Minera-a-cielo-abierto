import salabim as sim
import math
sim.reset()

####### Zona estética ########
'''Aquí se pueden añadir elementos para mejorar la apariencia de la simulación
   sin que afecten a la lógica de la simulación
   Esto se hace con el objetivo de que la simulación sea más comprensible
   e intuitiva'''

# ====== ENTORNO ====== #
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
sim.Animate3dBox(x_len=1, y_len=1, z_len=1, color = 'gray',
                 x=0,y=0,z=0)
                 

# Grilla que representa el suelo (z=0)
# Se hace en z=5 puesto que no reconoce coordenadas negativas en z
sim.Animate3dGrid(x_range=range(-10,11), y_range=range(-10,11), z_range=[10], color="lightgray")

######## Zona de movimiento ########
'''Aquí se definen las funciones necesarias para las trayectorias generales'''
# ====== PARÁMETROS DE MOVIMIENTO ====== #
omega = 2 * math.pi / 5   # velocidad angular de la espiral
R_max = 5                 # radio máximo al salir de la espiral
z_min, z_max = 0.0, 10.0   # altura de inicio y final de la espiral

# Los tiempos representan la duración de cada fase del movimiento
# en segundos
T_inicial=0.0
T_carga = 2.0
T_espiral = 10.0    # tiempo para completar la espiral (subir a z=5)
T_left   = 5.0      # tiempo para moverse en x negativo (alejarse del hoyo)
T_up     = 6.0      # tiempo para moverse en y positivo hasta el botadero
T_total  = T_espiral + T_left + T_up

destino = "botadero"  # opciones: "botadero", "stock", "planta"

# coordenadas destino
# Botadero
bot_x = -5.0
bot_y = 8.0
# Stock
st_x = 4.0
st_y = 8.0
# Planta
pl_x = 0.0
pl_y = 8.0

# ====== ESPIRAL ======
def z_func(t):
    if t <= T_espiral:
        return z_min + (z_max - z_min) * (t / T_espiral)
    else:
        return z_max

def r_func(t):
    # evita división por cero
    return 0.0 if z_max == 0 else (z_func(t) / z_max) * R_max

def spiral_pos(t):
    r = r_func(t)
    theta = omega * t
    return r * math.cos(theta), r * math.sin(theta)

# calculamos la posición exacta al terminar la espiral
x_end_spiral, y_end_spiral = spiral_pos(T_espiral)

# ====== FUNCIONES X, Y, Z por fases ======
def x_truck(t):
    if t <= T_espiral:
        x, y = spiral_pos(t)
        return x
    elif t <= T_espiral + T_left:
        # Movimiento lateral hacia el destino elegido
        alpha = (t - T_espiral) / T_left
        if destino == "botadero":
            return x_end_spiral + alpha * (bot_x - x_end_spiral)
        elif destino == "planta":
            return x_end_spiral + alpha * (pl_x - x_end_spiral)
        elif destino == "stock":
            return x_end_spiral + alpha * (st_x - x_end_spiral)
    # elif t <= T_espiral + T_left:
    #     # interpola linealmente desde x_end_spiral hasta bot_x (x negativo)
    #     alpha = (t - T_espiral) / T_left  # 0..1
        return x_end_spiral + alpha * (bot_x - x_end_spiral)
    elif t <= T_total:
        if destino == "botadero":
            return bot_x
        elif destino == "stock":
            return st_x
        elif destino == "planta":
            return pl_x
    else:
        if destino == "botadero":
            return bot_x
        elif destino == "stock":
            return st_x
        elif destino == "planta":
            return pl_x

def y_truck(t):
    if t <= T_espiral:
        x, y = spiral_pos(t)
        return y
    elif t <= T_espiral + T_left:
        # mientras se mueve en x, mantener la misma y final de la espiral
        return y_end_spiral
    elif t <= T_total:
        alpha = (t - (T_espiral+T_left)) / T_up
        if destino == "botadero":
            return y_end_spiral + alpha * (bot_y - y_end_spiral)
        elif destino == "stock":
            return y_end_spiral + alpha * (st_y - y_end_spiral)
        elif destino == "planta":
            return y_end_spiral + alpha * (pl_y - y_end_spiral)  
    else:
        if destino == "botadero":
            return bot_y
        elif destino == "stock":
            return st_y
        elif destino == "planta":
            return pl_y

def z_truck(t):
    # z sube con la espiral y luego se mantiene en z_max
    return z_func(t)

# ====== CAMIÓN (Animate3dBox) ======
sim.Animate3dBox(
    x_len=0.6, y_len=0.6, z_len=0.6, color="pink",
    x=x_truck, y=y_truck, z=z_truck
)

# ====== Dibujar la ruta planificada (puntos pequeños rojos) ======
n_points = 500
for i in range(n_points):
    t_sample = i * (T_total) / (n_points - 1)
    sim.Animate3dBox(
        x_len=0.06, y_len=0.06, z_len=0.06, color="red",
        x=spiral_pos(t_sample)[0] if t_sample <= T_espiral else (bot_x if t_sample > T_espiral else 0),
        y=spiral_pos(t_sample)[1] if t_sample <= T_espiral else (y_end_spiral + ( (t_sample - T_espiral)/ (T_left+T_up) )*(bot_y - y_end_spiral) if t_sample > T_espiral else 0),
        z=z_truck(t_sample)
    )

# ====== CÁMARA ======
env.view(
    x_eye=0, y_eye=-15, z_eye=20,
    x_center=-3, y_center=4, z_center=4,
    field_of_view_y=60
)
# ====== RUN ======
env.run(till=24)

