from repositories.encuesta_repository import EncuestaRepository
from repositories.resena_repository import ResenaRepository
from repositories.reserva_repository import ReservaRepository
from services.correo_service import CorreoService
from services.resena_services import ResenaService

class EncuestaService:

    def __init__(self):
        self.encuesta_repo = EncuestaRepository()
        self.resena_repo = ResenaRepository()
        self.resena_service = ResenaService()
        self.reserva_repo = ReservaRepository()
        self.correo_service = CorreoService()

    def enviar_encuesta(
        self,
        correo_cliente,
        nombre_cliente,
        id_reserva,
        paquete=None,
    ):
        return self.correo_service.enviar_encuesta(
            correo_cliente,
            nombre_cliente,
            id_reserva,
            paquete,
        )

    def guardar_encuesta_rapida(
        self,
        id_reserva,
        id_cliente,
        datos,
    ):
        reserva = self.resena_repo.obtener_reserva_valida(
            id_reserva,
            id_cliente,
        )

        if not reserva:
            return {
                "ok": False,
                "error": (
                    "La encuesta no está disponible para esta reserva."
                ),
            }

        if (
            self.resena_repo.ya_reseno_reserva(id_reserva)
            or self.encuesta_repo.ya_respondida(id_reserva)
        ):
            return {
                "ok": True,
                "mensaje": "Ya respondiste esta encuesta. ¡Gracias!",
                "duplicado": True,
            }

        return self.resena_service.guardar_parcial(
            reserva["id_paquete"],
            id_cliente,
            id_reserva,
            datos.get("calificacion"),
            datos.get("calificacion_servicio") or None,
            datos.get("titulo", ""),
            datos.get("comentario", ""),
        )

    def obtener_encuesta(self, id_reserva, id_cliente):

        reserva = self.encuesta_repo.verificar_reserva_cliente(
            id_reserva,
            id_cliente
        )

        if not reserva:
            return {
                "ok": False,
                "error": "La reserva no existe o no pertenece al usuario."
            }

        if reserva["estado"] != "completada":
            return {
                "ok": False,
                "error": "La encuesta estará disponible cuando el viaje haya sido completado."
            }

        if (
            self.resena_repo.ya_reseno_reserva(id_reserva)
            or self.encuesta_repo.ya_respondida(id_reserva)
        ):
            return {
                "ok": False,
                "error": "Ya respondiste la encuesta de esta reserva. ¡Gracias!"
            }

        preguntas = self.encuesta_repo.obtener_preguntas_activas()

        if not preguntas:
            return {
                "ok": False,
                "error": "Actualmente no hay preguntas disponibles para la encuesta."
            }

        return {
            "ok": True,
            "reserva": reserva,
            "preguntas": preguntas
        }

    def guardar_encuesta(
        self,
        id_cliente,
        id_reserva,
        respuestas
    ):

        if not id_cliente or not id_reserva:
            return {
                "ok": False,
                "error": "No se pudo identificar al cliente o la reserva."
            }

        if not respuestas:
            return {
                "ok": False,
                "error": "Responde al menos una pregunta de la encuesta."
            }

        reserva = self.encuesta_repo.verificar_reserva_cliente(
            id_reserva=id_reserva,
            id_cliente=id_cliente
        )

        if not reserva:
            return {
                "ok": False,
                "error": "La reserva no existe o no te pertenece."
            }

        if (
            self.resena_repo.ya_reseno_reserva(id_reserva)
            or self.encuesta_repo.ya_respondida(id_reserva)
        ):
            return {
                "ok": False,
                "error": "Ya respondiste la encuesta de esta reserva. ¡Gracias!"
            }

        preguntas = self.encuesta_repo.obtener_todas_preguntas()

        if not preguntas:
            return {
                "ok": False,
                "error": "No hay preguntas disponibles."
            }

        preguntas_dict = {
            pregunta["id_pregunta"]: pregunta
            for pregunta in preguntas
        }

        respuestas_dict = {}

        for respuesta in respuestas:
            id_pregunta = respuesta["id_pregunta"]

            # No aceptar preguntas inexistentes ni duplicadas.
            if id_pregunta not in preguntas_dict:
                return {
                    "ok": False,
                    "error": "Se recibió una pregunta no válida."
                }

            if id_pregunta in respuestas_dict:
                return {
                    "ok": False,
                    "error": "Se recibió una respuesta duplicada."
                }

            respuestas_dict[id_pregunta] = respuesta["valor"]

        respuestas_procesadas = []

        for id_pregunta, valor in respuestas_dict.items():

            pregunta = preguntas_dict[id_pregunta]

            tipo = (
                pregunta.get("tipo_respuesta") or ""
            ).strip().lower()

            valor = str(valor).strip()

            if not valor:
                return {
                    "ok": False,
                    "error": "Las respuestas no pueden estar vacías."
                }

            if tipo in (
                "numero",
                "rating",
                "calificacion"
            ):
                try:
                    numero = int(valor)

                except (ValueError, TypeError):
                    return {
                        "ok": False,
                        "error": (
                            f"La pregunta {id_pregunta} "
                            "requiere una calificación numérica."
                        )
                    }

                # El HTML presenta opciones del 1 al 5.
                if numero < 1 or numero > 5:
                    return {
                        "ok": False,
                        "error": "Las calificaciones deben estar entre 1 y 5."
                    }

                respuestas_procesadas.append({
                    "id_pregunta": id_pregunta,
                    "respuesta_texto": None,
                    "respuesta_numero": numero
                })

            else:
                respuestas_procesadas.append({
                    "id_pregunta": id_pregunta,
                    "respuesta_texto": valor,
                    "respuesta_numero": None
                })

        guardado = self.encuesta_repo.guardar_respuestas(
            id_cliente=id_cliente,
            id_reserva=id_reserva,
            respuestas=respuestas_procesadas
        )

        if not guardado:
            return {
                "ok": False,
                "error": (
                    "No fue posible guardar la encuesta. "
                    "Verifica si ya fue respondida e inténtalo nuevamente."
                )
            }

        return {
            "ok": True,
            "mensaje": "Encuesta guardada correctamente."
        }

    def obtener_preguntas_admin(self):
        return self.encuesta_repo.obtener_todas_preguntas()


    def obtener_pregunta(self, id_pregunta):
        return self.encuesta_repo.obtener_pregunta(id_pregunta)


    def crear_pregunta(self, texto, tipo_respuesta, orden):

        texto = texto.strip()

        if not texto:
            return {
                "ok": False,
                "error": "El texto de la pregunta es obligatorio."
            }

        if tipo_respuesta not in ("numero", "texto", "opcion"):
            return {
                "ok": False,
                "error": "El tipo de respuesta no es válido."
            }

        if orden < 1:
            return {
                "ok": False,
                "error": "El orden debe ser mayor a 0."
            }

        return self.encuesta_repo.crear_pregunta(
            texto,
            tipo_respuesta,
            orden
        )


    def actualizar_pregunta(
        self,
        id_pregunta,
        texto,
        tipo_respuesta,
        orden
    ):

        texto = texto.strip()

        if not texto:
            return {
                "ok": False,
                "error": "El texto de la pregunta es obligatorio."
            }

        if tipo_respuesta not in ("numero", "texto", "opcion"):
            return {
                "ok": False,
                "error": "El tipo de respuesta no es válido."
            }

        if orden < 1:
            return {
                "ok": False,
                "error": "El orden debe ser mayor a 0."
            }

        return self.encuesta_repo.actualizar_pregunta(
            id_pregunta,
            texto,
            tipo_respuesta,
            orden
        )


    def cambiar_estado_pregunta(self, id_pregunta):
        return self.encuesta_repo.cambiar_estado_pregunta(id_pregunta)

    def obtener_datos_reporte(self):
        return {
            "paquetes": self.encuesta_repo.obtener_paquetes_reporte(),
            "destinos": self.encuesta_repo.obtener_destinos_reporte()
        }

    def obtener_reporte(
        self,
        id_paquete=None,
        id_destino=None,
        fecha_inicio=None,
        fecha_fin=None
    ):
        return self.encuesta_repo.obtener_reporte_encuestas(
            id_paquete=id_paquete,
            id_destino=id_destino,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )