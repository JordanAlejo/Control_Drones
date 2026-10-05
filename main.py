import time
import serial
import numpy as np
import msvcrt

from gym_pybullet_drones.envs.VelocityAviary import VelocityAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync


# ============================================================
# CONFIGURACIÓN
# ============================================================

PUERTO_ESP32 = "COM4"
BAUDRATE = 115200

NUM_DRONES = 3

SIMULATION_FREQ = 240
CONTROL_FREQ = 48

ALTURA = 1.0

# Velocidad de desplazamiento hacia el punto
VELOCIDAD = 0.8

# ------------------------------------------------------------
# CONFIGURACIÓN DEL CÍRCULO
# ------------------------------------------------------------

RADIO_CIRCULO = 0.8

VELOCIDAD_CIRCULO = 0.6

# Qué tan rápido gira cada drone alrededor del centro
VELOCIDAD_ANGULAR = VELOCIDAD_CIRCULO / RADIO_CIRCULO


# ============================================================
# POSICIONES INICIALES
# ============================================================

INIT_XYZS = np.array([
    [-1.5, 0.0, ALTURA],
    [ 0.0, 0.0, ALTURA],
    [ 1.5, 0.0, ALTURA]
])

INIT_RPYS = np.array([
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
])


# ============================================================
# PUNTOS A, B Y C
# ============================================================

PUNTOS = {

    "A": np.array([
        -1.5,
         1.5,
         ALTURA
    ]),

    "B": np.array([
         0.0,
         1.5,
         ALTURA
    ]),

    "C": np.array([
         1.5,
         1.5,
         ALTURA
    ])
}


# ============================================================
# CONEXIÓN ESP32
# ============================================================

print()
print("======================================")
print(" CONECTANDO CON ESP32")
print("======================================")

try:

    esp32 = serial.Serial(
        port=PUERTO_ESP32,
        baudrate=BAUDRATE,
        timeout=0.1
    )

    time.sleep(2)

    print("ESP32 conectada correctamente.")
    print("Puerto:", PUERTO_ESP32)

except Exception as e:

    print()
    print("ERROR conectando con la ESP32")
    print(e)
    print()

    esp32 = None


# ============================================================
# FUNCIÓN PARA ENVIAR A ESP32
# ============================================================

def enviar_esp32(mensaje):

    if esp32 is not None:

        mensaje = mensaje + "\n"

        esp32.write(
            mensaje.encode("utf-8")
        )

        print(
            "[PC -> ESP32]",
            mensaje.strip()
        )


# ============================================================
# CREAR SIMULACIÓN
# ============================================================

print()
print("======================================")
print(" INICIANDO PYBULLET")
print("======================================")

env = VelocityAviary(

    drone_model=DroneModel.CF2X,

    num_drones=NUM_DRONES,

    initial_xyzs=INIT_XYZS,

    initial_rpys=INIT_RPYS,

    physics=Physics.PYB,

    pyb_freq=SIMULATION_FREQ,

    ctrl_freq=CONTROL_FREQ,

    gui=True,

    record=False,

    obstacles=False,

    user_debug_gui=False
)


# ============================================================
# RESET
# ============================================================

obs, info = env.reset()


# ============================================================
# VARIABLES DE CONTROL
# ============================================================

# Punto al que actualmente se dirigen
punto_actual = None

# Centro actual del círculo
centro_circulo = None

# Indica si ya llegó al destino
volando = True

# Ángulo inicial de cada drone
angulos = np.array([
    0.0,
    2.0 * np.pi / 3.0,
    4.0 * np.pi / 3.0
])


# ============================================================
# POSICIÓN DEL CENTRO DE LA FORMACIÓN
# ============================================================

def obtener_centro_drones():

    posiciones = np.array([
        obs[i][0:3]
        for i in range(NUM_DRONES)
    ])

    return np.mean(posiciones, axis=0)


