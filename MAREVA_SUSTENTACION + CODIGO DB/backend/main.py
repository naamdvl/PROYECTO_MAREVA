from flask import Flask, redirect, request, session, url_for

from routes.auth_routes import auth_bp
from routes.home_routes import home_bp
from routes.paquetes_routes import paquetes_bp
from routes.reserva_routes import reserva_bp
from routes.destino_routes import destinos_bp
from routes.encuesta_routes import encuesta_bp
from routes.favoritos_routes import favoritos_bp
from routes.gamificacion_routes import gamificacion_bp
from routes.guia_routes import guia_bp
from routes.proveedores_routes import proveedor_bp
from routes.reporte_routes import reporte_bp
from routes.dashboard_routes import dashboard_bp

from datetime import timedelta

import os
import time
from dotenv import load_dotenv

from services.resena_services import ResenaService
from services.reserva_services import ReservaService

load_dotenv()

main = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

main.secret_key = "mareva_secret_2026"

# Evita que Flask sirva una versión antigua de las plantillas después de
# editarlas mientras el servidor corre con debug=False.
main.config["TEMPLATES_AUTO_RELOAD"] = True

main.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID","").strip()

main.register_blueprint(proveedor_bp)
main.register_blueprint(guia_bp)
main.register_blueprint(gamificacion_bp)
main.register_blueprint(favoritos_bp)
main.register_blueprint(encuesta_bp)
main.register_blueprint(reserva_bp)
main.register_blueprint(paquetes_bp)
main.register_blueprint(auth_bp)
main.register_blueprint(destinos_bp)
main.register_blueprint(home_bp)
main.register_blueprint(reporte_bp)
main.register_blueprint(dashboard_bp)
main.permanent_session_lifetime = timedelta(days=30) 

# Un administrador solo gestiona la plataforma: no accede a catálogos,
# reservas, pagos ni al resto de flujos de un cliente.
ENDPOINTS_ADMIN = {
    "static",
    "home.logout",
    "auth.google_callback",
    "dashboard.mostrar_panel",
    "dashboard.obtener_metricas",
    "dashboard.obtener_alertas_reservas",
    "dashboard.obtener_alertas_paquetes",
    "dashboard.obtener_niveles",
    "dashboard.obtener_panel_completo",
    "paquetes.panel_admin",
    "paquetes.mostrar_form_crear",
    "paquetes.crear",
    "paquetes.mostrar_form_editar",
    "paquetes.actualizar",
    "paquetes.suspender",
    "paquetes.cancelar_por_contingencia",
    "paquetes.activar",
    "destinos.panel_admin",
    "destinos.mostrar_form_crear",
    "destinos.crear",
    "destinos.mostrar_form_editar",
    "destinos.actualizar",
    "destinos.suspender",
    "destinos.activar",
    "gamificacion.admin_niveles",
    "gamificacion.crear_nivel",
    "gamificacion.actualizar_nivel",
    "proveedor.mostrar_registro",
    "proveedor.registrar_proveedor",
    "reserva.listar_reservas_admin",
    "reserva.completar_reserva",
    "reserva.marcar_reembolso",
    "encuesta.reporte",
    "encuesta.panel_preguntas",
    "encuesta.nueva_pregunta",
    "encuesta.crear_pregunta",
    "encuesta.editar_pregunta",
    "encuesta.actualizar_pregunta",
    "encuesta.cambiar_estado_pregunta",
    "encuesta.guardar_encuesta",
}


@main.context_processor
def encuesta_pendiente_contexto():
    usuario = session.get("usuario") or {}

    if usuario.get("rol") != "cliente":
        return {"encuesta_pendiente": None}

    try:
        encuesta = ResenaService().obtener_encuesta_pendiente(usuario["id"])
    except Exception as error:
        print("ERROR CARGANDO ENCUESTA PENDIENTE:", error)
        encuesta = None

    if encuesta and session.get("encuesta_descartada") == encuesta["id_reserva"]:
        encuesta = None

    return {"encuesta_pendiente": encuesta}


ULTIMA_FINALIZACION = 0.0
INTERVALO_FINALIZACION = 300


@main.before_request
def finalizar_viajes_automaticamente():
    global ULTIMA_FINALIZACION

    if request.endpoint == "static":
        return None

    ahora = time.monotonic()

    if ahora - ULTIMA_FINALIZACION < INTERVALO_FINALIZACION:
        return None

    ULTIMA_FINALIZACION = ahora

    try:
        ReservaService().finalizar_viajes_pasados()
    except Exception as error:
        print("ERROR FINALIZANDO VIAJES AUTOMÁTICAMENTE:", error)

    return None


@main.before_request
def solo_administrar():
    """Bloquea a los administradores de los flujos de compra/cliente."""
    usuario = session.get("usuario")

    if not usuario or usuario.get("rol") != "admin":
        return None

    endpoint = request.endpoint or ""

    if endpoint in ENDPOINTS_ADMIN or endpoint.startswith("reporte."):
        return None

    return redirect(url_for("dashboard.mostrar_panel"))

if __name__ == "__main__":
    main.run(debug=True, use_reloader=False)
