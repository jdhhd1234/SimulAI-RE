from BPTK_Py import Model

def create_model(starttime: float, stoptime: float, dt: float, name: str):

    model = Model(
        starttime=starttime,
        stoptime=stoptime,
        dt=dt,
        name=name
    )

    return model