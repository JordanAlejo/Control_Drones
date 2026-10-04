#include <Keypad.h>


// ============================================================
// CONFIGURACIÓN DEL TECLADO
// ============================================================

const byte FILAS = 4;
const byte COLUMNAS = 4;


// ============================================================
// MAPA DEL TECLADO
// ============================================================

char teclas[FILAS][COLUMNAS] =
{
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'}
};


// ============================================================
// PINES DE LAS FILAS
// ============================================================

byte pinesFilas[FILAS] =
{
    13,
    14,
    27,
    26
};


// ============================================================
// PINES DE LAS COLUMNAS
// ============================================================

byte pinesColumnas[COLUMNAS] =
{
    25,
    33,
    32,
    35
};


// ============================================================
// CREAR TECLADO
// ============================================================

Keypad teclado = Keypad(
    makeKeymap(teclas),
    pinesFilas,
    pinesColumnas,
    FILAS,
    COLUMNAS
);


// ============================================================
// CONFIGURACIÓN
// ============================================================

void setup()
{
    Serial.begin(115200);

    delay(2000);

    Serial.println(
        "ESP32 LISTA"
    );

    Serial.println(
        "Esperando teclado..."
    );
}


// ============================================================
// LOOP
// ============================================================

void loop()
{

    // --------------------------------------------------------
    // LEER TECLADO
    // --------------------------------------------------------

    char tecla = teclado.getKey();


    // --------------------------------------------------------
    // SI SE PULSÓ UNA TECLA
    // --------------------------------------------------------

    if (tecla)
    {

        Serial.println(
            tecla
        );


        // ----------------------------------------------------
        // INFORMACIÓN LOCAL
        // ----------------------------------------------------

        if (tecla == 'A')
        {
            Serial.println(
                "ORDEN: IR AL PUNTO A"
            );
        }


        else if (tecla == 'B')
        {
            Serial.println(
                "ORDEN: IR AL PUNTO B"
            );
        }


        else if (tecla == 'D')
        {
            Serial.println(
                "ORDEN: IR AL PUNTO D"
            );
        }


        else if (tecla == '*')
        {
            Serial.println(
                "ORDEN: VOLVER AL INICIO"
            );
        }


        else if (tecla == '#')
        {
            Serial.println(
                "ORDEN: ATERRIZAR"
            );
        }


        else
        {
            Serial.print(
                "Tecla: "
            );

            Serial.println(
                tecla
            );
        }


        // ----------------------------------------------------
        // PEQUEÑA PAUSA
        // ----------------------------------------------------

        delay(150);
    }
}