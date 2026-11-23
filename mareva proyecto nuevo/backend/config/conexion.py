import atexit
import os
import threading

import psycopg
from dotenv import load_dotenv


load_dotenv()


class Conexion:
    """
    Envuelve una conexión de PostgreSQL y la abre solo cuando se usa.

    Antes cada repositorio abría una conexión al instanciarse. Como los
    controladores se crean al importar la app, eso agotaba el límite de
    conexiones de PostgreSQL ("ya tenemos demasiados clientes") y las
    reservas dejaban de guardarse.
    """

    _lock = threading.Lock()
    _conexiones = []

    def __init__(self):
        self._conexion = None

    def _obtener(self):
        if self._conexion is None or self._conexion.closed:
            with self._lock:
                if self._conexion is None or self._conexion.closed:
                    self._conexion = psycopg.connect(
                        host=os.getenv("DB_HOST"),
                        dbname=os.getenv("DB_NAME"),
                        user=os.getenv("DB_USER"),
                        password=os.getenv("DB_PASSWORD"),
                        port=os.getenv("DB_PORT"),
                    )
                    Conexion._conexiones.append(self._conexion)
        return self._conexion

    def cursor(self, *args, **kwargs):
        return self._obtener().cursor(*args, **kwargs)

    def commit(self):
        self._obtener().commit()

    def rollback(self):
        self._obtener().rollback()

    def close(self):
        if self._conexion is not None and not self._conexion.closed:
            self._conexion.close()

    def obtener_conexion(self):
        return self


@atexit.register
def _cerrar_conexiones():
    for conexion in list(Conexion._conexiones):
        try:
            if not conexion.closed:
                conexion.close()
        except Exception:
            pass
