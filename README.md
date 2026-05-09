# termistor-scripts
En este repositorio se guardan los scripts de Python y Arduino utilizados para este trabajo.

## Caracterización del termistor
El archivo ".ino" se utilizó para configurar la lectura de temperatura para un sensor de temperatura KY-013 (módulo para Arduino).
El archivo "ScriptMultimetroArduino.py" controla en paralelo un multímetro HP-34401A y un Arduino Uno. Mide resistencia y temperatura para intervalos fijos de tiempo (por defecto, 0.5 segundos).
A partir de los datos almacenados en el csv, se debe realizar los ajustes correspondientes y obtener los parámetros "a" y "b" del termistor. Este script no incluye dicho tratamiento, el mismo se puede hallar en "AnalisisDatos.py" dentro de la carpeta "auxiliar".

## Termómetro c/ multímetro HP 34401A
El archivo "TermometroMultimetro.py" se utiliza para medir temperatura una vez caracterizado el termistor (es decir, que se cuenta con los parámetros "a" y "b" del mismo). El mismo calcula de forma automática la incertidumbre asociada a los parámetros del termistor, así como la incertidumbre asociada al multímetro HP-34401A.

## Carpeta 'auxiliar'
Contiene funciones, clases y demás archivos auxiliares que fueron utilizados para el trabajo.
