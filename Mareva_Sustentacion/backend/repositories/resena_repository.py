from config.conexion import Conexion
from psycopg.errors import UniqueViolation


class ResenaRepository:

    def __init__(self):
        self.conexion = Conexion().obtener_conexion()

    def guardar(
        self,
        id_paquete,
        id_cliente,
        id_reserva,
        calificacion,
        calificacion_servicio,
        titulo,
        comentario,
    ):
        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO resena_paquete (
                    id_paquete,
                    id_cliente,
                    id_reserva,
                    calificacion,
                    calificacion_servicio,
                    titulo,
                    comentario,
                    origen
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'real')
                RETURNING id_resena
                """,
                (
                    id_paquete,
                    id_cliente,
                    id_reserva,
                    calificacion,
                    calificacion_servicio,
                    titulo or None,
                    comentario or None,
                ),
            )
            id_resena = cursor.fetchone()[0]
            self.conexion.commit()
            cursor.close()
            return {"ok": True, "id": id_resena}
        except UniqueViolation:
            self.conexion.rollback()
            cursor.close()
            return {
                "ok": False,
                "error": "Ya enviaste una opinión sobre este paquete."
            }
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return {
                "ok": False,
                "error": "No fue posible guardar tu opinión. Intenta de nuevo."
            }

    def obtener_por_paquete(self, id_paquete):
        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    rp.calificacion,
                    rp.calificacion_servicio,
                    rp.titulo,
                    rp.comentario,
                    rp.fecha_resena,
                    c.nombre,
                    c.apellido
                FROM resena_paquete rp
                JOIN cliente c ON c.id_cliente = rp.id_cliente
                WHERE rp.id_paquete = %s AND rp.estado = 'visible'
                ORDER BY rp.fecha_resena DESC, rp.id_resena DESC
                """,
                (id_paquete,),
            )
            filas = cursor.fetchall()
            cursor.close()
            self.conexion.rollback()
            return [
                {
                    "calificacion": fila[0],
                    "calificacion_servicio": fila[1],
                    "titulo": fila[2],
                    "comentario": fila[3],
                    "fecha": fila[4],
                    "nombre": fila[5],
                    "apellido": fila[6],
                }
                for fila in filas
            ]
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return []

    def ya_reseno(self, id_paquete, id_cliente):
        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                    SELECT EXISTS (
                        SELECT 1 FROM resena_paquete
                        WHERE id_paquete = %s
                          AND id_cliente = %s
                          AND origen = 'real'
                    )
                """,
                (id_paquete, id_cliente),
            )
            resultado = bool(cursor.fetchone()[0])
            cursor.close()
            self.conexion.rollback()
            return resultado
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return False

    def ya_reseno_reserva(self, id_reserva):
        if not id_reserva:
            return False

        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                    SELECT EXISTS (
                        SELECT 1 FROM resena_paquete
                        WHERE id_reserva = %s
                          AND origen = 'real'
                    )
                """,
                (id_reserva,),
            )
            resultado = bool(cursor.fetchone()[0])
            cursor.close()
            self.conexion.rollback()
            return resultado
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return False

    def obtener_encuesta_pendiente(self, id_cliente):
        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    r.id_reserva,
                    r.codigo_unico,
                    p.nombre,
                    p.slug
                FROM reserva r
                JOIN paquete_turistico p ON p.id_paquete = r.id_paquete
                WHERE r.id_cliente = %s
                  AND r.estado = 'completada'
                  AND r.encuesta_enviada
                  AND NOT EXISTS (
                      SELECT 1 FROM resena_paquete rp
                      WHERE rp.id_reserva = r.id_reserva
                  )
                ORDER BY r.fecha_viaje DESC, r.id_reserva DESC
                LIMIT 1
                """,
                (id_cliente,),
            )
            fila = cursor.fetchone()
            cursor.close()
            self.conexion.rollback()

            if not fila:
                return None

            return {
                "id_reserva": fila[0],
                "codigo_unico": fila[1],
                "paquete": fila[2],
                "slug": fila[3],
            }
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return None

    def obtener_reserva_valida(self, id_reserva, id_cliente):
        cursor = self.conexion.cursor()

        try:
            cursor.execute(
                """
                SELECT r.id_reserva, r.id_paquete, r.codigo_unico, p.nombre, p.slug
                FROM reserva r
                JOIN paquete_turistico p ON p.id_paquete = r.id_paquete
                WHERE r.id_reserva = %s
                  AND r.id_cliente = %s
                  AND r.estado = 'completada'
                """,
                (id_reserva, id_cliente),
            )
            fila = cursor.fetchone()
            cursor.close()
            self.conexion.rollback()

            if not fila:
                return None

            return {
                "id_reserva": fila[0],
                "id_paquete": fila[1],
                "codigo_unico": fila[2],
                "paquete": fila[3],
                "slug": fila[4],
            }
        except Exception:
            self.conexion.rollback()
            cursor.close()
            return None
