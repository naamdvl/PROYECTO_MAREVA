import html
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Paleta MAREVA Caribe
MOR_ADO = colors.HexColor("#2b0870")
TURQUESA = colors.HexColor("#0f8fa4")
CORAL = colors.HexColor("#ff6f61")
ARENA = colors.HexColor("#fdf5e4")
GRIS_TEXTO = colors.HexColor("#4a5568")
GRIS_CLARO = colors.HexColor("#f4f7f6")


class PDFService:
    """Genera un PDF simple y elegante con el resumen de una reserva."""

    def generar_resumen_reserva(self, detalle):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            title=f"Reserva {detalle.get('codigo_unico', '')} · MAREVA",
        )

        estilos = getSampleStyleSheet()
        estilo_marca = ParagraphStyle(
            "Marca", parent=estilos["Normal"], fontSize=20, textColor=MOR_ADO,
            fontName="Helvetica-Bold", spaceAfter=2,
        )
        estilo_subtitulo = ParagraphStyle(
            "Subtitulo", parent=estilos["Normal"], fontSize=9.5,
            textColor=GRIS_TEXTO, spaceAfter=10,
        )
        estilo_h2 = ParagraphStyle(
            "H2", parent=estilos["Normal"], fontSize=12.5, textColor=MOR_ADO,
            fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
        )
        estilo_texto = ParagraphStyle(
            "Texto", parent=estilos["Normal"], fontSize=9.5,
            textColor=GRIS_TEXTO, leading=14,
        )
        estilo_codigo = ParagraphStyle(
            "Codigo", parent=estilos["Normal"], fontSize=13, textColor=CORAL,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        )
        estilo_pie = ParagraphStyle(
            "Pie", parent=estilos["Normal"], fontSize=7.6, textColor=colors.HexColor("#8a97a6"),
            leading=11,
        )

        elementos = []

        elementos.append(Paragraph("MAREVA", estilo_marca))
        elementos.append(Paragraph("Resumen de solicitud de reserva · Caribe colombiano", estilo_subtitulo))
        elementos.append(HRFlowable(width="100%", thickness=1.4, color=TURQUESA, spaceAfter=10))

        elementos.append(Paragraph("CÓDIGO DE RESERVA", ParagraphStyle(
            "Label", parent=estilo_texto, alignment=TA_CENTER, fontSize=8, textColor=GRIS_TEXTO
        )))
        elementos.append(Paragraph(detalle.get("codigo_unico", "-"), estilo_codigo))
        elementos.append(Spacer(1, 10))

        # --- Datos del paquete ---
        elementos.append(Paragraph("Tu experiencia", estilo_h2))
        datos_paquete = [
            ["Paquete", detalle.get("paquete_nombre", "-")],
            ["Destino", detalle.get("destino", "-")],
            ["Duración", detalle.get("duracion", "-")],
            ["Fecha del viaje", detalle.get("fecha_viaje") or "Por confirmar"],
            ["Viajeros", f"{detalle.get('adultos', 0)} adulto(s) · {detalle.get('menores', 0)} menor(es)"],
            ["Estado", detalle.get("estado", "Solicitada").capitalize()],
        ]
        tabla_paquete = Table(datos_paquete, colWidths=[45 * mm, 115 * mm])
        tabla_paquete.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.3),
            ("TEXTCOLOR", (0, 0), (0, -1), MOR_ADO),
            ("TEXTCOLOR", (1, 0), (1, -1), GRIS_TEXTO),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e5ecea")),
            ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ]))
        elementos.append(tabla_paquete)

        # --- Servicios seleccionados ---
        items_servicios = []

        if detalle.get("alojamientos"):
            for a in detalle["alojamientos"]:
                items_servicios.append(
                    ["🏨 Alojamiento", a.get("nombre", ""), f"$ {0:,.0f}"]
                )

        if detalle.get("alimentacion"):
            for a in detalle["alimentacion"]:
                items_servicios.append(
                    ["🍽️ Alimentación", a.get("restaurante", ""), f"$ {a.get('precio', 0) or 0:,.0f}"]
                )

        if detalle.get("transportes"):
            for t in detalle["transportes"]:
                items_servicios.append(
                    ["🚌 Transporte", f"{t.get('empresa', '')} ({t.get('tipo', '')})", f"$ {0:,.0f}"]
                )

        if detalle.get("actividades"):
            for a in detalle["actividades"]:
                items_servicios.append(
                    ["🎟️ Actividad", a.get("nombre", ""), f"$ {a.get('costo', 0) or 0:,.0f}"]
                )

        if detalle.get("seguros"):
            for s in detalle["seguros"]:
                items_servicios.append(
                    ["🛡️ Seguro", s.get("nombre", ""), f"$ {s.get('precio', 0) or 0:,.0f}"]
                )

        for e in (detalle.get("extras") or []):
            items_servicios.append(
                ["✨ Extra", e.get("nombre", ""), f"$ {e.get('precio', 0) or 0:,.0f}"]
            )

        if items_servicios:
            elementos.append(Paragraph("Servicios seleccionados", estilo_h2))
            filas_s = [["Tipo", "Servicio", "Precio"]] + items_servicios
            tabla_s = Table(filas_s, colWidths=[42 * mm, 92 * mm, 26 * mm])
            tabla_s.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), MOR_ADO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(tabla_s)

        # --- Personalización ---
        if detalle.get("personalizacion"):
            elementos.append(Paragraph("Personalización solicitada", estilo_h2))
            texto_per = str(detalle["personalizacion"]).replace("\n", "<br/>")
            elementos.append(Paragraph(texto_per, estilo_texto))

        # --- Extras ---
        if detalle.get("extras"):
            elementos.append(Paragraph("Experiencias opcionales agregadas", estilo_h2))
            filas = [["Servicio", "Precio"]] + [
                [e["nombre"], f"$ {e['precio']:,.0f}"] for e in detalle["extras"]
            ]
            tabla_extras = Table(filas, colWidths=[120 * mm, 40 * mm])
            tabla_extras.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), MOR_ADO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elementos.append(tabla_extras)

        # --- Precio ---
        elementos.append(Spacer(1, 12))
        desglose = detalle.get("desglose") or {}
        filas_precio = []

        if desglose:
            filas_precio.append([
                "Precio base del paquete (por persona)",
                f"$ {desglose.get('base_por_persona', 0):,.0f} COP",
            ])
            for item in desglose.get("items", []):
                filas_precio.append([
                    f"{item.get('grupo')}: {item.get('nombre')}",
                    f"$ {item.get('precio', 0):,.0f} COP",
                ])
            filas_precio.append([
                "Adicionales por persona",
                f"$ {desglose.get('adicionales_por_persona', 0):,.0f} COP",
            ])
            filas_precio.append([
                "Precio por persona",
                f"$ {desglose.get('precio_por_persona', 0):,.0f} COP",
            ])
            filas_precio.append([
                "Viajeros",
                str(desglose.get("total_personas", 1)),
            ])
            precio_total = desglose.get(
                "total_final", detalle.get("precio_total", 0)
            )
        else:
            precio_total = detalle.get("precio_total", 0)

        filas_precio.append([
            "TOTAL DE LA RESERVA",
            f"$ {precio_total:,.0f} COP",
        ])

        tabla_precio = Table(
            filas_precio,
            colWidths=[110 * mm, 50 * mm],
        )
        tabla_precio.setStyle(TableStyle([
            ("BACKGROUND", (0, -1), (-1, -1), MOR_ADO),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -2), [colors.white, GRIS_CLARO]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elementos.append(tabla_precio)

        # --- Notas ---
        if detalle.get("notas") or detalle.get("alergias"):
            elementos.append(Paragraph("Notas del viajero", estilo_h2))
            if detalle.get("alergias"):
                elementos.append(Paragraph(f"<b>Alergias / necesidades:</b> {detalle['alergias']}", estilo_texto))
            if detalle.get("notas"):
                elementos.append(Paragraph(f"<b>Solicitudes especiales:</b> {detalle['notas']}", estilo_texto))

        elementos.append(Spacer(1, 18))
        elementos.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#dfe6e4"), spaceAfter=8))

        elementos.append(Paragraph(
            "El pago de este viaje se realiza directamente al proveedor del servicio, "
            "siguiendo las instrucciones que MAREVA te compartirá por correo. MAREVA no procesa pagos "
            "ni cobra comisiones dentro de esta plataforma.",
            estilo_pie,
        ))
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph(
            "Esta solicitud queda sujeta a la Política de No Reembolso de MAREVA aceptada por el cliente "
            "durante su registro. Documento generado automáticamente, no requiere firma.",
            estilo_pie,
        ))

        doc.build(elementos)
        buffer.seek(0)
        return buffer

    def _pie_comprobante(self, lienzo, documento):
        lienzo.saveState()
        lienzo.setFont("Helvetica", 7)
        lienzo.setFillColor(colors.HexColor("#8a97a6"))
        lienzo.drawString(
            20 * mm,
            10 * mm,
            "MAREVA · Comprobante generado automáticamente",
        )
        lienzo.drawRightString(
            190 * mm,
            10 * mm,
            f"Página {documento.page}",
        )
        lienzo.restoreState()

    def generar_comprobante_pago(self, pago):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            title=f"Comprobante de pago {pago.get('codigo_unico', '')}",
        )

        estilos = getSampleStyleSheet()
        estilo_marca = ParagraphStyle(
            "MarcaComprobante",
            parent=estilos["Normal"],
            fontSize=22,
            textColor=colors.white,
            fontName="Helvetica-Bold",
            leading=24,
        )
        estilo_marca_secundaria = ParagraphStyle(
            "MarcaComprobanteSecundaria",
            parent=estilos["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#d8ccf4"),
            fontName="Helvetica-Bold",
            letterSpacing=1.2,
            leading=14,
        )
        estilo_titulo = ParagraphStyle(
            "TituloComprobante",
            parent=estilos["Normal"],
            fontSize=17,
            textColor=MOR_ADO,
            fontName="Helvetica-Bold",
            leading=20,
        )
        estilo_estado = ParagraphStyle(
            "EstadoComprobante",
            parent=estilos["Normal"],
            fontSize=10,
            textColor=colors.white,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            leading=12,
        )
        estilo_etiqueta = ParagraphStyle(
            "EtiquetaComprobante",
            parent=estilos["Normal"],
            fontSize=8,
            textColor=GRIS_TEXTO,
            fontName="Helvetica-Bold",
            leading=11,
        )
        estilo_monto = ParagraphStyle(
            "MontoComprobante",
            parent=estilos["Normal"],
            fontSize=26,
            textColor=MOR_ADO,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            leading=30,
        )
        estilo_frase = ParagraphStyle(
            "FraseComprobante",
            parent=estilos["Normal"],
            fontSize=10.5,
            textColor=GRIS_TEXTO,
            alignment=TA_CENTER,
            leading=15,
        )
        estilo_celda = ParagraphStyle(
            "CeldaComprobante",
            parent=estilos["Normal"],
            fontSize=9.5,
            textColor=colors.HexColor("#263445"),
            leading=13,
        )
        estilo_seccion = ParagraphStyle(
            "SeccionComprobante",
            parent=estilos["Normal"],
            fontSize=11,
            textColor=MOR_ADO,
            fontName="Helvetica-Bold",
            leading=14,
            spaceBefore=4,
            spaceAfter=6,
        )
        estilo_pie = ParagraphStyle(
            "PieComprobante",
            parent=estilos["Normal"],
            fontSize=7.8,
            textColor=colors.HexColor("#8a97a6"),
            leading=11,
        )

        codigo = html.escape(str(pago.get("codigo_unico", "-")))
        pagador = html.escape(str(pago.get("detalle_pagador", "-")))
        beneficiario = html.escape(
            str(pago.get("beneficiario_nombre", "Turismo Mágico"))
        )
        cuenta = html.escape(str(pago.get("beneficiario_cuenta", "-")))
        metodo = html.escape(str(pago.get("metodo_nombre", "-")))
        fecha = html.escape(str(pago.get("fecha_aprobacion", "-")))
        token = str(pago.get("token", ""))
        verificacion = html.escape(
            token[-10:] if token else codigo.replace("MRV-", "")
        )
        monto = float(pago.get("monto", 0) or 0)
        monto_texto = f"$ {monto:,.0f} COP"

        elementos = []

        cabecera = Table(
            [[
                Paragraph("MAREVA", estilo_marca),
                Paragraph("TURISMO MÁGICO · PAGO SEGURO", estilo_marca_secundaria),
            ]],
            colWidths=[80 * mm, 80 * mm],
        )
        cabecera.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), MOR_ADO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LEFTPADDING", (0, 0), (-1, -1), 16),
            ("RIGHTPADDING", (0, 0), (-1, -1), 16),
            ("LINEBELOW", (0, 0), (-1, -1), 3, TURQUESA),
        ]))
        elementos.append(cabecera)
        elementos.append(Spacer(1, 16))

        titulo = Table(
            [[
                Paragraph("COMPROBANTE DE PAGO", estilo_titulo),
                Paragraph("PAGADO", estilo_estado),
            ]],
            colWidths=[125 * mm, 35 * mm],
        )
        titulo.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#0f8f62")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ]))
        elementos.append(titulo)
        elementos.append(Spacer(1, 12))

        heroe = Table(
            [[
                Paragraph("VALOR PAGADO", estilo_etiqueta),
            ], [
                Paragraph(monto_texto, estilo_monto),
            ], [
                Paragraph(
                    f"Pago realizado por {pagador} por un valor de {monto_texto}",
                    estilo_frase,
                ),
            ]],
            colWidths=[160 * mm],
        )
        heroe.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), ARENA),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#eadfc7")),
            ("LINEBEFORE", (0, 0), (0, -1), 4, TURQUESA),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
            ("TOPPADDING", (0, 1), (-1, 1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ]))
        elementos.append(heroe)
        elementos.append(Spacer(1, 18))

        elementos.append(Paragraph("Detalles de la transacción", estilo_seccion))
        detalles = [
            ["Estado", Paragraph("PAGADO", estilo_celda)],
            ["Código de reserva", Paragraph(codigo, estilo_celda)],
            ["Fecha del pago", Paragraph(fecha, estilo_celda)],
            ["Método de pago", Paragraph(metodo, estilo_celda)],
            ["Pagador", Paragraph(pagador, estilo_celda)],
            ["Código de verificación", Paragraph(verificacion, estilo_celda)],
        ]
        tabla_detalles = Table(detalles, colWidths=[52 * mm, 108 * mm])
        tabla_detalles.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("TEXTCOLOR", (0, 0), (0, -1), MOR_ADO),
            ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [GRIS_CLARO, colors.white]),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e5ecea")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5ecea")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elementos.append(tabla_detalles)
        elementos.append(Spacer(1, 16))

        elementos.append(Paragraph("Beneficiario", estilo_seccion))
        beneficiario_tabla = Table(
            [
                ["Nombre", Paragraph(beneficiario, estilo_celda)],
                ["Cuenta de destino", Paragraph(cuenta, estilo_celda)],
                ["Valor acreditado", Paragraph(monto_texto, estilo_celda)],
            ],
            colWidths=[52 * mm, 108 * mm],
        )
        beneficiario_tabla.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("TEXTCOLOR", (0, 0), (0, -1), MOR_ADO),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e5ecea")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5ecea")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elementos.append(beneficiario_tabla)
        elementos.append(Spacer(1, 14))

        elementos.append(HRFlowable(
            width="100%",
            thickness=0.8,
            color=colors.HexColor("#dfe6e4"),
            spaceAfter=8,
        ))
        elementos.append(Paragraph(
            "Este comprobante acredita la confirmación del pago realizado a Turismo Mágico. "
            "MAREVA no recibe pagos directamente ni actúa como entidad financiera.",
            estilo_pie,
        ))
        elementos.append(Spacer(1, 4))
        elementos.append(Paragraph(
            f"Reserva {codigo} · Verificación {verificacion} · "
            "Documento generado automáticamente, no requiere firma.",
            estilo_pie,
        ))

        doc.build(
            elementos,
            onFirstPage=self._pie_comprobante,
            onLaterPages=self._pie_comprobante,
        )
        buffer.seek(0)
        return buffer
