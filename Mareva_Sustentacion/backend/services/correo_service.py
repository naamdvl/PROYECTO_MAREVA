import html
import os
import smtplib

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

load_dotenv()

class CorreoService:
    """Servicio centralizado para enviar correos de MAREVA mediante SMTP."""

    def _configuracion(self):
        correo_emisor = os.getenv("SMTP_USER")
        contrasena = os.getenv("SMTP_PASSWORD")
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        usar_ssl = os.getenv("SMTP_USE_SSL", "").strip().lower() in (
            "1", "true", "yes", "si"
        )

        if not correo_emisor or not contrasena:
            return None

        return {
            "correo_emisor": correo_emisor,
            "contrasena": contrasena,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "usar_ssl": usar_ssl,
            "nombre_emisor": os.getenv("SMTP_FROM_NAME", "MAREVA"),
            "reply_to": os.getenv("SMTP_REPLY_TO", correo_emisor),
        }

    def _construir_mensaje(
        self,
        config,
        asunto,
        contenido_html,
        contenido_texto,
        correo_cliente,
    ):
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = asunto
        mensaje["From"] = formataddr(
            (config["nombre_emisor"], config["correo_emisor"])
        )
        mensaje["To"] = correo_cliente
        mensaje["Reply-To"] = config["reply_to"]
        mensaje["Date"] = formatdate(localtime=True)
        mensaje["Message-ID"] = make_msgid(
            domain=config["correo_emisor"].split("@")[-1]
        )
        mensaje.attach(MIMEText(contenido_texto, "plain", "utf-8"))
        mensaje.attach(MIMEText(contenido_html, "html", "utf-8"))
        return mensaje

    def _enviar(self, config, mensaje, destinatarios):
        destinatarios = list(dict.fromkeys(destinatarios))
        usar_ssl = config["usar_ssl"] or config["smtp_port"] == 465

        if usar_ssl:
            servidor = smtplib.SMTP_SSL(
                config["smtp_host"],
                config["smtp_port"],
                timeout=30,
            )
        else:
            servidor = smtplib.SMTP(
                config["smtp_host"],
                config["smtp_port"],
                timeout=30,
            )

        with servidor:
            servidor.ehlo()
            if not usar_ssl:
                servidor.starttls()
                servidor.ehlo()
            servidor.login(config["correo_emisor"], config["contrasena"])
            rechazados = servidor.sendmail(
                config["correo_emisor"],
                destinatarios,
                mensaje.as_string(),
            )

        if rechazados:
            return {
                "ok": False,
                "error": (
                    "El servidor SMTP rechazó: "
                    + ", ".join(rechazados.keys())
                ),
            }

        return {"ok": True}

    def enviar_codigo_verificacion(self, correo_cliente, codigo):
        config = self._configuracion()

        if not config:
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        asunto = "Confirma tu correo para empezar a viajar con MAREVA"
        codigo_seguro = html.escape(str(codigo))
        contenido = f"""
<div style="margin:0;padding:32px 14px;background:#f3f6fb;font-family:Arial,Helvetica,sans-serif;color:#1e293b;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 18px 45px rgba(15,23,42,.10);">
    <tr>
      <td style="background:linear-gradient(135deg,#1d4ed8,#0f766e);padding:30px 36px;color:#ffffff;">
        <div style="font-size:22px;font-weight:800;letter-spacing:3px;">MAREVA</div>
        <div style="font-size:13px;opacity:.85;margin-top:6px;">Viaja con propósito</div>
      </td>
    </tr>
    <tr>
      <td style="padding:38px 36px 20px;">
        <p style="margin:0 0 12px;font-size:15px;color:#475569;">Hola, viajero:</p>
        <h1 style="margin:0 0 14px;font-size:26px;line-height:1.3;color:#0f172a;">Un último paso antes de despegar</h1>
        <p style="margin:0 0 22px;font-size:15px;line-height:1.65;color:#475569;">Recibimos un intento de registro en MAREVA con este correo. Usa el código siguiente para confirmar tu cuenta y comenzar a descubrir Colombia.</p>
        <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 22px;">
          <tr>
            <td style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;padding:18px 30px;text-align:center;">
              <span style="display:block;font-size:11px;letter-spacing:2px;color:#2563eb;font-weight:700;">TU CÓDIGO DE VERIFICACIÓN</span>
              <span style="display:block;margin-top:8px;font-size:34px;letter-spacing:10px;font-weight:800;color:#1e3a8a;">{codigo_seguro}</span>
            </td>
          </tr>
        </table>
        <p style="margin:0 0 8px;font-size:14px;color:#475569;"><strong>¿Cómo continuar?</strong></p>
        <ol style="margin:0;padding-left:20px;font-size:14px;line-height:1.7;color:#475569;">
          <li>Copia el código en el formulario de registro.</li>
          <li>Pulsa <strong>Verificar código</strong>.</li>
          <li>Completa tus datos y crea tu cuenta.</li>
        </ol>
        <p style="margin:22px 0 0;padding:14px 16px;background:#fff7ed;border-left:4px solid #f97316;border-radius:10px;font-size:13px;line-height:1.6;color:#7c2d12;">Este código vence en <strong>10 minutos</strong> y es de uso único. Si no fuiste tú quien solicitó el registro, ignora este mensaje.</p>
      </td>
    </tr>
    <tr>
      <td style="padding:22px 36px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#64748b;">MAREVA · Viaja con propósito<br>Tu próxima aventura empieza aquí</td>
    </tr>
  </table>
</div>
"""
        contenido_texto = f"""MAREVA · Viaja con propósito

Hola, viajero:

Recibimos un intento de registro en MAREVA con este correo.

Tu código de verificación es: {codigo}

Cómo continuar:
1. Copia el código en el formulario de registro.
2. Pulsa Verificar código.
3. Completa tus datos y crea tu cuenta.

Este código vence en 10 minutos y es de uso único.
Si no fuiste tú quien solicitó el registro, ignora este mensaje.
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )
        destinatarios = [correo_cliente]
        correo_admin = os.getenv("SMTP_ADMIN_EMAIL", "").strip()

        if correo_admin and correo_admin.lower() != correo_cliente.lower():
            destinatarios.append(correo_admin)

        try:
            return self._enviar(config, mensaje, destinatarios)

        except Exception as e:
            return {
                "ok": False,
                "error": f"No fue posible enviar el código ({e})."
            }

    def enviar_confirmacion_cuenta(self, correo_cliente, nombre_cliente):
        config = self._configuracion()

        if not config:
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        nombre = html.escape((nombre_cliente or "viajero").strip())
        asunto = "¡Bienvenido a MAREVA! Tu cuenta está lista"
        contenido = f"""
