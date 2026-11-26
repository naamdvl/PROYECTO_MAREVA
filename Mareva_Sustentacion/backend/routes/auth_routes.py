from flask import Blueprint, render_template, request, jsonify
from controllers.auth_controllers import AuthController

auth_bp = Blueprint('auth', __name__)

controller = AuthController()

#Muestra el formulario de registro
@auth_bp.route("/registro", methods=["GET"])
def mostrar_registro():
    print("Se accedio al GET del registro correcamente")
    return controller.mostrar_registro(
        next_url=request.args.get("next")
    )

#Maneja el registro de un nuevo usuario
@auth_bp.route("/registro", methods=["POST"])
def funcion_registro():
    print("Se accedio al POST del registro correctamente")
    print("DATOS RECIBIDOS:", request.form)
    return controller.registrar_usuario()

#Muestra el formulario de login
@auth_bp.route("/login", methods=["GET"])
def mostrar_login():
    print("Se accedio al GET del login correctamente")
    return render_template(
        "principal/login.html",
        next=request.args.get("next", "")
    )

#Maneja el inicio de sesión de un usuario
@auth_bp.route("/login", methods=["POST"])
def funcion_login():
    print("Se accedio al POST del login correctamente")
    return controller.iniciar_sesion()

@auth_bp.route("/auth/google", methods=["GET"])
def google_login():
    return controller.iniciar_sesion_google()


@auth_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    return controller.google_callback()

@auth_bp.route("/auth/google/registro", methods=["GET"])
def google_registro():
    return controller.iniciar_sesion_google(intencion="registro")


@auth_bp.route("/auth/verificar-correo/enviar", methods=["POST"])
def enviar_codigo_correo():
    respuesta, estado = controller.enviar_codigo_correo()
    return jsonify(respuesta), estado


@auth_bp.route("/auth/verificar-correo/confirmar", methods=["POST"])
def confirmar_codigo_correo():
    respuesta, estado = controller.verificar_codigo_correo()
    return jsonify(respuesta), estado


@auth_bp.route("/olvide-mi-contrasena", methods=["GET"])
def mostrar_recuperacion():
    return controller.mostrar_recuperacion()


@auth_bp.route("/olvide-mi-contrasena", methods=["POST"])
def enviar_recuperacion():
    return controller.enviar_recuperacion()


@auth_bp.route("/olvide-mi-contrasena/verificar", methods=["POST"])
def verificar_recuperacion():
    return controller.verificar_recuperacion()


@auth_bp.route("/olvide-mi-contrasena/cambiar", methods=["POST"])
def cambiar_password_recuperado():
    return controller.cambiar_password_recuperado()

