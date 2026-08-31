import numpy as np
import scipy as sp

def normalize(data: np.ndarray):
    log_data = np.log10(data)
    print(log_data)


arr = np.array([323, 120000, 3274, 378354, 383649, 283464])