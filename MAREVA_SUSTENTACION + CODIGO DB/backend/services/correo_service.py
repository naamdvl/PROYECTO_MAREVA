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

        asunto = "Tu código de verificación MAREVA"
        contenido = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">
          <h2 style="color:#0f766e;">Verifica tu correo</h2>
          <p>Recibimos un intento de registro en MAREVA con este correo.</p>
          <p style="font-size:28px;letter-spacing:6px;font-weight:bold;">
            {html.escape(str(codigo))}
          </p>
          <p>Este código vence en 10 minutos. Si no fuiste tú, ignora este mensaje.</p>
          <p style="color:#64748b;font-size:12px;">MAREVA · Viaja con propósito</p>
        </div>
        """
        contenido_texto = f"""MAREVA

Tu código de verificación es: {codigo}

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
