from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
import re
import datetime

from services.reserva_services import ReservaService
from services.paquete_services import PaqueteService
from services.pdf_services import PDFService
from repositories.salida_repository import SalidaRepository
from services.correo_service import CorreoService
from services.pago_service import (
    BENEFICIARIO_CUENTA,
    BENEFICIARIO_NOMBRE,
    PSE_BANCOS,
    TIPOS_DOCUMENTO,
    TIPOS_TARJETA,
    crear_token,
    leer_token,
)


METODOS_PAGO = {
    "nequi": "Nequi",
    "pse": "PSE",
    "tarjeta": "Tarjeta de crédito/débito",
}


class ReservaController:

    def __init__(self):

        self.service = ReservaService()

        self.paquete_service = PaqueteService()

        self.pdf_service = PDFService()

        self.salida_repository = SalidaRepository()

        self.correo_service = CorreoService()

    @staticmethod
    def _es_admin():
        usuario = session.get("usuario")
        return bool(usuario and usuario.get("rol") == "admin")

    @staticmethod
    def _texto_fecha(valor):
        """Devuelve la fecha en dd/mm/yyyy aunque venga como date o como texto."""
        if hasattr(valor, "strftime"):
            return valor.strftime("%d/%m/%Y")
        texto = str(valor or "")
        try:
            return datetime.date.fromisoformat(texto).strftime("%d/%m/%Y")
        except ValueError:
            return texto

    @staticmethod
    def _es_destino_amazonas(paquete):
        texto = " ".join(
            str(paquete.get(clave) or "")
            for clave in ("nombre", "slug")
        ).lower()
        return "amazonas" in texto or "leticia" in texto

    @staticmethod
    def _categoria_viajero(indice, adultos, menores):
        if indice < adultos:
            return "adulto"
        if indice < adultos + menores:
            return "menor"
        return "bebe"

    @staticmethod
    def _tipos_documento_permitidos(categoria):
        if categoria == "adulto":
            return ("CC", "CE", "Pasaporte")
        if categoria == "menor":
            return ("TI", "RC", "Pasaporte")
        return ("RC", "Pasaporte")

    @staticmethod
    def _documento_valido(tipo, documento):
        valor = str(documento or "").strip()
        if tipo == "CC" or tipo == "TI":
            return bool(re.fullmatch(r"\d{6,12}", valor))
        if tipo == "CE":
            return bool(re.fullmatch(r"[A-Za-z0-9]{6,12}", valor))
        if tipo == "RC":
            return bool(re.fullmatch(r"[A-Za-z0-9-]{5,15}", valor))
        if tipo == "Pasaporte":
            return bool(re.fullmatch(r"[A-Za-z0-9]{5,20}", valor))
        return False

    def _render_pago(
        self,
        reserva,
        paquete,
        error=None,
        valores=None,
        monto=0
    ):
        return render_template(
            "cliente/pago.html",
            reserva=reserva,
            paquete=paquete,
            error=error,
            valores=valores or {},
            monto=monto,
            bancos=PSE_BANCOS,
            tipos_documento=TIPOS_DOCUMENTO,
            tipos_tarjeta=TIPOS_TARJETA,
            beneficiario_nombre=BENEFICIARIO_NOMBRE,
            beneficiario_cuenta=BENEFICIARIO_CUENTA,
        )

    # =========================================================
    # LISTAR RESERVAS ADMIN
    # =========================================================

    def listar_reservas_admin(self):
        if not self._es_admin():
            return redirect(url_for("auth.mostrar_login"))

        try:
            reservas = self.service.listar_reservas_admin()
            return render_template(
                "admin/reservas.html",
                reservas=reservas,
                error=None
            )
        except Exception as e:
            print("ERROR LISTAR RESERVAS ADMIN:", e)
            return render_template(
                "admin/reservas.html",
                reservas=[],
                error="No fue posible cargar las reservas."
            )


    # =========================================================
    # COMPLETAR RESERVA (PANEL ADMIN)
    # =========================================================

    def completar_reserva(self, id_reserva):
        if not self._es_admin():
            return redirect(url_for("auth.mostrar_login"))

        try:

            resultado = self.service.completar_reserva(id_reserva)

            if resultado.get("ok"):
                mensaje = "Reserva completada y encuesta enviada."
                if not resultado.get("encuesta_enviada"):
                    mensaje = (
                        "Reserva completada. No se pudo enviar la encuesta."
                    )
                categoria = "success"
            else:
                mensaje = resultado.get(
                    "error",
                    "No fue posible completar la reserva."
                )
                categoria = "error"

        except Exception as e:
            print("ERROR COMPLETANDO RESERVA (ADMIN):", e)
            mensaje = "No fue posible completar la reserva."
            categoria = "error"

        flash(mensaje, categoria)

        return redirect(url_for("reserva.listar_reservas_admin"))


    # =========================================================
    # MARCAR REEMBOLSO (PANEL ADMIN)
    # =========================================================

    def marcar_reembolso(self, id_reserva):
        if not self._es_admin():
            return redirect(url_for("auth.mostrar_login"))

        try:

            realizado = self.service.marcar_reembolso_realizado(
                id_reserva
            )

            if realizado:
                mensaje = "Reembolso marcado como realizado."
                categoria = "success"
            else:
                mensaje = (
                    "No se pudo marcar el reembolso. "
                    "Verifica que la reserva esté cancelada y "
                    "el reembolso pendiente."
                )
                categoria = "error"

        except Exception as e:
            print("ERROR MARCANDO REEMBOLSO:", e)
            mensaje = "No se pudo registrar el reembolso."
            categoria = "error"

        flash(mensaje, categoria)

        return redirect(url_for("reserva.listar_reservas_admin"))


    # =========================================================
    # PREPARAR RESERVA (desde el reserva del paquete)
    # =========================================================

    def preparar_reserva(self, slug):

        paquete = self.paquete_service.obtener_detalle(slug)

        if not paquete:
            return redirect(url_for("paquetes.listar_catalogo"))

        id_salida = request.form.get("id_salida", "").strip()

        if not id_salida:
            return redirect(
                url_for(
                    "paquetes.ver_detalle",
                    slug=slug,
                    error="Debes seleccionar una fecha de salida."
                )
            )

        try:
            id_salida = int(id_salida)
        except (ValueError, TypeError):
            return redirect(
                url_for(
                    "paquetes.ver_detalle",
                    slug=slug,
                    error="La fecha seleccionada no es válida."
                )
            )

        salida = self.salida_repository.obtener_por_id(id_salida)

        if (
            not salida
            or salida["id_paquete"] != paquete["id_paquete"]
            or salida["estado"] not in ("programada", "disponible")
        ):
            return redirect(
                url_for(
                    "paquetes.ver_detalle",
                    slug=slug,
                    error="La fecha seleccionada ya no está disponible."
                )
            )

        def _ids(campo):
            resultado = []
            for valor in request.form.getlist(campo):
                try:
                    resultado.append(int(valor))
                except (ValueError, TypeError):
                    continue
            return resultado

        ids_seguros = set(_ids("seguros"))

        for seguro in paquete.get("seguros", []):
            if seguro.get("es_obligatorio"):
                ids_seguros.add(seguro.get("id_seguro"))

        # El selector libre envía el rango elegido en campos ocultos. Se
        # guarda en la sesión para que el resumen y la confirmación muestren
        # exactamente las fechas elegidas, sin alterar la validación de la
        # salida ni la grabación de la reserva.
        fecha_viaje = self._texto_fecha(salida["fecha_salida"])
        fecha_regreso = self._texto_fecha(salida["fecha_regreso"])
        fecha_salida_cruda = getattr(
            salida["fecha_salida"],
            "isoformat",
            lambda: str(salida["fecha_salida"])
        )()
        fecha_regreso_cruda = getattr(
            salida["fecha_regreso"],
            "isoformat",
            lambda: str(salida["fecha_regreso"])
        )()

        for nombre, clave in (
            ("fecha_salida", "fecha_viaje"),
            ("fecha_regreso", "fecha_regreso"),
        ):
            valor = request.form.get(nombre, "").strip()
            if valor:
                try:
                    fecha_elegida = datetime.date.fromisoformat(valor)
                except ValueError:
                    continue
                if clave == "fecha_viaje":
                    fecha_viaje = self._texto_fecha(fecha_elegida)
                    fecha_salida_cruda = valor
                else:
                    fecha_regreso = self._texto_fecha(fecha_elegida)
                    fecha_regreso_cruda = valor

        try:
            dias = paquete.get("duracion_dias")
            noches_paquete = paquete.get("duracion_noches")
            noches_esperadas = int(
                noches_paquete
                if noches_paquete not in (None, "", 0)
                else max(int(dias or 1) - 1, 1)
            )
            inicio = datetime.date.fromisoformat(fecha_salida_cruda)
            fin = datetime.date.fromisoformat(fecha_regreso_cruda)

            if (fin - inicio).days != noches_esperadas:
                return redirect(
                    url_for(
                        "paquetes.ver_detalle",
                        slug=slug,
                        error=(
                            f"Este paquete dura exactamente "
                            f"{noches_esperadas} "
                            f"{'noche' if noches_esperadas == 1 else 'noches'}. "
                            "Selecciona el regreso correspondiente."
                        )
                    )
                )
        except (TypeError, ValueError):
            pass

        seleccion = {
            "slug": slug,
            "id_salida": id_salida,
            "fecha_viaje": fecha_viaje,
            "fecha_regreso": fecha_regreso,
            "alojamiento": _ids("alojamiento"),
            "alimentacion": _ids("alimentacion"),
            "transporte": _ids("transporte"),
            "actividades": _ids("actividades"),
            "seguros": sorted(ids_seguros),
            "extras": _ids("extras"),
        }

        # Viajeros e indicaciones capturados en el detalle. Se guardan en la
        # misma sesión para que la confirmación llegue diligenciada; se usan
        # los nombres de campo que guardar_reserva ya entiende (arrays
        # paralelos), sin crear campos ni endpoints nuevos.
        def _cantidad(campo, defecto, minimo, maximo):
            try:
                return min(maximo, max(minimo, int(request.form.get(campo, defecto))))
            except (ValueError, TypeError):
                return defecto

        adultos = _cantidad("adultos", 1, 1, 20)
        menores = _cantidad("menores", 0, 0, 20)
        bebes = _cantidad("bebes", 0, 0, 10)

        if self._es_destino_amazonas(paquete) and bebes:
            return redirect(
                url_for(
                    "paquetes.ver_detalle",
                    slug=slug,
                    error=(
                        "En Amazonas no se permiten bebés. "
                        "Retira los bebés para continuar."
                    )
                )
            )

        total_personas = adultos + menores + bebes

        def _lista(campo):
            return [valor.strip() for valor in request.form.getlist(campo)]

        nombres = _lista("viajero_nombre[]")
        apellidos = _lista("viajero_apellido[]")
        tipos = _lista("viajero_tipo_documento[]")
        documentos = _lista("viajero_documento[]")
        idiomas = _lista("viajero_idioma[]")
        edades = _lista("viajero_edad[]")
        meses = _lista("viajero_meses[]")
        necesidades = _lista("viajero_necesidades[]")

        def _valor(lista, indice):
            return lista[indice] if indice < len(lista) else ""

        viajeros = []
        for indice in range(total_personas):
            categoria = self._categoria_viajero(indice, adultos, menores)
            tipo = _valor(tipos, indice)
            numero = _valor(documentos, indice)
            permitidos = self._tipos_documento_permitidos(categoria)

            if tipo and tipo not in permitidos:
                return redirect(
                    url_for(
                        "paquetes.ver_detalle",
                        slug=slug,
                        error=(
                            f"El viajero {indice + 1} es {categoria} y debe "
                            f"usar {' o '.join(permitidos)}."
                        )
                    )
                )

            if numero and not self._documento_valido(tipo, numero):
                return redirect(
                    url_for(
                        "paquetes.ver_detalle",
                        slug=slug,
                        error=(
                            f"El documento del viajero {indice + 1} "
                            "no tiene un formato válido."
                        )
                    )
                )

            edad = _valor(edades, indice)
            edad_meses = _valor(meses, indice)

            if categoria == "menor" and edad:
                try:
                    anios = int(edad)
                except (TypeError, ValueError):
                    anios = -1
                if anios < 2 or anios > 17:
                    return redirect(
                        url_for(
                            "paquetes.ver_detalle",
                            slug=slug,
                            error=(
                                "Los niños van de 2 a 17 años; "
                                "desde 24 meses dejan de ser bebés."
                            )
                        )
                    )

            if categoria == "bebe" and edad_meses:
                try:
                    edad_meses_numero = int(edad_meses)
                except (TypeError, ValueError):
                    edad_meses_numero = -1
                if edad_meses_numero < 0 or edad_meses_numero > 23:
                    return redirect(
                        url_for(
                            "paquetes.ver_detalle",
                            slug=slug,
                            error=(
                                "Desde los 24 meses deja de ser bebé: "
                                "cambia a niño o corrige los meses (0 a 23)."
                            )
                        )
                    )

            viajeros.append({
                "nombre": _valor(nombres, indice),
                "apellido": _valor(apellidos, indice),
                "categoria": categoria,
                "tipo_documento": tipo,
                "numero_documento": numero,
                "idioma": _valor(idiomas, indice) or "Español",
                "edad": _valor(edades, indice),
                "meses": _valor(meses, indice),
                "necesidades": _valor(necesidades, indice),
            })

        seleccion.update({
            "adultos": adultos,
            "menores": menores,
            "bebes": bebes,
            "destino_amazonas": self._es_destino_amazonas(paquete),
            "mascotas": request.form.get("mascotas", "no").strip().lower() == "si",
            "mascotas_cantidad": request.form.get("mascotas_cantidad", "").strip(),
            "mascotas_tipo": request.form.get("mascotas_tipo", "").strip(),
            "alergias": request.form.get("alergias", "").strip(),
            "observaciones": request.form.get("observaciones", "").strip(),
            "acepta_no_reembolso": request.form.get("acepta_no_reembolso") == "1",
            "viajeros": viajeros,
        })

        session["seleccion_reserva"] = seleccion

        if not session.get("usuario"):
            session["reserva_pendiente_url"] = url_for(
                "reserva.confirmar_reserva", slug=slug
            )
            return redirect(
                url_for(
                    "auth.mostrar_login",
                    next=session["reserva_pendiente_url"]
                )
            )

        return redirect(
            url_for("reserva.confirmar_reserva", slug=slug)
        )


    # =========================================================
    # MOSTRAR FORMULARIO
    # =========================================================

    def mostrar_formulario(
        self,
        slug
    ):

        paquete = (
            self.paquete_service.obtener_detalle(
                slug
            )
        )


        if not paquete:

            return redirect(
                url_for(
                    "paquetes.listar_catalogo"
                )
            )


        salidas = (
            self.salida_repository.obtener_por_paquete(
                paquete["id_paquete"],
                solo_disponibles=True
            )
        )


        return render_template(
            "cliente/reserva.html",
            paquete=paquete,
            salidas=salidas
        )


    # =========================================================
    # CONFIRMAR RESERVA
    # =========================================================

    def confirmar(
        self,
        slug
    ):      
        print("========== ENTRÓ A ReservaController.confirmar ==========", flush=True)

        usuario = session.get("usuario")


        if not usuario:

            return redirect(
                url_for(
                    "auth.mostrar_login",
                    next=f"/reserva/{slug}"
                )
            )


        paquete = (
            self.paquete_service.obtener_detalle(
                slug
            )
        )


        if not paquete:

            return redirect(
                url_for(
                    "paquetes.listar_catalogo"
                )
            )


        # -----------------------------------------------------
        # SALIDA SELECCIONADA
        # -----------------------------------------------------

        id_salida = (
            request.form
            .get("id_salida", "")
            .strip()
        )


        if not id_salida:

            salidas = (
                self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                )
            )


            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=salidas,
                error=(
                    "Debes seleccionar una fecha "
                    "de salida."
                )
            )


        try:

            id_salida = int(id_salida)

        except (
            ValueError,
            TypeError
        ):

            salidas = (
                self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                )
            )


            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=salidas,
                error=(
                    "La fecha seleccionada "
                    "no es válida."
                )
            )


        salida = (
            self.salida_repository.obtener_por_id(
                id_salida
            )
        )


        if not salida:

            salidas = (
                self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                )
            )


            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=salidas,
                error=(
                    "La salida seleccionada "
                    "no existe."
                )
            )


        if salida["id_paquete"] != paquete["id_paquete"]:

            salidas = (
                self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                )
            )


            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=salidas,
                error=(
                    "La fecha seleccionada "
                    "no pertenece a este paquete."
                )
            )


        if salida["estado"] not in (
            "programada",
            "disponible"
        ):

            salidas = (
                self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                )
            )


            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=salidas,
                error=(
                    "La fecha seleccionada "
                    "ya no está disponible."
                )
            )


        fecha_viaje = salida["fecha_salida"]


        # -----------------------------------------------------
        # CANTIDAD DE VIAJEROS
        # -----------------------------------------------------

        try:

            adultos = max(
                1,
                int(
                    request.form.get(
                        "adultos",
                        "1"
                    )
                )
            )

            menores = max(
                0,
                int(
                    request.form.get(
                        "menores",
                        "0"
                    )
                )
            )

        except (
            ValueError,
            TypeError
        ):

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=(
                    "La cantidad de viajeros "
                    "no es válida."
                )
            )


        total_personas = (
            adultos + menores
        )


        if total_personas < 1:

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=(
                    "Debes ingresar al menos "
                    "un viajero."
                )
            )


        # -----------------------------------------------------
        # DATOS GENERALES
        # -----------------------------------------------------

        alergias = (
            request.form
            .get("alergias", "")
            .strip()
        )


        observaciones = (
            request.form
            .get("observaciones", "")
            .strip()
        )


        plan = (
            request.form
            .get("plan", "completo")
            .strip()
        )


        mascotas = (
            request.form
            .get("mascotas", "no")
            .strip()
            .lower()
            == "si"
        )


        metodo_contacto = (
            request.form
            .get("metodo_contacto", "correo")
            .strip()
        )


        acepta = (
            usuario.get(
                "acepta_politica_no_reembolso",
                False
            )
        )


        if not acepta:

            acepta = (
                request.form
                .get(
                    "acepta_no_reembolso"
                )
                == "1"
            )


        if not acepta:

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=(
                    "Debes aceptar la política "
                    "de no reembolso."
                )
            )


        # -----------------------------------------------------
        # VIAJEROS
        # -----------------------------------------------------

        nombres = request.form.getlist(
            "viajero_nombre[]"
        )

        apellidos = request.form.getlist(
            "viajero_apellido[]"
        )

        tipos = request.form.getlist(
            "viajero_tipo_documento[]"
        )

        documentos = request.form.getlist(
            "viajero_documento[]"
        )

        idiomas = request.form.getlist(
            "viajero_idioma[]"
        )


        if (
            len(nombres) != total_personas
            or len(apellidos) != total_personas
            or len(tipos) != total_personas
            or len(documentos) != total_personas
            or len(idiomas) != total_personas
        ):

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=(
                    "Debes completar los datos "
                    "de todos los viajeros."
                )
            )


        viajeros = []


        for i in range(total_personas):

            nombre = nombres[i].strip()

            apellido = apellidos[i].strip()

            tipo = tipos[i].strip()

            documento = documentos[i].strip()

            idioma = idiomas[i].strip()


            if (
                not nombre
                or not apellido
                or not tipo
                or not documento
                or not idioma
            ):

                return render_template(
                    "cliente/reserva.html",
                    paquete=paquete,
                    salidas=self.salida_repository.obtener_por_paquete(
                        paquete["id_paquete"],
                        solo_disponibles=True
                    ),
                    error=(
                        f"Completa los datos "
                        f"del viajero {i + 1}."
                    )
                )


            viajeros.append(
                {
                    "nombre": nombre,
                    "apellido": apellido,
                    "tipo_documento": tipo,
                    "numero_documento": documento,
                    "idioma": idioma
                }
            )

        
        # -----------------------------------------------------
        # SERVICIOS EXTRA
        # -----------------------------------------------------

        extras_ids = []


        for extra in request.form.getlist(
            "extras"
        ):

            try:

                extras_ids.append(
                    int(extra)
                )

            except (
                ValueError,
                TypeError
            ):

                continue


        # -----------------------------------------------------
        # CLIENTE
        # -----------------------------------------------------

        id_cliente = (
            usuario.get("id")
            or usuario.get("id_cliente")
        )


        # -----------------------------------------------------
        # VALOR REFERENCIAL
        # -----------------------------------------------------

        try:

            precio = float(
                paquete.get(
                    "precio",
                    0
                ) or 0
            )

        except (
            ValueError,
            TypeError
        ):

            precio = 0


        valor_referencial = (
            precio * total_personas
        )


        # -----------------------------------------------------
        # DATOS DE RESERVA
        # -----------------------------------------------------
        


        resultado = (
            self.service.confirmar_reserva(

                id_cliente=id_cliente,

                id_paquete=paquete[
                    "id_paquete"
                ],

                id_salida=id_salida,

                fecha_viaje=fecha_viaje,

                cant_adultos=adultos,

                cant_menores=menores,

                observaciones=observaciones,

                acepta_no_reembolso=acepta,

                alergias=alergias,

                mascotas=mascotas,

                plan=plan,

                metodo_contacto=metodo_contacto,

                extras_ids=extras_ids,

                viajeros=viajeros,

                precio_total=valor_referencial

            )
        )


        if not resultado:

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=(
                    "No fue posible registrar "
                    "la reserva."
                )
            )


        if not resultado.get("ok"):

            return render_template(
                "cliente/reserva.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                error=resultado.get(
                    "error",
                    "No fue posible registrar "
                    "la reserva."
                )
            )


        # -----------------------------------------------------
        # DETALLE PARA CONFIRMACIÓN
        # -----------------------------------------------------

        detalle = resultado.copy()


        detalle.update(
            {
                "paquete": paquete,

                "id_salida": id_salida,

                "fecha_viaje": fecha_viaje,

                "fecha_regreso": (
                    salida["fecha_regreso"]
                ),

                "cant_adultos": adultos,

                "cant_menores": menores,

                "total_personas": total_personas,

                "valor_referencial":
                    valor_referencial,

                "viajeros": viajeros,

                "estado":
                    detalle.get(
                        "estado",
                        "solicitada"
                    ),

                "pago_directo": True
            }
        )



    # =========================================================
    # CONFIRMACIÓN EDITABLE (nuevo flujo)
    # =========================================================

    def mostrar_confirmacion_reserva(self, slug):

        if not session.get("usuario"):
            session["reserva_pendiente_url"] = url_for(
                "reserva.confirmar_reserva", slug=slug
            )
            return redirect(
                url_for(
                    "auth.mostrar_login",
                    next=session["reserva_pendiente_url"]
                )
            )

        paquete = self.paquete_service.obtener_detalle(slug)

        if not paquete:
            return redirect(url_for("paquetes.listar_catalogo"))

        seleccion = session.get("seleccion_reserva")

        if not seleccion or seleccion.get("slug") != slug:
            return redirect(
                url_for("paquetes.ver_detalle", slug=slug)
            )

        salidas = self.salida_repository.obtener_por_paquete(
            paquete["id_paquete"],
            solo_disponibles=True
        )

        salida = self.salida_repository.obtener_por_id(
            seleccion["id_salida"]
        )

        total_personas = (
            int(seleccion.get("adultos", 1) or 1)
            + int(seleccion.get("menores", 0) or 0)
        )

        desglose = self._calcular_desglose_precio(
            paquete, seleccion, total_personas
        )

        return render_template(
            "cliente/reserva_confirmar.html",
            paquete=paquete,
            salidas=salidas,
            salida=salida,
            seleccion=seleccion,
            desglose=desglose
        )


    # =========================================================
    # GUARDAR RESERVA (nuevo flujo)
    # =========================================================

    def guardar_reserva(self, slug):

        usuario = session.get("usuario")

        if not usuario:
            return redirect(
                url_for(
                    "auth.mostrar_login",
                    next=f"/reserva/confirmar/{slug}"
                )
            )

        paquete = self.paquete_service.obtener_detalle(slug)

        if not paquete:
            return redirect(url_for("paquetes.listar_catalogo"))

        # -----------------------------------------------------
        # SESIÓN DE SELECCIÓN
        # -----------------------------------------------------

        seleccion = session.get("seleccion_reserva")

        if not seleccion or seleccion.get("slug") != slug:
            return redirect(
                url_for("paquetes.ver_detalle", slug=slug)
            )

        # La selección puede haber sido editada en la pantalla
        # de confirmación, así que se relee del formulario.

        seleccion = self._leer_seleccion_form(
            seleccion,
            paquete=paquete
        )

        session["seleccion_reserva"] = seleccion

        id_form = request.form.get("id_salida", "").strip()

        if id_form.isdigit():
            id_salida = int(id_form)
        else:
            id_salida = seleccion["id_salida"]

        salida = self.salida_repository.obtener_por_id(id_salida)

        if (
            not salida
            or salida["id_paquete"] != paquete["id_paquete"]
            or salida["estado"] not in ("programada", "disponible")
        ):
            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=self.salida_repository.obtener_por_id(
                    seleccion["id_salida"]
                ),
                seleccion=seleccion,
                error="La fecha seleccionada ya no está disponible."
            )

        fecha_viaje = salida["fecha_salida"]

        # -----------------------------------------------------
        # CANTIDAD DE VIAJEROS
        # -----------------------------------------------------

        try:

            adultos = max(
                1,
                int(
                    request.form.get("adultos")
                    or seleccion.get("adultos", 1)
                )
            )

            menores = max(
                0,
                int(
                    request.form.get("menores")
                    if request.form.get("menores") not in (None, "")
                    else seleccion.get("menores", 0)
                )
            )

            bebes = min(
                10,
                max(
                    0,
                    int(
                        request.form.get("bebes")
                        if request.form.get("bebes") not in (None, "")
                        else seleccion.get("bebes", 0)
                    )
                )
            )

        except (ValueError, TypeError):

            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error="La cantidad de viajeros no es válida."
            )

        if self._es_destino_amazonas(paquete) and bebes:
            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error="En Amazonas no se permiten bebés. Retira los bebés para continuar."
            )

        total_personas = adultos + menores + bebes
        total_pagantes = adultos + menores

        if total_personas < 1:

            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error="Debes ingresar al menos un viajero."
            )

        # -----------------------------------------------------
        # DATOS GENERALES
        # -----------------------------------------------------

        alergias = (
            request.form.get("alergias")
            if request.form.get("alergias") is not None
            else seleccion.get("alergias", "")
        ).strip()

        observaciones = (
            request.form.get("observaciones")
            if request.form.get("observaciones") is not None
            else seleccion.get("observaciones", "")
        ).strip()

        plan = request.form.get("plan", "completo").strip()

        valor_mascotas = request.form.get("mascotas")
        if valor_mascotas is None:
            valor_mascotas = "si" if seleccion.get("mascotas") else "no"

        mascotas = valor_mascotas.strip().lower() == "si"

        metodo_contacto = (
            request.form.get("metodo_contacto", "correo").strip()
        )

        acepta = bool(usuario.get("acepta_politica_no_reembolso", False))

        if not acepta:
            acepta = (
                request.form.get("acepta_no_reembolso") == "1"
                or bool(seleccion.get("acepta_no_reembolso"))
            )

        if not acepta:

            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error="Debes aceptar la política de no reembolso."
            )

        # -----------------------------------------------------
        # VIAJEROS
        # -----------------------------------------------------

        viajeros_guardados = seleccion.get("viajeros", [])

        def _campo_viajeros(nombre, clave):
            valores = request.form.getlist(nombre)
            if valores:
                return valores
            return [str(viajero.get(clave, "")) for viajero in viajeros_guardados]

        nombres = _campo_viajeros("viajero_nombre[]", "nombre")
        apellidos = _campo_viajeros("viajero_apellido[]", "apellido")
        tipos = _campo_viajeros("viajero_tipo_documento[]", "tipo_documento")
        documentos = _campo_viajeros("viajero_documento[]", "numero_documento")
        idiomas = _campo_viajeros("viajero_idioma[]", "idioma")
        edades = _campo_viajeros("viajero_edad[]", "edad")
        meses = _campo_viajeros("viajero_meses[]", "meses")
        necesidades = _campo_viajeros("viajero_necesidades[]", "necesidades")

        if (
            len(nombres) != total_personas
            or len(apellidos) != total_personas
            or len(tipos) != total_personas
            or len(documentos) != total_personas
            or len(idiomas) != total_personas
        ):

            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error="Debes completar los datos de todos los viajeros."
            )

        def _valor_viajero(lista, indice):
            return lista[indice].strip() if indice < len(lista) else ""

        viajeros = []

        for i in range(total_personas):

            nombre = nombres[i].strip()
            apellido = apellidos[i].strip()
            tipo = tipos[i].strip()
            documento = documentos[i].strip()
            idioma = idiomas[i].strip()
            categoria = self._categoria_viajero(i, adultos, menores)
            permitidos = self._tipos_documento_permitidos(categoria)

            if not (nombre and apellido and tipo and documento and idioma):

                return render_template(
                    "cliente/reserva_confirmar.html",
                    paquete=paquete,
                    salidas=self.salida_repository.obtener_por_paquete(
                        paquete["id_paquete"],
                        solo_disponibles=True
                    ),
                    salida=salida,
                    seleccion=seleccion,
                    error=f"Completa los datos del viajero {i + 1}."
                )

            if tipo not in permitidos:
                return render_template(
                    "cliente/reserva_confirmar.html",
                    paquete=paquete,
                    salidas=self.salida_repository.obtener_por_paquete(
                        paquete["id_paquete"],
                        solo_disponibles=True
                    ),
                    salida=salida,
                    seleccion=seleccion,
                    error=(
                        f"El viajero {i + 1} es {categoria} y debe usar "
                        f"{' o '.join(permitidos)}."
                    )
                )

            if not self._documento_valido(tipo, documento):
                return render_template(
                    "cliente/reserva_confirmar.html",
                    paquete=paquete,
                    salidas=self.salida_repository.obtener_por_paquete(
                        paquete["id_paquete"],
                        solo_disponibles=True
                    ),
                    salida=salida,
                    seleccion=seleccion,
                    error=(
                        f"El documento del viajero {i + 1} "
                        "no tiene un formato válido."
                    )
                )

            edad = _valor_viajero(edades, i)
            edad_meses = _valor_viajero(meses, i)

            if categoria == "menor":
                try:
                    anios = int(edad)
                except (TypeError, ValueError):
                    anios = 0
                if anios < 2 or anios > 17:
                    return render_template(
                        "cliente/reserva_confirmar.html",
                        paquete=paquete,
                        salidas=self.salida_repository.obtener_por_paquete(
                            paquete["id_paquete"],
                            solo_disponibles=True
                        ),
                        salida=salida,
                        seleccion=seleccion,
                        error=(
                            "Los niños van de 2 a 17 años; "
                            "desde 24 meses dejan de ser bebés."
                        )
                    )

            if categoria == "bebe":
                try:
                    edad_meses_numero = int(edad_meses or 0)
                except (TypeError, ValueError):
                    edad_meses_numero = -1
                if edad_meses_numero < 0 or edad_meses_numero > 23:
                    return render_template(
                        "cliente/reserva_confirmar.html",
                        paquete=paquete,
                        salidas=self.salida_repository.obtener_por_paquete(
                            paquete["id_paquete"],
                            solo_disponibles=True
                        ),
                        salida=salida,
                        seleccion=seleccion,
                        error=(
                            "Desde los 24 meses deja de ser bebé: "
                            "cambia a niño o corrige los meses (0 a 23)."
                        )
                    )

            viajeros.append(
                {
                    "nombre": nombre,
                    "apellido": apellido,
                    "categoria": categoria,
                    "tipo_documento": tipo,
                    "numero_documento": documento,
                    "idioma": idioma,
                    "edad": edad,
                    "meses": edad_meses,
                    "necesidades": _valor_viajero(necesidades, i),
                }
            )

        seleccion.update({
            "adultos": adultos,
            "menores": menores,
            "bebes": bebes,
            "viajeros": viajeros,
        })

        # -----------------------------------------------------
        # SERVICIOS EXTRA
        # -----------------------------------------------------

        extras_ids = [
            int(extra)
            for extra in request.form.getlist("extras")
            if extra.isdigit()
        ]

        id_cliente = usuario.get("id") or usuario.get("id_cliente")

        # -----------------------------------------------------
        # VALOR REFERENCIAL
        # -----------------------------------------------------

        try:

            precio = float(paquete.get("precio", 0) or 0)

        except (ValueError, TypeError):

            precio = 0

        valor_referencial = precio * total_pagantes

        desglose = ReservaController._calcular_desglose_precio(
            paquete,
            seleccion,
            total_pagantes
        )

        precio_total = desglose["total_final"]

        # -----------------------------------------------------
        # PERSONALIZACIÓN (resumen de lo seleccionado)
        # -----------------------------------------------------

        personalizacion = self._construir_personalizacion(
            paquete,
            seleccion
        )

        # La base de datos no tiene columnas para la edad de menores, el
        # detalle de mascotas ni necesidades por viajero. Se conservan como
        # texto dentro de observaciones, que sí se persiste y se muestra en
        # el comprobante.
        detalles = []

        if mascotas and seleccion.get("mascotas_cantidad"):
            detalles.append(
                "Mascotas: " + str(seleccion["mascotas_cantidad"])
                + (", " + str(seleccion["mascotas_tipo"])
                   if seleccion.get("mascotas_tipo") else "")
            )

        for indice, viajero in enumerate(viajeros, start=1):
            if viajero.get("categoria") == "menor" and viajero.get("edad"):
                detalles.append(
                    f"Viajero {indice} (menor), edad: {viajero['edad']} años"
                )
            if viajero.get("categoria") == "bebe":
                detalles.append(
                    f"Viajero {indice} (bebé), edad: {viajero.get('meses', 0)} meses"
                )
            if viajero.get("necesidades"):
                detalles.append(
                    f"Viajero {indice}, necesidades: {viajero['necesidades']}"
                )

        if detalles:
            observaciones = "\n".join(
                detalles + ([observaciones] if observaciones else [])
            )

        if observaciones:

            personalizacion = (
                personalizacion + "\nSolicitudes especiales: "
                + observaciones
            )

        # -----------------------------------------------------
        # CREAR RESERVA
        # -----------------------------------------------------

        resultado = self.service.confirmar_reserva(
            id_cliente=id_cliente,
            id_paquete=paquete["id_paquete"],
            id_salida=id_salida,
            fecha_viaje=fecha_viaje,
            cant_adultos=adultos,
            cant_menores=menores,
            observaciones=personalizacion,
            acepta_no_reembolso=acepta,
            alergias=alergias,
            mascotas=mascotas,
            plan=plan,
            metodo_contacto=metodo_contacto,
            extras_ids=extras_ids,
            viajeros=viajeros,
            precio_total=precio_total
        )

        if not resultado or not resultado.get("ok"):

            return render_template(
                "cliente/reserva_confirmar.html",
                paquete=paquete,
                salidas=self.salida_repository.obtener_por_paquete(
                    paquete["id_paquete"],
                    solo_disponibles=True
                ),
                salida=salida,
                seleccion=seleccion,
                error=(
                    resultado.get("error", "No fue posible "
                    "registrar la reserva.")
                    if resultado
                    else "No fue posible registrar la reserva."
                )
            )

        # -----------------------------------------------------
        # DETALLE PARA CONFIRMACIÓN
        # -----------------------------------------------------

        obj_extras = self._resolver_items(paquete, extras_ids)

        detalle = resultado.copy()

        detalle.update(
            {
                "paquete": paquete,
                "id_salida": id_salida,
                "fecha_viaje": fecha_viaje,
                "fecha_regreso": salida["fecha_regreso"],
                "cant_adultos": adultos,
                "cant_menores": menores,
                "total_personas": total_personas,
                "valor_referencial": valor_referencial,
                "precio_total": precio_total,
                "desglose": desglose,
                "viajeros": viajeros,
                "paquete_nombre": paquete["nombre"],
                "destino": paquete.get("nombre_destino", ""),
                "duracion": (
                    f"{paquete.get('duracion_dias', 0)} días · "
                    f"{paquete.get('duracion_noches', 0)} noches"
                ),
                "adultos": adultos,
                "menores": menores,
                "extras": obj_extras,
                "alojamientos": self._seleccionados_alojamientos(
                    paquete, seleccion
                ),
                "alimentacion": self._seleccionados_alimentacion(
                    paquete, seleccion
                ),
                "transportes": self._seleccionados_transportes(
                    paquete, seleccion
                ),
                "actividades": self._seleccionados_actividades(
                    paquete, seleccion
                ),
                "seguros": self._seleccionados_seguros(
                    paquete, seleccion
                ),
                "personalizacion": personalizacion,
                "notas": observaciones,
                "alergias": alergias,
                "estado": detalle.get("estado", "solicitada"),
                "pago_directo": True
            }
        )

        print("DEBUG - Usuario en sesión:", usuario is not None)
        print("DEBUG - Claves disponibles:", list(usuario.keys()) if isinstance(usuario, dict) else "No es un diccionario")
        print("DEBUG - Correo disponible:", bool(usuario.get("correo")) if isinstance(usuario, dict) else False)
                
        correo_cliente = (
           usuario.get("correo")
        )
                
        nombre_cliente = (
           usuario.get("nombre")
          or "Cliente"
        )

        session["detalle_reserva"] = detalle
        session.pop("seleccion_reserva", None)
        session.pop("reserva_pendiente_url", None)
                
        envio_correo = (
            self.correo_service.enviar_confirmacion_reserva(
            correo_cliente=correo_cliente,
            nombre_cliente=nombre_cliente,
            reserva=detalle
                )
            )
                
        if not envio_correo.get("ok"):
                
            print(
                "AVISO: La reserva fue creada, "
                "pero no se pudo enviar el correo "
                "de confirmación."
            )
                
        else:
                
            print(
            f"Correo de confirmación enviado a "
            f"{correo_cliente}"
            )
                
                
            return redirect(
                url_for(
                "reserva.confirmacion"
                )
            )

        return redirect(url_for("reserva.confirmacion"))


    # =========================================================
    # HELPERS DE SELECCIÓN
    # =========================================================

    @staticmethod
    def _ids_form(campo):

        resultado = []

        for valor in request.form.getlist(campo):

            try:
                resultado.append(int(valor))
            except (ValueError, TypeError):
                continue

        return resultado


    def _leer_seleccion_form(self, base, paquete=None):

        seleccion = dict(base)

        seleccion.update(
            {
                "alojamiento": self._ids_form(
                    "alojamiento"
                ),
                "alimentacion": self._ids_form(
                    "alimentacion"
                ),
                "transporte": self._ids_form(
                    "transporte"
                ),
                "actividades": self._ids_form(
                    "actividades"
                ),
                "seguros": self._ids_form(
                    "seguros"
                ),
                "extras": self._ids_form(
                    "extras"
                ),
            }
        )

        # Los seguros obligatorios se muestran marcados
        # y deshabilitados, por lo que no llegan por el
        # formulario; se agregan siempre.

        if paquete:

            ids = set(seleccion["seguros"])

            for seguro in paquete.get("seguros", []):

                if seguro.get("es_obligatorio"):

                    ids.add(seguro.get("id_seguro"))

            seleccion["seguros"] = sorted(ids)

        return seleccion


    @staticmethod
    def _resolver_items(paquete, ids):

        disponibles = paquete.get("servicios_extra", [])

        return [
            item for item in disponibles
            if item.get("id") in ids
        ]


    @staticmethod
    def _seleccionados_alojamientos(paquete, seleccion):

        return [
            item for item in paquete.get("alojamientos", [])
            if item.get("id_alojamiento") in seleccion.get(
                "alojamiento", []
            )
        ]


    @staticmethod
    def _seleccionados_alimentacion(paquete, seleccion):

        return [
            item for item in paquete.get("alimentacion", [])
            if item.get("id_alimentacion") in seleccion.get(
                "alimentacion", []
            )
        ]


    @staticmethod
    def _seleccionados_transportes(paquete, seleccion):

        return [
            item for item in paquete.get("transportes", [])
            if item.get("id_transporte") in seleccion.get(
                "transporte", []
            )
        ]


    @staticmethod
    def _seleccionados_actividades(paquete, seleccion):

        return [
            item for item in paquete.get("actividades", [])
            if item.get("id_actividad") in seleccion.get(
                "actividades", []
            )
        ]


    @staticmethod
    def _seleccionados_seguros(paquete, seleccion):

        return [
            item for item in paquete.get("seguros", [])
            if item.get("id_seguro") in seleccion.get(
                "seguros", []
            )
        ]


    @staticmethod
    def _construir_personalizacion(paquete, seleccion):

        lineas = []

        alojamientos = ReservaController._seleccionados_alojamientos(
            paquete, seleccion
        )

        if alojamientos:

            lineas.append(
                "Alojamiento: "
                + ", ".join(a["nombre"] for a in alojamientos)
            )

        alimentacion = ReservaController._seleccionados_alimentacion(
            paquete, seleccion
        )

        if alimentacion:

            lineas.append(
                "Alimentación: "
                + ", ".join(a["restaurante"] for a in alimentacion)
            )

        transportes = ReservaController._seleccionados_transportes(
            paquete, seleccion
        )

        if transportes:

            lineas.append(
                "Transporte: "
                + ", ".join(
                    f"{t['empresa']} ({t['tipo']})"
                    for t in transportes
                )
            )

        actividades = ReservaController._seleccionados_actividades(
            paquete, seleccion
        )

        if actividades:

            lineas.append(
                "Actividades: "
                + ", ".join(a["nombre"] for a in actividades)
            )

        seguros = ReservaController._seleccionados_seguros(
            paquete, seleccion
        )

        if seguros:

            lineas.append(
                "Seguro: "
                + ", ".join(s["nombre"] for s in seguros)
            )

        extras = ReservaController._resolver_items(
            paquete, seleccion.get("extras", [])
        )

        if extras:

            lineas.append(
                "Servicios extra: "
                + ", ".join(e["nombre"] for e in extras)
            )

        if not lineas:

            lineas.append(
                "Composición estándar del paquete."
            )

        return "\n".join(lineas)


    @staticmethod
    def _a_float(valor):

        try:

            return float(valor or 0)

        except (ValueError, TypeError):

            return 0.0

    @staticmethod
    def _calcular_desglose_precio(paquete, seleccion, total_personas):

        base = ReservaController._a_float(paquete.get("precio", 0))
        items = []

        def agregar(grupo, nombre, precio):
            items.append({
                "grupo": grupo,
                "nombre": nombre or grupo,
                "precio": round(ReservaController._a_float(precio), 2),
            })

        for item in ReservaController._seleccionados_alimentacion(
            paquete, seleccion
        ):
            agregar(
                "Alimentación",
                item.get("restaurante") or item.get("nombre"),
                item.get("precio", 0),
            )

        for item in ReservaController._seleccionados_actividades(
            paquete, seleccion
        ):
            agregar(
                "Actividades",
                item.get("nombre"),
                item.get("costo", 0),
            )

        for item in ReservaController._seleccionados_seguros(
            paquete, seleccion
        ):
            agregar(
                "Seguro",
                item.get("nombre"),
                item.get("precio", 0),
            )

        for item in ReservaController._resolver_items(
            paquete, seleccion.get("extras", [])
        ):
            agregar(
                "Servicio extra",
                item.get("nombre"),
                item.get("precio", 0),
            )

        incluidos = []

        for item in ReservaController._seleccionados_alojamientos(
            paquete, seleccion
        ):
            incluidos.append(item.get("nombre") or "Alojamiento")

        for item in ReservaController._seleccionados_transportes(
            paquete, seleccion
        ):
            incluidos.append(
                f"{item.get('empresa') or 'Transporte'} ({item.get('tipo') or 'incluido'})"
            )

        adicionales = round(sum(i["precio"] for i in items), 2)
        por_persona = round(base + adicionales, 2)

        try:
            personas = max(int(total_personas or 1), 1)
        except (ValueError, TypeError):
            personas = 1

        return {
            "base_por_persona": round(base, 2),
            "incluidos": incluidos,
            "items": items,
            "adicionales_por_persona": adicionales,
            "precio_por_persona": por_persona,
            "total_personas": personas,
            "total_final": round(por_persona * personas, 2),
        }

    @staticmethod
    def _calcular_precio_total(paquete, seleccion, total_personas):

        return ReservaController._calcular_desglose_precio(
            paquete, seleccion, total_personas
        )["total_final"]


    # =========================================================
    # CONFIRMACIÓN
    # =========================================================

    def mostrar_confirmacion(self):

        detalle = session.get(
            "detalle_reserva"
        )


        if not detalle:

            return redirect(
                url_for(
                    "paquetes.listar_catalogo"
                )
            )


        return render_template(
            "principal/reserva_confirmada.html",
            reserva=detalle,
            detalle=detalle
        )

    def descargar_pdf(self):

        detalle = session.get(
            "detalle_reserva"
        )


        if not detalle:

            return redirect(
                url_for(
                    "paquetes.listar_catalogo"
                )
            )


        return self.pdf_service.generar_resumen_reserva(
            detalle
        )

    def cancelar_reserva_cliente(self, id_reserva):

        usuario = session.get("usuario") or {}

        id_cliente = (
            usuario.get("id")
            or usuario.get("id_cliente")
        )

        if not id_cliente:
            return redirect(
                url_for(
                    "auth.mostrar_login",
                    next=url_for("home.perfil")
                )
            )

        resultado = self.service.cancelar_reserva_cliente(
            id_reserva,
            id_cliente
        )

        if resultado.get("ok"):
            flash("Reserva cancelada correctamente.", "success")
        else:
            flash(
                resultado.get(
                    "error",
                    "No fue posible cancelar la reserva."
                ),
                "error"
            )

        return redirect(url_for("home.perfil"))

    def listar_reservas_cliente(self, id_cliente):
        return self.service.listar_reservas_cliente(id_cliente)

    def mostrar_pago(self, id_reserva):

        usuario = session.get("usuario")

        if not usuario:

            return redirect(
                url_for(
                    "auth.mostrar_login"
                )
            )

        id_cliente = usuario["id"]

        reserva = self.service.obtener_reserva_con_viajeros(
            id_reserva,
            id_cliente
        )

        if not reserva:
            return redirect(url_for("home.perfil"))

        paquete = self.paquete_service.obtener_por_id(
            reserva["id_paquete"]
        )

        monto = float(
            reserva.get("precio_total")
            or (paquete or {}).get("precio")
            or 0
        )

        return self._render_pago(
            reserva,
            paquete,
            monto=monto
        )

    def procesar_pago(self, id_reserva):

        usuario = session.get("usuario")

        if not usuario:

            return redirect(
                url_for(
                    "auth.mostrar_login"
                )
            )

        id_cliente = usuario["id"]

        reserva = self.service.obtener_reserva_con_viajeros(
            id_reserva,
            id_cliente
        )

        if not reserva:
            return redirect(url_for("home.perfil"))

        paquete = self.paquete_service.obtener_por_id(
            reserva["id_paquete"]
        )

        monto = float(
            reserva.get("precio_total")
            or (paquete or {}).get("precio")
            or 0
        )

        valores = {
            "metodo_pago": request.form.get("metodo_pago", ""),
            "nequi_telefono": request.form.get("nequi_telefono", ""),
            "pse_banco": request.form.get("pse_banco", ""),
            "pse_tipo_documento": request.form.get("pse_tipo_documento", ""),
            "pse_documento": request.form.get("pse_documento", ""),
            "tarjeta_tipo": request.form.get("tarjeta_tipo", ""),
            "tarjeta_numero": request.form.get("tarjeta_numero", ""),
            "tarjeta_titular": request.form.get("tarjeta_titular", ""),
            "tarjeta_vencimiento": request.form.get("tarjeta_vencimiento", ""),
        }

        metodo = (
            request.form
            .get(
                "metodo_pago",
                ""
            )
            .strip()
            .lower()
        )

        metodos_validos = {
            "nequi",
            "pse",
            "tarjeta"
        }

        if metodo not in metodos_validos:

            return self._render_pago(
                reserva,
                paquete,
                valores=valores,
                monto=monto,
                error=(
                    "Debes seleccionar "
                    "un método de pago válido."
                )
            )

        if metodo == "nequi":

            telefono = "".join(
                caracter
                for caracter in (
                    request.form
                    .get("nequi_telefono", "")
                    .strip()
                )
                if caracter.isdigit()
            )

            if (
                telefono.startswith("57")
                and len(telefono) == 12
            ):
                telefono = telefono[2:]

            if not telefono:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes ingresar "
                        "el número de celular."
                    )
                )

            if not telefono.isdigit():

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El número de Nequi "
                        "solo debe contener números."
                    )
                )

            if len(telefono) != 10:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El número de Nequi "
                        "debe tener exactamente 10 dígitos."
                    )
                )

            if not telefono.startswith("3"):

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El número de Nequi "
                        "debe comenzar por 3."
                    )
                )


        elif metodo == "pse":

            banco = (
                request.form
                .get(
                    "pse_banco",
                    ""
                )
                .strip()
            )

            tipo_documento = (
                request.form
                .get(
                    "pse_tipo_documento",
                    ""
                )
                .strip()
                .upper()
            )

            documento = (
                request.form
                .get(
                    "pse_documento",
                    ""
                )
                .strip()
            )

            bancos_validos = set(PSE_BANCOS)
            tipos_validos = set(TIPOS_DOCUMENTO)

            if banco not in bancos_validos:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes seleccionar "
                        "un banco válido."
                    )
                )

            if tipo_documento not in tipos_validos:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes seleccionar "
                        "un tipo de documento válido."
                    )
                )

            if not documento:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes ingresar "
                        "el número de documento."
                    )
                )

            if not documento.isdigit():

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El documento debe contener "
                        "solo números."
                    )
                )

            if not (
                6 <= len(documento) <= 12
            ):

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El documento debe tener "
                        "entre 6 y 12 dígitos."
                    )
                )


        elif metodo == "tarjeta":

            tipo_tarjeta = (
                request.form
                .get("tarjeta_tipo", "")
                .strip()
                .lower()
            )

            if tipo_tarjeta not in TIPOS_TARJETA:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes seleccionar el tipo de tarjeta."
                    )
                )

            numero = (
                request.form
                .get(
                    "tarjeta_numero",
                    ""
                )
                .replace(
                    " ",
                    ""
                )
                .strip()
            )

            titular = (
                request.form
                .get(
                    "tarjeta_titular",
                    ""
                )
                .strip()
            )

            vencimiento = (
                request.form
                .get(
                    "tarjeta_vencimiento",
                    ""
                )
                .strip()
            )

            cvv = (
                request.form
                .get(
                    "tarjeta_cvv",
                    ""
                )
                .strip()
            )

            if not numero:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes ingresar "
                        "el número de tarjeta."
                    )
                )

            if not numero.isdigit():

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El número de tarjeta "
                        "solo debe contener números."
                    )
                )

            if len(numero) != 16:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El número de tarjeta "
                        "debe tener exactamente 16 dígitos."
                    )
                )

            if not titular:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes ingresar "
                        "el nombre del titular."
                    )
                )

            if len(titular) < 3:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El nombre del titular "
                        "no es válido."
                    )
                )

            if not re.fullmatch(
                r"(0[1-9]|1[0-2])/[0-9]{2}",
                vencimiento
            ):

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El vencimiento debe tener "
                        "el formato MM/AA."
                    )
                )

            mes = int(
                vencimiento[:2]
            )

            anio = int(
                vencimiento[3:]
            )

            anio_completo = 2000 + anio

            fecha_actual = datetime.datetime.now()

            if (
                anio_completo < fecha_actual.year
                or (
                    anio_completo == fecha_actual.year
                    and mes < fecha_actual.month
                )
            ):

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "La tarjeta está vencida."
                    )
                )


            if not cvv:

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "Debes ingresar "
                        "el CVV."
                    )
                )

            if not cvv.isdigit():

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El CVV solo debe contener números."
                    )
                )

            if len(cvv) not in (3, 4):

                return self._render_pago(
                    reserva,
                    paquete,
                    valores=valores,
                    monto=monto,
                    error=(
                        "El CVV debe tener "
                        "3 o 4 dígitos."
                    )
                )
            
        datos_pago = {
            "id_reserva": id_reserva,
            "id_cliente": id_cliente,
            "codigo_unico": reserva["codigo_unico"],
            "monto": monto,
            "metodo": metodo,
            "metodo_nombre": METODOS_PAGO[metodo],
            "beneficiario_nombre": BENEFICIARIO_NOMBRE,
            "beneficiario_cuenta": BENEFICIARIO_CUENTA,
        }

        if metodo == "nequi":

            datos_pago["telefono"] = telefono
            datos_pago["detalle_pagador"] = f"Nequi {telefono}"

        elif metodo == "pse":

            datos_pago["banco"] = banco
            datos_pago["documento"] = documento
            datos_pago["detalle_pagador"] = (
                f"{banco} · {tipo_documento} {documento}"
            )

        else:

            tipo_tarjeta_nombre = (
                "CRÉDITO" if tipo_tarjeta == "credito" else "DÉBITO"
            )
            datos_pago["tipo_tarjeta"] = tipo_tarjeta
            datos_pago["ultimos4"] = numero[-4:]
            datos_pago["detalle_pagador"] = (
                f"{tipo_tarjeta_nombre} · {titular} · **** {numero[-4:]}"
            )

        token = crear_token(datos_pago)

        datos_pago["token"] = token
        datos_pago["enlace_aprobacion"] = url_for(
            "reserva.aprobar_pago",
            token=token,
            _external=True
        )

        correo_cliente = usuario.get("correo")

        if not correo_cliente:

            return self._render_pago(
                reserva,
                paquete,
                valores=valores,
                monto=monto,
                error=(
                    "No pudimos encontrar tu correo registrado. "
                    "Actualízalo en tu perfil para continuar."
                )
            )

        nombre_cliente = (
            f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip()
            or "Viajero"
        )

        envio = self.correo_service.enviar_solicitud_pago(
            correo_cliente,
            nombre_cliente,
            datos_pago
        )

        if not envio["ok"]:

            return self._render_pago(
                reserva,
                paquete,
                valores=valores,
                monto=monto,
                error=(
                    "No pudimos enviar el correo de confirmación. "
                    f"{envio.get('error', '')}"
                )
            )

        return redirect(
            url_for(
                "reserva.pago_pendiente",
                token=token
            )
        )

    def pago_pendiente(self, token):

        datos_pago = leer_token(token)

        if not datos_pago:

            flash("El enlace de pago no es válido o ya venció.")

            return redirect(url_for("home.perfil"))

        return render_template(
            "cliente/pago_pendiente.html",
            pago=datos_pago,
            token=token
        )

    def estado_pago(self, token):

        datos_pago = leer_token(token)

        if not datos_pago:
            return jsonify({"ok": False}), 400

        reserva = self.service.obtener_estado_reserva(
            datos_pago["id_reserva"],
            datos_pago["id_cliente"]
        )

        aprobado = bool(
            reserva
            and reserva.get("estado") == "pagada"
        )

        return jsonify({
            "ok": True,
            "aprobado": aprobado,
            "estado": (reserva or {}).get("estado")
        })

    def aprobar_pago(self, token):

        datos_pago = leer_token(token)

        if not datos_pago:

            flash("El enlace de pago no es válido o ya venció.")

            return redirect(url_for("home.perfil"))

        reserva = self.service.obtener_estado_reserva(
            datos_pago["id_reserva"],
            datos_pago["id_cliente"]
        )

        if not reserva:

            flash("No encontramos la reserva asociada a este pago.")

            return redirect(url_for("home.perfil"))

        if reserva.get("estado") != "pagada":

            cambio_estado = self.service.cambiar_estado_reserva(
                datos_pago["id_reserva"],
                datos_pago["id_cliente"]
            )

            if not cambio_estado["ok"]:

                estado_actual = self.service.obtener_estado_reserva(
                    datos_pago["id_reserva"],
                    datos_pago["id_cliente"]
                )

                if not estado_actual or estado_actual.get("estado") != "pagada":

                    flash(
                        "No fue posible registrar el pago. "
                        "Intenta nuevamente o contacta a servicio al cliente."
                    )

                    return redirect(
                        url_for(
                            "reserva.pago_pendiente",
                            token=token
                        )
                    )

        datos_pago = dict(datos_pago)
        datos_pago["estado"] = "pagada"
        datos_pago["fecha_aprobacion"] = datetime.datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )

        detalle = session.get("detalle_reserva")

        if (
            detalle
            and detalle.get("id_reserva") == datos_pago["id_reserva"]
        ):
            detalle["estado"] = "pagada"
            session["detalle_reserva"] = detalle

        return render_template(
            "cliente/pago_exitoso.html",
            pago=datos_pago,
            token=token
        )

    def descargar_comprobante(self, token):

        datos_pago = leer_token(token)

        if not datos_pago:

            flash("El comprobante no es válido o ya venció.")

            return redirect(url_for("home.perfil"))

        reserva = self.service.obtener_estado_reserva(
            datos_pago["id_reserva"],
            datos_pago["id_cliente"]
        )

        if not reserva or reserva.get("estado") != "pagada":

            flash("El pago aún no ha sido aprobado.")

            return redirect(
                url_for(
                    "reserva.pago_pendiente",
                    token=token
                )
            )

        datos_pago = dict(datos_pago)

        if not datos_pago.get("fecha_aprobacion"):

            datos_pago["fecha_aprobacion"] = datetime.datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            )

        archivo = self.pdf_service.generar_comprobante_pago(
            datos_pago
        )

        codigo = str(
            datos_pago.get("codigo_unico", "pago")
        ).replace("/", "-")

        return send_file(
            archivo,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"comprobante_{codigo}.pdf"
        )