<div style="margin:0;padding:32px 14px;background:#f3f6fb;font-family:Arial,Helvetica,sans-serif;color:#1e293b;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 18px 45px rgba(15,23,42,.10);">
    <tr>
      <td style="background:linear-gradient(135deg,#1d4ed8,#0f766e);padding:30px 36px;color:#ffffff;">
        <div style="font-size:22px;font-weight:800;letter-spacing:3px;">MAREVA</div>
        <div style="font-size:13px;opacity:.85;margin-top:6px;">Viaja con propósito</div>
      </td>
    </tr>
    <tr>
      <td style="padding:38px 36px 30px;">
        <p style="margin:0 0 12px;font-size:15px;color:#475569;">Hola, {nombre}:</p>
        <h1 style="margin:0 0 14px;font-size:26px;color:#0f172a;">Tu cuenta ya está lista</h1>
        <p style="margin:0 0 22px;font-size:15px;line-height:1.65;color:#475569;">Ya puedes explorar destinos, guardar tus favoritos y preparar tu próxima reserva. Nos alegra tenerte a bordo.</p>
        <table role="presentation" cellpadding="0" cellspacing="0">
          <tr><td style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:14px 22px;font-size:14px;font-weight:700;color:#1d4ed8;">Ya puedes iniciar sesión y empezar a explorar</td></tr>
        </table>
        <p style="margin:24px 0 0;font-size:13px;line-height:1.6;color:#64748b;">Si no creaste esta cuenta, puedes ignorar este mensaje con total seguridad.</p>
      </td>
    </tr>
    <tr>
      <td style="padding:22px 36px;background:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#64748b;">MAREVA · Viaja con propósito</td>
    </tr>
  </table>
</div>
"""
        contenido_texto = f"""MAREVA · Viaja con propósito

