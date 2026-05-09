# -*- coding: utf-8 -*-
"""
@author: Agustin O. Umedez

Obtención de los parámetros 'a' y 'b' del termistor, así como sus incertidumbres.
"""

import numpy as np
import pandas as pd

def ajuste(root):
    # Extraigo los datos de interés y ajusto unidades
    df = pd.read_csv(root)
    df['Temperatura (K)'] = df['Temperatura (C)'] + 273.15
    
    # Ajuste lineal
    Y = np.log(df['Resistencia (Ohm)'])
    X = 1 / df['Temperatura (K)']
    p, pcov = np.polyfit(X, Y, 1, cov=True)
    uA = np.sqrt(np.diag(pcov))
    
    return p, uA