# ============================================================
# VELOCIDAD HACIA UN PUNTO
# ============================================================

def calcular_velocidad(posicion, objetivo):

    error = objetivo - posicion

    distancia = np.linalg.norm(error)

    if distancia < 0.08:

        return np.zeros(3)

    direccion = error / distancia

    velocidad = direccion * VELOCIDAD

    # Evitar exceder la velocidad máxima
    velocidad = np.clip(
        velocidad,
        -VELOCIDAD,
        VELOCIDAD
    )

    return velocidad


# ============================================================
# VELOCIDAD PARA FORMAR EL CÍRCULO
# ============================================================

def calcular_velocidad_circulo(
    posicion,
    centro,
    angulo_deseado
):

    # --------------------------------------------------------
    # POSICIÓN DESEADA DEL DRONE EN EL CÍRCULO
    # --------------------------------------------------------

    posicion_deseada = np.array([

        centro[0] +
        RADIO_CIRCULO * np.cos(angulo_deseado),

        centro[1] +
        RADIO_CIRCULO * np.sin(angulo_deseado),

        centro[2]

    ])

    # --------------------------------------------------------
    # CONTROL HACIA LA POSICIÓN DESEADA
    # --------------------------------------------------------

    error = posicion_deseada - posicion

    distancia = np.linalg.norm(error)

    if distancia > 0.05:

        velocidad = error / distancia * VELOCIDAD_CIRCULO

    else:

        velocidad = np.zeros(3)

    return velocidad


# ============================================================
# CAMBIAR DE PUNTO
# ============================================================

def seleccionar_punto(nombre):

    global punto_actual
    global centro_circulo
    global volando

    nombre = nombre.upper()

    # D será equivalente a C
    if nombre == "D":

        nombre = "C"

    if nombre not in PUNTOS:

        return

    punto_actual = PUNTOS[nombre].copy()

    centro_circulo = punto_actual.copy()

    volando = True

    print()
    print("======================================")
    print(" NUEVO DESTINO")
    print("======================================")

    print(
        f"Punto seleccionado: {nombre}"
    )

    print(
        f"Destino: {punto_actual}"
    )

    print()

    enviar_esp32(
        "DESTINO_" + nombre
    )


# ============================================================
# TECLADO
# ============================================================

def leer_teclado():

    if not msvcrt.kbhit():

        return None

    tecla = msvcrt.getch()

    try:

        tecla = tecla.decode(
            "utf-8"
        ).upper()

    except:

        return None

    return tecla


# ============================================================
# ENVIAR INICIO
# ============================================================

enviar_esp32("INICIO")

time.sleep(1)


# ============================================================
# INFORMACIÓN
# ============================================================

print()
print("======================================")
print(" DRONES CREADOS")
print("======================================")

for i in range(NUM_DRONES):

    print(
        f"Drone {i}: "
        f"{INIT_XYZS[i]}"
    )

print()
print("======================================")
print(" CONTROL DE DRONES")
print("======================================")

print()
print(" A -> Ir al punto A")
print(" B -> Ir al punto B")
print(" C -> Ir al punto C")
print(" D -> Ir al punto C")
print()
print(" ESC / Ctrl+C -> Salir")
print()

print("Los drones están esperando una orden.")
print()


# ============================================================
# SIMULACIÓN
# ============================================================

START = time.time()

paso = 0

# Tiempo utilizado para el círculo
ultimo_tiempo = time.time()


