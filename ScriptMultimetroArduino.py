# -*- coding: utf-8 -*-
"""
@author: Agustin O. Umedez

Script para medir temperatura y resistencia en paralelo usando un arduino y un multímetro HP 34401A
"""

import serial
import time
import csv

# Configuración del puerto
PUERTO_MULTIMETRO = 'COM9'
PUERTO_ARDUINO    = 'COM8'
INTERVALO = 0.5 # s
BAUD_RATE = 9600
TIMEOUT = 2 # Timeout generoso
ARCHIVO_DESTINO = "mediciones.csv"

multimetro = serial.Serial(
    port=PUERTO_MULTIMETRO,
    baudrate=BAUD_RATE,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS,
    timeout=TIMEOUT
)

# Líneas de control para habilitar el puerto en equipos viejos
multimetro.dtr = True
multimetro.rts = True

print("Estableciendo conexión con el arduino...")
# Abrimos el puerto serie
arduino = serial.Serial(
    port=PUERTO_ARDUINO,
    baudrate=BAUD_RATE,
    timeout=TIMEOUT
)
# Esperamos 2 segundos para que el Arduino se reinicie al conectar
time.sleep(2)

def configurar_multimetro():    
    print("Estableciendo conexión remota...")
    # 1. FORZAR MODO REMOTO
    multimetro.write(b'SYST:REM\r\n')
    time.sleep(0.2)
    
    # 2. LIMPIAR ERRORES PREVIOS
    multimetro.write(b'*CLS\r\n')
    time.sleep(0.1)
    
    # 3. RESET Y CONFIGURACIÓN
    print("Configurando rango fijo de 10kOhm...")
    multimetro.write(b'*RST\r\n')
    time.sleep(0.1)
    multimetro.write(b'CONF:RES 10000\r\n') # Rango fijo 10k
    
    # 4. VELOCIDAD DE MUESTREO (NPLC)
    # 1 NPLC es el balance justo para 0.5s de intervalo.
    multimetro.write(b'SENSE:RES:NPLC 1\r\n')
    
    time.sleep(0.5)
    print("Instrumento listo y en modo Rmt.")

def capturar_datos():
    configurar_multimetro()
    
    with open(ARCHIVO_DESTINO, mode='w', newline='', buffering=1) as file:
        writer = csv.writer(file)
        writer.writerow(["Tiempo (s)", "Resistencia (Ohm)", "Temperatura (C)"])
        file.flush()
        
        print(f"Captura iniciada. Guardando en {ARCHIVO_DESTINO}...")
        print("Presione Ctrl+C para detener.")
        
        t_inicio = time.perf_counter()
        next_sample = t_inicio
        
        try:
            while True:
                # Usamos perf_counter para máxima precisión en el tiempo relativo
                ahora = time.perf_counter()
                
                # Pedir lectura del Multímetro
                multimetro.write(b'READ?\r\n')
                linea_multimetro = multimetro.readline().decode('ascii').strip()
                # Pedir lectura del Arduino
                linea_arduino = arduino.readline().decode('utf-8').strip()
                
                if not linea_multimetro:
                    print("Timeout: El multímetro no respondió a tiempo.")
                if not linea_arduino:
                    print("Timeout: El arduino no respondió a tiempo.")
                else:
                    t_relativo = ahora - t_inicio
                    writer.writerow([f"{t_relativo:.3f}", linea_multimetro, linea_arduino])
                    file.flush()
                    
                    print(f"[{t_relativo:6.3f}s] R: {linea_multimetro} Ohm | T: {linea_arduino} C")
                
                # Metrónomo de precisión para los 0.5s
                next_sample += INTERVALO
                sleep_time = next_sample - time.perf_counter()
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Si el procesamiento tardó más de 0.5s, resincronizamos
                    print("Warning: Latencia detectada, ajustando tiempo...")
                    next_sample = time.perf_counter()
                    
        except Exception as e:
            print(f"Error en el sistema: {e}")
        
        except KeyboardInterrupt:
            print("\nFinalizando captura y liberando equipo...")
            
        finally:
            # Cerramos el puerto del Arduino
            arduino.close()
            
            # Volvemos a modo local antes de cerrar para que se puedan usar los botones
            multimetro.write(b'SYST:LOC\r\n')
            # Cerramos el puerto del Multímetro
            multimetro.close()
            
            print("Puertos cerrados con éxito.")

if __name__ == "__main__":
    capturar_datos()