Hola, {nombre}:

Tu cuenta ya está lista. Ya puedes explorar destinos, guardar favoritos y preparar tu próxima reserva.

Si no creaste esta cuenta, puedes ignorar este mensaje.
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )

        try:
            return self._enviar(config, mensaje, [correo_cliente])
        except Exception as e:
            return {
                "ok": False,
                "error": f"No fue posible enviar el código ({e})."
            }

    def enviar_encuesta(
        self,
        correo_cliente,
        nombre_cliente,
        id_reserva,
        paquete=None,
    ):
        config = self._configuracion()

        if not config:
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        asunto = "Cuéntanos cómo fue tu viaje con MAREVA"
        nombre = html.escape(str(nombre_cliente or "Viajero"))
        paquete_texto = html.escape(str(paquete or "tu paquete MAREVA"))

        base_url = os.getenv("APP_URL", "").strip().rstrip("/")
        enlace = None

        if base_url:
            enlace = (
                f"{base_url}/?encuesta="
                f"{html.escape(str(id_reserva))}"
            )

        if enlace:
            accion = f"""
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#2b0870;border-radius:12px;">
                  <a href="{enlace}" style="display:inline-block;padding:14px 26px;color:#ffffff;text-decoration:none;font-weight:700;font-size:14px;">
                    Responder encuesta
                  </a>
                </td>
              </tr>
            </table>
            """
        else:
            accion = """
            <table role="presentation" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#f3f0ff;border:1px solid #ddd4ff;border-radius:12px;padding:14px 22px;font-size:14px;font-weight:700;color:#2b0870;">
                  Ingresa a MAREVA y responde la encuesta pendiente
                </td>
              </tr>
            </table>
            """

        contenido = f"""
        <div style="background:#f5f7fb;padding:28px 12px;">
          <div style="max-width:600px;margin:auto;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 18px 45px rgba(32,48,86,.12);">
            <div style="background:linear-gradient(135deg,#2b0870,#4b1696 55%,#2d70d6);padding:28px 32px;color:#ffffff;">
              <p style="margin:0;font-size:12px;letter-spacing:3px;font-weight:800;opacity:.8;">MAREVA · TU OPINIÓN IMPORTA</p>
              <h1 style="margin:8px 0 4px;font-size:26px;">¿Cómo fue tu experiencia?</h1>
              <p style="margin:0;opacity:.9;font-size:14px;">Tu reseña ayuda a otros viajeros a elegir con confianza.</p>
            </div>
            <div style="padding:28px 32px 32px;color:#243049;font-size:15px;line-height:1.65;">
              <p>Hola, <strong>{nombre}</strong>:</p>
              <p>Esperamos que hayas disfrutado <strong>{paquete_texto}</strong>. Ya finalizó tu viaje y nos encantaría conocer tu opinión.</p>
              <p style="text-align:center;color:#f6a04d;font-size:28px;letter-spacing:6px;margin:22px 0 6px;">★★★★★</p>
              <p style="text-align:center;color:#7a8698;font-size:13px;margin-top:0;">Califica el paquete y la atención del servicio en menos de un minuto.</p>
              <div style="margin:26px 0;">{accion}</div>
              <p style="color:#7a8698;font-size:12px;line-height:1.5;">
                Referencia: reserva {html.escape(str(id_reserva))}. Si ya respondiste, puedes ignorar este mensaje.
              </p>
              <hr style="border:0;border-top:1px solid #e6eaf0;margin:26px 0 18px;">
              <p style="color:#94a0b3;font-size:12px;margin:0;">MAREVA · Viaja con propósito</p>
            </div>
          </div>
        </div>
        """

        contenido_texto = f"""Hola, {nombre_cliente or 'Viajero'}:

Ya finalizó tu viaje con MAREVA ({paquete or 'tu paquete'}).

Cuéntanos cómo fue tu experiencia: califica el paquete y la atención del servicio en menos de un minuto.

Referencia: reserva {id_reserva}.
{'Responde aquí: ' + enlace if enlace else 'Ingresa a MAREVA y responde la encuesta pendiente.'}

Si ya respondiste, puedes ignorar este mensaje.

MAREVA · Viaja con propósito
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )

        try:
            return self._enviar(config, mensaje, [correo_cliente])
        except Exception as e:
            print("ERROR ENVIANDO ENCUESTA:", e)
            return {
                "ok": False,
                "error": f"No fue posible enviar la encuesta ({e})."
            }


    def enviar_confirmacion_reserva(self, correo_cliente, nombre_cliente, reserva):
        """
        Envía al cliente la confirmación de una reserva recién creada.

        El envío es independiente de la creación de la reserva:
        si SMTP falla, la reserva no se deshace.
        """
        if not correo_cliente:
            return {
                "ok": False,
                "error": "El cliente no tiene un correo registrado."
            }

        config = self._configuracion()

        if not config:
            print(
                "ERROR: No están configuradas las credenciales del correo "
                "(revisa SMTP_USER / SMTP_PASSWORD en el .env)."
            )
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        codigo = reserva.get("codigo_unico", "N/D")
        paquete = reserva.get("paquete", {})
        paquete_nombre = paquete.get("nombre", "N/D")
        fecha_viaje = reserva.get("fecha_viaje", "N/D")
        fecha_regreso = reserva.get("fecha_regreso", "N/D")
        adultos = reserva.get("cant_adultos", 0)
        menores = reserva.get("cant_menores", 0)
        total_personas = reserva.get("total_personas", adultos + menores)
        valor = reserva.get("valor_referencial", 0)
        plan = reserva.get("plan", "N/D")
        metodo_contacto = reserva.get("metodo_contacto", "N/D")

        desglose = reserva.get("desglose") or {}
        filas_precio = []

        if desglose:
            filas_precio.append(
                "<p><strong>Precio base (por persona):</strong> "
                f"${desglose.get('base_por_persona', 0):,.0f}</p>"
            )
            for item in desglose.get("items", []):
                grupo = html.escape(str(item.get("grupo", "")))
                nombre = html.escape(str(item.get("nombre", "")))
                filas_precio.append(
                    f"<p><strong>{grupo}: {nombre}:</strong> "
                    f"+${item.get('precio', 0):,.0f}</p>"
                )
            filas_precio.append(
                "<p><strong>Adicionales por persona:</strong> "
                f"${desglose.get('adicionales_por_persona', 0):,.0f}</p>"
            )
            filas_precio.append(
                "<p><strong>Precio por persona:</strong> "
                f"${desglose.get('precio_por_persona', 0):,.0f}</p>"
            )
            filas_precio.append(
                "<p><strong>Viajeros:</strong> "
                f"{desglose.get('total_personas', total_personas)}</p>"
            )
            total = desglose.get("total_final", valor)
        else:
            total = valor

        filas_precio.append(
            "<p><strong>Total de la reserva:</strong> "
            f"${total:,.0f}</p>"
        )
        precio_html = "".join(filas_precio)
        filas_precio_texto = []

        if desglose:
            filas_precio_texto.append(
                f"Precio base (por persona): ${desglose.get('base_por_persona', 0):,.0f}"
            )
            for item in desglose.get("items", []):
                filas_precio_texto.append(
                    f"{item.get('grupo', '')}: {item.get('nombre', '')}: "
                    f"+${item.get('precio', 0):,.0f}"
                )
            filas_precio_texto.append(
                "Adicionales por persona: "
                f"${desglose.get('adicionales_por_persona', 0):,.0f}"
            )
            filas_precio_texto.append(
                f"Precio por persona: ${desglose.get('precio_por_persona', 0):,.0f}"
            )
            filas_precio_texto.append(
                "Viajeros: "
                f"{desglose.get('total_personas', total_personas)}"
            )

        filas_precio_texto.append(f"Total de la reserva: ${total:,.0f}")
        precio_texto = "\n".join(filas_precio_texto)

        viajeros_html = ""
        for viajero in reserva.get("viajeros", []):
            viajeros_html += f"""
                <li>
                    {viajero.get("nombre", "")} {viajero.get("apellido", "")}
                    — {viajero.get("tipo_documento", "")}:
                    {viajero.get("numero_documento", "")}
                </li>
            """

        if not viajeros_html:
            viajeros_html = "<li>Información de viajeros registrada en MAREVA.</li>"

        asunto = f"MAREVA - Confirmación de reserva {codigo}"

        contenido = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5;">
                <div style="max-width: 680px; margin: auto;">
                    <h2 style="margin-bottom: 4px;">¡Hola, {nombre_cliente}!</h2>
                    <p>
                        Hemos recibido correctamente tu reserva en <strong>MAREVA</strong>.
                    </p>

                    <div style="padding: 18px; border: 1px solid #ddd; border-radius: 10px;">
                        <h3 style="margin-top: 0;">Resumen de tu reserva</h3>
                        <p><strong>Código:</strong> {codigo}</p>
                        <p><strong>Paquete:</strong> {paquete_nombre}</p>
                        <p><strong>Fecha de viaje:</strong> {fecha_viaje}</p>
                        <p><strong>Fecha de regreso:</strong> {fecha_regreso}</p>
                        <p><strong>Adultos:</strong> {adultos}</p>
                        <p><strong>Menores:</strong> {menores}</p>
                        <p><strong>Total de viajeros:</strong> {total_personas}</p>
                        <p><strong>Plan:</strong> {plan}</p>
                        <p><strong>Método de contacto:</strong> {metodo_contacto}</p>
                        {precio_html}

                        <h4>Viajeros</h4>
                        <ul>
                            {viajeros_html}
                        </ul>
                    </div>

                    <p>
                        Tu reserva ha quedado registrada. Conserva el código
                        <strong>{codigo}</strong> para futuras consultas.
                    </p>

                    <p>
                        Gracias por elegir MAREVA. 🌴
                    </p>
                </div>
            </body>
        </html>
        """

        contenido_texto = f"""Hola, {nombre_cliente}:

Hemos recibido correctamente tu reserva en MAREVA.

Código: {codigo}
Paquete: {paquete_nombre}
Fecha de viaje: {fecha_viaje}
Fecha de regreso: {fecha_regreso}
Adultos: {adultos}
Menores: {menores}
Total de viajeros: {total_personas}
Plan: {plan}
Método de contacto: {metodo_contacto}

{precio_texto}

Conserva el código {codigo} para futuras consultas.

MAREVA · Viaja con propósito
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )

        destinatarios = [correo_cliente]
        correo_admin = os.getenv("SMTP_ADMIN_EMAIL", "").strip()

        if correo_admin and correo_admin.lower() != correo_cliente.lower():
            mensaje["Cc"] = correo_admin
            destinatarios.append(correo_admin)

        try:
            resultado = self._enviar(config, mensaje, destinatarios)

            if resultado["ok"]:
                print(f"Confirmación de reserva enviada a {correo_cliente}")

            return resultado

        except Exception as e:
            print("ERROR ENVIANDO CONFIRMACIÓN DE RESERVA:", e)
            return {
                "ok": False,
                "error": f"No fue posible enviar el correo ({e})."
            }

    def enviar_solicitud_pago(self, correo_cliente, nombre_cliente, datos):
        if not correo_cliente:
            return {
                "ok": False,
                "error": "El cliente no tiene un correo registrado."
            }

        config = self._configuracion()

        if not config:
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        codigo = html.escape(str(datos.get("codigo_unico", "N/D")))
        nombre = html.escape(str(nombre_cliente or "Viajero"))
        monto = float(datos.get("monto", 0) or 0)
        metodo = html.escape(str(datos.get("metodo_nombre", "Pago")))
        detalle = html.escape(str(datos.get("detalle_pagador", "")))
        beneficiario = html.escape(str(datos.get("beneficiario_nombre", "Turismo Mágico")))
        cuenta = html.escape(str(datos.get("beneficiario_cuenta", "")))
        enlace = html.escape(str(datos.get("enlace_aprobacion", "")), quote=True)

        asunto = f"Turismo Mágico - Confirma tu pago {codigo}"

        contenido = f"""
        <html>
            <body style="margin:0;background:#f8f7f4;font-family:Arial,sans-serif;color:#222;">
                <div style="max-width:620px;margin:auto;padding:32px 20px;">
                    <div style="background:#fff;border:1px solid #e8e5df;border-radius:18px;padding:30px;">
                        <span style="display:inline-block;margin-bottom:10px;color:#0f766e;font-size:11px;font-weight:bold;letter-spacing:2px;">
                            TURISMO MÁGICO · PAGO SEGURO
                        </span>
                        <h2 style="margin:0 0 16px;font-size:26px;">Hola, {nombre}</h2>
                        <p style="color:#555;line-height:1.6;">
                            Recibimos una solicitud para procesar el pago de tu reserva
                            <strong>{codigo}</strong> con <strong>{metodo}</strong>.
                        </p>
                        <div style="margin:22px 0;padding:18px;background:#f8f7f4;border-radius:12px;">
                            <p style="margin:0 0 8px;"><strong>Detalle:</strong> {detalle}</p>
                            <p style="margin:0 0 8px;"><strong>Valor a pagar:</strong> ${monto:,.0f}</p>
                            <p style="margin:0;"><strong>Beneficiario:</strong> {beneficiario}</p>
                            <p style="margin:0;"><strong>Cuenta:</strong> {cuenta}</p>
                        </div>
                        <p style="color:#555;line-height:1.6;">
                            Revisa los datos y confirma que fuiste tú. Al aprobar, el pago quedará
                            registrado y tu reserva se marcará como <strong>Pagada</strong>.
                        </p>
                        <p style="text-align:center;margin:28px 0;">
                            <a href="{enlace}" style="display:inline-block;background:#2b0870;color:#fff;text-decoration:none;padding:14px 24px;border-radius:10px;font-weight:bold;">
                                Realizar pago
                            </a>
                        </p>
                        <p style="color:#7a8698;font-size:12px;line-height:1.5;">
                            Si no reconoces esta solicitud, ignora este correo. El enlace vence en 60 minutos.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        contenido_texto = f"""Hola, {nombre_cliente or 'Viajero'}:

Recibimos una solicitud para procesar el pago de tu reserva {codigo}
con {metodo}.

Detalle: {datos.get('detalle_pagador', '')}
Valor a pagar: ${monto:,.0f}
Beneficiario: {beneficiario}
Cuenta: {cuenta}

Revisa los datos y confirma que fuiste tú:
{datos.get('enlace_aprobacion', '')}

Al aprobar, el pago quedará registrado y tu reserva se marcará como Pagada.
Si no reconoces esta solicitud, ignora este correo. El enlace vence en 60 minutos.

MAREVA · Viaja con propósito
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )
        destinatarios = [correo_cliente]
        correo_admin = os.getenv("SMTP_ADMIN_EMAIL", "").strip()

        if correo_admin and correo_admin.lower() != correo_cliente.lower():
            destinatarios.append(correo_admin)

        try:
            return self._enviar(config, mensaje, destinatarios)

        except Exception as e:
            print("ERROR ENVIANDO SOLICITUD DE PAGO:", e)
            return {
                "ok": False,
                "error": f"No fue posible enviar el correo ({e})."
            }

    def enviar_codigo_recuperacion(self, correo_cliente, codigo):
        config = self._configuracion()

        if not config:
            return {
                "ok": False,
                "error": "No está configurado el servicio de correo."
            }

        asunto = "Recupera tu contraseña MAREVA"
        contenido = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">
          <h2 style="color:#0f766e;">Recupera tu contraseña</h2>
          <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta MAREVA.</p>
          <p style="font-size:28px;letter-spacing:6px;font-weight:bold;">
            {html.escape(str(codigo))}
          </p>
          <p>Este código vence en 10 minutos. Si no fuiste tú, ignora este mensaje.</p>
          <p style="color:#64748b;font-size:12px;">MAREVA · Viaja con propósito</p>
        </div>
        """
        contenido_texto = f"""MAREVA

Recibimos una solicitud para restablecer tu contraseña.

Tu código de recuperación es: {codigo}

Vence en 10 minutos. Si no fuiste tú, ignora este mensaje.

MAREVA · Viaja con propósito
"""
        mensaje = self._construir_mensaje(
            config,
            asunto,
            contenido,
            contenido_texto,
            correo_cliente,
        )
        destinatarios = [correo_cliente]
        correo_admin = os.getenv("SMTP_ADMIN_EMAIL", "").strip()

        if correo_admin and correo_admin.lower() != correo_cliente.lower():
            destinatarios.append(correo_admin)

        try:
            return self._enviar(config, mensaje, destinatarios)

        except Exception as e:
            return {
                "ok": False,
                "error": f"No fue posible enviar el código ({e})."
            }
