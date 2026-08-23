import numpy as np
import pandas as pd

import random

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
normal_asset = 61.3
myasset = np.random.normal(loc=normal_asset, scale=1, size=1000)
print(myasset[0])