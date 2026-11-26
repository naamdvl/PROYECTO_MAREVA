from repositories.resena_repository import ResenaRepository


class ResenaService:

    def __init__(self):
        self.repository = ResenaRepository()

    @staticmethod
    def _calificacion_valida(valor):
        try:
            return 1 <= int(valor) <= 5
        except (TypeError, ValueError):
            return False

    def guardar(
        self,
        id_paquete,
        id_cliente,
        id_reserva,
        calificacion,
        calificacion_servicio=None,
        titulo="",
        comentario="",
    ):
        if not self._calificacion_valida(calificacion):
            return {
                "ok": False,
                "error": "Selecciona una valoración de 1 a 5 estrellas."
            }

        if calificacion_servicio not in (None, "") and not self._calificacion_valida(
            calificacion_servicio
        ):
            return {
                "ok": False,
                "error": "Selecciona una valoración del servicio de 1 a 5 estrellas."
            }

        titulo = " ".join(str(titulo or "").split())[:120]
        comentario = str(comentario or "").strip()[:1200]

        return self.repository.guardar(
            id_paquete,
            id_cliente,
            id_reserva or None,
            int(calificacion),
            int(calificacion_servicio) if calificacion_servicio not in (None, "") else None,
            titulo,
            comentario,
        )

    def guardar_parcial(
        self,
        id_paquete,
        id_cliente,
        id_reserva,
        calificacion=None,
        calificacion_servicio=None,
        titulo="",
        comentario="",
    ):
        titulo = " ".join(str(titulo or "").split())[:120]
        comentario = str(comentario or "").strip()[:1200]

        if calificacion in (None, ""):
            calificacion = None
        elif not self._calificacion_valida(calificacion):
            return {
                "ok": False,
                "error": "Selecciona una valoración general de 1 a 5 estrellas."
            }
        else:
            calificacion = int(calificacion)

        if calificacion_servicio in (None, ""):
            calificacion_servicio = None
        elif not self._calificacion_valida(calificacion_servicio):
            return {
                "ok": False,
                "error": "Selecciona una valoración del servicio de 1 a 5 estrellas."
            }
        else:
            calificacion_servicio = int(calificacion_servicio)

        if not any((calificacion, calificacion_servicio, titulo, comentario)):
            return {
                "ok": False,
                "error": "Responde al menos una opción de la encuesta."
            }

        return self.repository.guardar(
            id_paquete,
            id_cliente,
            id_reserva or None,
            calificacion,
            calificacion_servicio,
            titulo,
            comentario,
        )

    def ya_reseno_reserva(self, id_reserva):
        return self.repository.ya_reseno_reserva(id_reserva)

    def obtener_por_paquete(self, id_paquete):
        return self.repository.obtener_por_paquete(id_paquete)

    def ya_reseno(self, id_paquete, id_cliente):
        return self.repository.ya_reseno(id_paquete, id_cliente)

    def obtener_encuesta_pendiente(self, id_cliente):
        return self.repository.obtener_encuesta_pendiente(id_cliente)

    def obtener_reserva_valida(self, id_reserva, id_cliente):
        return self.repository.obtener_reserva_valida(id_reserva, id_cliente)
