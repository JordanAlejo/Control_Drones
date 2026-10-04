import time
import serial
import numpy as np

from gym_pybullet_drones.envs.VelocityAviary import VelocityAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync


# ============================================================
# CONFIGURACIÓN
# ============================================================

PUERTO_ESP32 = "COM4"       # <-- CAMBIA ESTO
BAUDRATE = 115200

NUM_DRONES = 3

SIMULATION_FREQ = 240
CONTROL_FREQ = 48

ALTURA = 1.0

# Velocidad máxima de desplazamiento
VELOCIDAD = 0.8


# ============================================================
# POSICIONES INICIALES
# ============================================================

INIT_XYZS = np.array([
    [-1.5, 0.0, ALTURA],    # Drone 0
    [ 0.0, 0.0, ALTURA],    # Drone 1
    [ 1.5, 0.0, ALTURA]     # Drone 2
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
# FUNCIÓN PARA ENVIAR A LA ESP32
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
# ESTADO DE LOS DRONES
# ============================================================

objetivos = np.copy(INIT_XYZS)


# ============================================================
# ENVIAR INICIO A ESP32
# ============================================================

enviar_esp32("INICIO")

time.sleep(1)


# ============================================================
# MOSTRAR INFORMACIÓN
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
print("Puntos disponibles:")

for nombre, posicion in PUNTOS.items():

    print(
        f"{nombre} -> {posicion}"
    )

print()


# ============================================================
# FUNCIÓN PARA CALCULAR VELOCIDAD
# ============================================================

def calcular_velocidad(posicion_actual, objetivo):

    error = objetivo - posicion_actual

    distancia = np.linalg.norm(error)

    if distancia < 0.05:

        return np.array([
            0.0,
            0.0,
            0.0
        ])

    direccion = error / distancia

    velocidad = direccion * VELOCIDAD

    return velocidad


# ============================================================
# SIMULACIÓN
# ============================================================

print("Simulación iniciada.")
print()


START = time.time()

paso = 0


try:

    while True:

        # ----------------------------------------------------
        # COMPROBAR DATOS RECIBIDOS DESDE ESP32
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # CALCULAR VELOCIDAD DE CADA DRON
        # ----------------------------------------------------

        action = np.zeros(
            (NUM_DRONES, 4)
        )


        for i in range(NUM_DRONES):

            posicion = obs[i][0:3]

            velocidad = calcular_velocidad(
                posicion,
                objetivos[i]
            )

            action[i, 0] = velocidad[0]
            action[i, 1] = velocidad[1]
            action[i, 2] = velocidad[2]

            # 1 = dron activo
            action[i, 3] = 1.0


        # ----------------------------------------------------
        # AVANZAR SIMULACIÓN
        # ----------------------------------------------------

        obs, reward, terminated, truncated, info = env.step(
            action
        )


        # ----------------------------------------------------
        # MOSTRAR POSICIONES
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # SINCRONIZAR
        # ----------------------------------------------------

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

    print("Programa terminado.")