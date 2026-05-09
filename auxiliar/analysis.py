# -*- coding: utf-8 -*-
"""
@author: Agustin O. Umedez

Archivo auxiliar para tratar la incertidumbre asociado al multímetro
Contiene el objeto DigitalData con los métodos para obtener la incertidumbre de forma automática.
"""

import numpy as np
import scipy.stats as st

class Data:
    def __init__(self, data):
        self.data = np.array(data)
        # mode: 0 [univariado], 1 [bivariado (x, y)]
        self.mode = 0 if len(self.data.shape)==1 else 1

    def mean(self):
        return np.mean(self.data, axis=1) if self.mode else np.mean(self.data)

    def std_mean(self):
        """Error estándar de la media (Tipo A)"""
        n = self.data.shape[1] if self.mode else len(self.data)
        return np.std(self.data, axis=1 if self.mode else 0, ddof=1) / np.sqrt(n)

    def linear_fit(self, values=True, stats=False):
        if not self.mode or len(self.data) < 2:
            raise ValueError("So' un wachin, te falta el eje X o datos suficientes.")
        
        x, y = self.data
        params, cov = np.polyfit(x, y, deg=1, cov=True)
        
        if values:
            xs = np.linspace(x[0], x[-1])
            ys = np.polyval(params, xs)
        
        if stats:
            m, p = params
            sdv_m, sdv_p = np.sqrt(np.diag(cov))
            return ((m, sdv_m), (p, sdv_p)) if not values else ((m, sdv_m), (p, sdv_p), ys)
        return params if not values else (params, ys)

class DigitalData(Data):
    def __init__(self, data, instrument, instr_mode="DC_Voltage", period="1y"):
        super().__init__(data)
        self.instrument = instrument # Objeto de la clase HP34401A o similar
        self.instr_mode = instr_mode
        self.period = period

    def get_uB(self, value):
        """Obtiene la incertidumbre Tipo B del instrumento."""
        return self.instrument.calculate_error(value, self.instr_mode, self.period)

    def fast(self, sigmas=1):
        """Reporte rápido con propagación completa."""
        # Factor de cobertura k (t-Student)
        conf = {
            1: 0.68,
            2: 0.95,
            3: 0.997
        }
        dof = (self.data.shape[1] if self.mode else len(self.data)) - 1
        k = st.t.ppf(1 - (1 - conf[sigmas])/2, df=dof)

        if not self.mode:
            # Caso una sola magnitud
            val_mean = self.mean()
            uA = self.std_mean()
            uB = self.get_uB(val_mean)
            uC = np.sqrt(uA**2 + uB**2)
            return val_mean, k * uC
        
        else:
            # Caso ajuste lineal (Propagación en la pendiente)
            M, P = self.linear_fit(values=False, stats=True)
            m, sm = M # m: pendiente, sm: error del ajuste (Tipo A)
            p, sp = P
            
            # Error instrumental medio (Tipo B)
            x_mean = np.mean(self.data[0])
            y_mean = np.mean(self.data[1])
            uB_x = self.get_uB(x_mean)
            uB_y = self.get_uB(y_mean)

            # Propagación simplificada a la pendiente
            # sigma_m^2 = (sm_fit)^2 + (uB_slope)^2
            # Aquí uB_slope se aproxima por la propagación de errores sistemáticos
            uB_m = m * np.sqrt((uB_y/y_mean)**2 + (uB_x/x_mean)**2)
            uB_p = p * np.sqrt((uB_y/y_mean)**2 + (uB_x/x_mean)**2)
            
            uC_m = np.sqrt(sm**2 + uB_m**2)
            uC_p = np.sqrt(sp**2 + uB_p**2)
            return (m, k * uC_m), (p, k * uC_p)
