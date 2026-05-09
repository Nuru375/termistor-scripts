# -*- coding: utf-8 -*-
"""
@author: Agustin O. Umedez

Script para medir temperatura utilizando un termistor caracterizado y un multímetro HP 34401A.
"""

import serial
import time
import csv
import numpy as np
from auxiliar.analysis import DigitalData
from auxiliar.instruments import HP34401A
from auxiliar.AnalisisDatos import ajuste

# Caracterización del termistor
root = "mediciones.csv"
p, uA = ajuste(root)
a, b = p
uA_a, uA_b = uA
temperatura = lambda R: b/(np.log(R) - a)

# Configuración del puerto
PUERTO_MULTIMETRO = 'COM9'
INTERVALO = 0.5 # s
BAUD_RATE = 9600
TIMEOUT = 2 # Timeout generoso
ARCHIVO_DESTINO = "nuevas_mediciones.csv"

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
        writer.writerow(["Tiempo (s)", "Temperatura (K)", "Incertidumbre (K)"])
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
                
                if not linea_multimetro:
                    print("Timeout: El multímetro no respondió a tiempo.")
                else:
                    """Error de la medición de temperatura desde el multímetro"""
                    x = DigitalData(
                        data=float(linea_multimetro),
                        instrument=HP34401A(T=16),
                        instr_mode="DC_Resistance"
                    )
                    R_read, uB = x.fast()
                    T_read = temperatura(R_read) # [K]
                    uA = T_read*np.sqrt(
                        (a*(-b/(np.log(R_read) - a)**2))**2
                        + (b/(np.log(R_read) - a))**2
                        + (R_read*b/(np.log(R_read) - a)**2*1/R_read)**2
                    )
                    U = np.sqrt(uA**2 + uB**2)
                    
                    t_relativo = ahora - t_inicio
                    writer.writerow([f"{t_relativo:.3f}", T_read, U]) # Mide en Kelvin
                    file.flush()
                    
                    print(f"[{t_relativo:6.3f}s] T: {T_read - 273.15} +/- {U - 273.15} C") # En pantalla muestro en Celcius
                
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
            # Volvemos a modo local antes de cerrar para que se puedan usar los botones
            multimetro.write(b'SYST:LOC\r\n')
            # Cerramos el puerto del Multímetro
            multimetro.close()
            
            print("Puerto cerrado con éxito.")

if __name__ == "__main__":
    capturar_datos()