try:

    while True:

        # ====================================================
        # LEER TECLADO
        # ====================================================

        tecla = leer_teclado()

        if tecla is not None:

            if tecla in ["A", "B", "C", "D"]:

                seleccionar_punto(tecla)

            elif tecla == "\x1b":

                break


        # ====================================================
        # LEER ESP32
        # ====================================================

        if esp32 is not None:

            while esp32.in_waiting:

                dato = esp32.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if dato:

                    print(
                        "[ESP32 -> PC]",
                        dato
                    )


        # ====================================================
        # CREAR ACTION
        # ====================================================

        action = np.zeros(
            (NUM_DRONES, 4)
        )


        # ====================================================
        # SI TODAVÍA NO HAY DESTINO
        # ====================================================

        if punto_actual is None:

            for i in range(NUM_DRONES):

                action[i, 0] = 0.0
                action[i, 1] = 0.0
                action[i, 2] = 0.0

                action[i, 3] = 1.0


        # ====================================================
        # IR HACIA EL PUNTO
        # ====================================================

        elif volando:

            todos_llegaron = True

            for i in range(NUM_DRONES):

                posicion = obs[i][0:3]

                velocidad = calcular_velocidad(
                    posicion,
                    punto_actual
                )

                action[i, 0] = velocidad[0]
                action[i, 1] = velocidad[1]
                action[i, 2] = velocidad[2]

                action[i, 3] = 1.0


                distancia = np.linalg.norm(
                    punto_actual - posicion
                )

                if distancia > 0.15:

                    todos_llegaron = False


            # ------------------------------------------------
            # LOS 3 DRONES YA LLEGARON
            # ------------------------------------------------

            if todos_llegaron:

                volando = False

                centro_circulo = punto_actual.copy()

                # Reiniciar posiciones angulares
                angulos = np.array([
                    0.0,
                    2.0 * np.pi / 3.0,
                    4.0 * np.pi / 3.0
                ])

                print()
                print(
                    ">>> DESTINO ALCANZADO"
                )

                print(
                    ">>> INICIANDO VUELO CIRCULAR"
                )

                enviar_esp32(
                    "CIRCULO"
                )


        # ====================================================
        # VOLAR EN CÍRCULO
        # ====================================================

        else:

            tiempo_actual = time.time()

            dt = tiempo_actual - ultimo_tiempo

            ultimo_tiempo = tiempo_actual


            # ------------------------------------------------
            # ACTUALIZAR ÁNGULOS
            # ------------------------------------------------

            for i in range(NUM_DRONES):

                angulos[i] += (
                    VELOCIDAD_ANGULAR * dt
                )

                # Mantener entre 0 y 2PI
                angulos[i] %= (
                    2.0 * np.pi
                )


            # ------------------------------------------------
            # CONTROLAR CADA DRONE
            # ------------------------------------------------

            for i in range(NUM_DRONES):

                posicion = obs[i][0:3]

                velocidad = calcular_velocidad_circulo(

                    posicion,

                    centro_circulo,

                    angulos[i]

                )

                action[i, 0] = velocidad[0]
                action[i, 1] = velocidad[1]
                action[i, 2] = velocidad[2]

                action[i, 3] = 1.0


        # ====================================================
        # AVANZAR SIMULACIÓN
        # ====================================================

        obs, reward, terminated, truncated, info = env.step(
            action
        )


        # ====================================================
        # MOSTRAR POSICIONES
        # ====================================================

        if paso % CONTROL_FREQ == 0:

            print()

            for i in range(NUM_DRONES):

                posicion = obs[i][0:3]

                print(
                    f"D{i}: "
                    f"X={posicion[0]:+.2f} "
                    f"Y={posicion[1]:+.2f} "
                    f"Z={posicion[2]:+.2f}"
                )

            if punto_actual is not None:

                if volando:

                    print(
                        "Estado: VOLANDO AL DESTINO"
                    )

                else:

                    print(
                        "Estado: VOLANDO EN CÍRCULO"
                    )


        # ====================================================
        # SINCRONIZAR
        # ====================================================

        sync(
            paso,
            START,
            env.CTRL_TIMESTEP
        )

        paso += 1


except KeyboardInterrupt:

    print()
    print("Deteniendo simulación...")


finally:

    enviar_esp32("STOP")

    env.close()

    if esp32 is not None:

        esp32.close()

    print()
    print("Programa terminado.")