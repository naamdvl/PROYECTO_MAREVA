document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formConfirmarReserva");
    const adultos = document.getElementById("inputAdultos");
    const menores = document.getElementById("inputMenores");
    const bebes = document.getElementById("inputBebes");
    const viajerosContainer = document.getElementById("viajerosContainer");
    const resumenViajeros = document.getElementById("resumenViajeros");
    const alertaBebesAmazonas = document.getElementById("alertaBebesAmazonas");
    const alertaEdadViajeros = document.getElementById("alertaEdadViajeros");
    const destinoAmazonas = window.MAREVA_DESTINO_AMAZONAS === true;

    if (!form) return;

    // ---------- Constructor de viajeros ----------

    const TIPOS_DOC = {
        adulto: ["CC", "CE", "Pasaporte"],
        menor: ["TI", "RC", "Pasaporte"],
        bebe: ["RC", "Pasaporte"],
    };

    function esc(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, carc => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        })[carc]);
    }

    function categoriaViajero(indice) {
        const cantidadAdultos = Number(adultos?.value || 1);
        const cantidadMenores = Number(menores?.value || 0);
        if (indice < cantidadAdultos) return "adulto";
        if (indice < cantidadAdultos + cantidadMenores) return "menor";
        return "bebe";
    }

    function documentoValido(tipo, documento) {
        const valor = String(documento || "").trim();
        if (tipo === "CC" || tipo === "TI") return /^\d{6,12}$/.test(valor);
        if (tipo === "CE") return /^[A-Za-z0-9]{6,12}$/.test(valor);
        if (tipo === "RC") return /^[A-Za-z0-9-]{5,15}$/.test(valor);
        if (tipo === "Pasaporte") return /^[A-Za-z0-9]{5,20}$/.test(valor);
        return false;
    }

    function validarViajerosEnVivo() {
        const avisos = [];

        if (destinoAmazonas && Number(bebes?.value || 0) > 0) {
            avisos.push("En Amazonas no se permiten bebés. Retira los bebés para continuar.");
        }

        [...viajerosContainer.querySelectorAll(".traveler-form")].forEach((tarjeta, i) => {
            const tipo = tarjeta.querySelector('[name="viajero_tipo_documento[]"]')?.value || "";
            const documento = tarjeta.querySelector('[name="viajero_documento[]"]')?.value || "";
            const categoria = categoriaViajero(i);
            const permitidos = TIPOS_DOC[categoria];

            if (tipo && !permitidos.includes(tipo)) {
                avisos.push(`El viajero ${i + 1} es ${categoria} y debe usar ${permitidos.join(" o ")}.`);
            }
            if (documento && !documentoValido(tipo, documento)) {
                avisos.push(`El documento del viajero ${i + 1} no tiene un formato válido.`);
            }

            if (categoria === "menor") {
                const edad = Number(tarjeta.querySelector('[name="viajero_edad[]"]')?.value);
                if (tarjeta.querySelector('[name="viajero_edad[]"]')?.value && (!Number.isInteger(edad) || edad < 2 || edad > 17)) {
                    avisos.push(`Los niños van de 2 a 17 años; desde 24 meses dejan de ser bebés.`);
                }
            }

            if (categoria === "bebe") {
                const campoMeses = tarjeta.querySelector('[name="viajero_meses[]"]');
                const meses = Number(campoMeses?.value || 0);
                if (campoMeses?.value && (!Number.isInteger(meses) || meses < 0 || meses > 23)) {
                    avisos.push(`Desde los 24 meses deja de ser bebé: cambia a niño o corrige los meses (0 a 23).`);
                }
            }
        });

        return avisos;
    }

    function actualizarAlertaEdades() {
        if (!alertaEdadViajeros) return;
        const avisos = validarViajerosEnVivo().filter(mensaje =>
            /beb|niño|años|meses/i.test(mensaje)
        );
        alertaEdadViajeros.textContent = avisos.join(" ");
        alertaEdadViajeros.hidden = avisos.length === 0;
    }

    function renderTravelers() {
        if (!viajerosContainer) return;

        const cantidadAdultos = Number(adultos?.value || 1);
        const cantidadMenores = Number(menores?.value || 0);
        const cantidadBebes = Number(bebes?.value || 0);
        const totalPersonas = cantidadAdultos + cantidadMenores + cantidadBebes;

        if (resumenViajeros) {
            resumenViajeros.textContent = totalPersonas;
        }
        if (alertaBebesAmazonas) {
            alertaBebesAmazonas.hidden = !(destinoAmazonas && cantidadBebes > 0);
        }

        // Conserva lo ya diligenciado al cambiar el número de viajeros.
        const anteriores = [...viajerosContainer.querySelectorAll(".traveler-form")]
            .map(box => ({
                nombre: box.querySelector('[name="viajero_nombre[]"]')?.value || "",
                apellido: box.querySelector('[name="viajero_apellido[]"]')?.value || "",
                tipo: box.querySelector('[name="viajero_tipo_documento[]"]')?.value || "",
                documento: box.querySelector('[name="viajero_documento[]"]')?.value || "",
                idioma: box.querySelector('[name="viajero_idioma[]"]')?.value || "Español",
                edad: box.querySelector('[name="viajero_edad[]"]')?.value || "",
                meses: box.querySelector('[name="viajero_meses[]"]')?.value || "",
            }));

        viajerosContainer.innerHTML = "";

        for (let i = 0; i < totalPersonas; i++) {
            const categoria = categoriaViajero(i);
            const etiqueta = categoria === "adulto"
                ? "Adulto"
                : categoria === "menor"
                    ? "Menor"
                    : "Bebé";
            const guardado = anteriores[i] || {};
            const n = i + 1;
            const tipos = TIPOS_DOC[categoria];
            const idiomas = ["Español", "Inglés", "Portugués", "Francés"];

            const box = document.createElement("div");
            box.className = "traveler-form";

            box.innerHTML = `
                <div class="traveler-form__title">
                    <strong>Viajero ${n}</strong>
                    <span>${etiqueta}</span>
                </div>

                <div class="form-grid">
                    <div>
                        <label class="form-label">Nombre</label>
                        <input class="form-input" name="viajero_nombre[]" required
                               autocomplete="given-name" value="${esc(guardado.nombre)}">
                    </div>
                    <div>
                        <label class="form-label">Apellido</label>
                        <input class="form-input" name="viajero_apellido[]" required
                               autocomplete="family-name" value="${esc(guardado.apellido)}">
                    </div>
                    <div>
                        <label class="form-label">Tipo de documento</label>
                        <select class="form-select" name="viajero_tipo_documento[]" required>
                            <option value="">Selecciona</option>
                            ${tipos.map(valor => `<option value="${valor}"
                                ${guardado.tipo === valor ? "selected" : ""}>${valor}</option>`).join("")}
                        </select>
                    </div>
                    <div>
                        <label class="form-label">Número de documento</label>
                        <input class="form-input" name="viajero_documento[]" required
                               value="${esc(guardado.documento)}">
                    </div>
                    <div>
                        <label class="form-label">Idioma preferido</label>
                        <select class="form-select" name="viajero_idioma[]" required>
                            ${idiomas.map(valor => `<option value="${valor}"
                                ${guardado.idioma === valor ? "selected" : ""}>${valor}</option>`).join("")}
                        </select>
                    </div>
                    ${categoria === "menor" ? `
                    <div>
                        <label class="form-label">Edad</label>
                        <input type="number" class="form-input" name="viajero_edad[]"
                               min="2" max="17" required value="${esc(guardado.edad)}">
                    </div>` : ""}
                    ${categoria === "bebe" ? `
                    <div>
                        <label class="form-label">Meses de edad</label>
                        <input type="number" class="form-input" name="viajero_meses[]"
                               min="0" max="23" required value="${esc(guardado.meses)}">
                    </div>` : ""}
                </div>
            `;

            viajerosContainer.appendChild(box);
        }
    }

    adultos?.addEventListener("change", renderTravelers);
    menores?.addEventListener("change", renderTravelers);
    bebes?.addEventListener("change", renderTravelers);

    form.addEventListener("input", actualizarAlertaEdades);
    form.addEventListener("change", actualizarAlertaEdades);

    // ---------- Cambio de fecha ----------

    const cambiaFechaPanel = document.getElementById("cambiarFecha");
    const botonCambiaFecha = document.querySelector("[onclick='toggleFecha(this)']");

    window.toggleFecha = function (boton) {
        if (!cambiaFechaPanel) return;
        cambiaFechaPanel.hidden = !cambiaFechaPanel.hidden;
        if (!cambiaFechaPanel.hidden) {
            cambiaFechaPanel.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    };

    window.aplicarFecha = function () {
        if (!cambiaFechaPanel) return;

        const elegida = cambiaFechaPanel.querySelector('input[name="id_salida_alt"]:checked');
        if (!elegida) return;

        const oculto = form.querySelector('input[name="id_salida"]');
        if (oculto) oculto.value = elegida.value;

        const rotulo = elegida.closest(".pick-date");
        const texto = rotulo ? rotulo.querySelector("strong").textContent : "Actualizada";

        const itemFecha = form.querySelector(".confirm-card .sel-item");
        if (itemFecha) {
            const strong = itemFecha.querySelector(".sel-item__body strong");
            if (strong) strong.textContent = texto;
        }

        cambiaFechaPanel.hidden = true;
    };

    // ---------- Validación al enviar ----------

    form.addEventListener("submit", event => {
        const idSalida = form.querySelector('input[name="id_salida"]')?.value;
        const alojamiento = form.querySelector('input[name="alojamiento"]:checked');

        if (!idSalida) {
            event.preventDefault();
            alert("Debes elegir una fecha de salida.");
            return;
        }

        if (!alojamiento) {
            event.preventDefault();
            alert("Debes elegir un alojamiento.");
            return;
        }

        const cantidadBebes = Number(bebes?.value || 0);
        const personas = Number(adultos?.value || 1)
            + Number(menores?.value || 0)
            + cantidadBebes;

        if (personas < 1) {
            event.preventDefault();
            alert("Debes ingresar al menos un viajero.");
            return;
        }

        const avisos = validarViajerosEnVivo();
        if (avisos.length) {
            event.preventDefault();
            actualizarAlertaEdades();
            alert(avisos[0]);
        }
    });

    // ---------- Desglose de precio dinámico ----------

    const precioBaseEl = document.getElementById("precioBase");
    const precioTotalEl = document.getElementById("precioTotal");
    const precioAdicionalesEl = document.getElementById("precioAdicionales");
    const precioFinalEl = document.getElementById("precioFinal");
    const adicionalesDetalle = document.getElementById("adicionalesDetalle");
    const cantidadViajerosEl = document.getElementById("cantidadViajeros");
    const stickyTotal = document.getElementById("stickyTotal");
    const stickyViajeros = document.getElementById("stickyViajeros");
    const stickyBase = document.getElementById("stickyBase");
    const stickyItems = document.getElementById("stickyItems");
    const stickyAdicionales = document.getElementById("stickyAdicionales");
    const stickyPorPersona = document.getElementById("stickyPorPersona");
    const stickyToggle = document.getElementById("stickyToggle");
    const stickyDetail = document.getElementById("stickyDetail");
    const precioBase = parseFloat(precioBaseEl?.dataset.base || precioTotalEl?.dataset.base) || 0;

    function formatearPrecio(valor) {
        return "$" + Math.round(valor).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function actualizarPrecioTotal() {
        const items = Array.from(
            document.querySelectorAll(
                'input[name="alimentacion"]:checked, ' +
                'input[name="transporte"]:checked, ' +
                'input[name="actividades"]:checked, ' +
                'input[name="seguros"]:checked, ' +
                'input[name="extras"]:checked'
            )
        ).map(cb => ({
            nombre: cb.dataset.nombre
                || cb.closest("label")?.querySelector("h3")?.textContent.trim()
                || "Servicio adicional",
            precio: parseFloat(cb.dataset.precio) || 0,
        }));

        const filasItems = items.map(item => {
            const fila = document.createElement("div");
            fila.className = "price-breakdown__line";
            const nombre = document.createElement("span");
            nombre.textContent = item.nombre;
            const valor = document.createElement("strong");
            valor.textContent = "+" + formatearPrecio(item.precio);
            fila.append(nombre, valor);
            return fila;
        });

        if (adicionalesDetalle) {
            adicionalesDetalle.replaceChildren(...filasItems);
        }
        if (stickyItems) {
            stickyItems.replaceChildren(...filasItems.map(fila => fila.cloneNode(true)));
        }

        const adicionales = items.reduce((suma, item) => suma + item.precio, 0);
        const porPersona = precioBase + adicionales;
        const adultos = Number(document.querySelector('[name="adultos"]')?.value || 1);
        const menores = Number(document.querySelector('[name="menores"]')?.value || 0);
        const bebes = Number(document.querySelector('[name="bebes"]')?.value || 0);
        const viajeros = adultos + menores + bebes;
        const pagantes = Math.max(adultos + menores, 1);

        if (precioAdicionalesEl) {
            precioAdicionalesEl.textContent = formatearPrecio(adicionales);
        }
        if (precioTotalEl) {
            precioTotalEl.textContent = formatearPrecio(porPersona);
        }
        if (cantidadViajerosEl) {
            cantidadViajerosEl.textContent = viajeros;
        }
        if (precioFinalEl) {
            precioFinalEl.textContent = formatearPrecio(porPersona * pagantes);
        }
        if (stickyTotal) {
            stickyTotal.textContent = formatearPrecio(porPersona * pagantes);
        }
        if (stickyViajeros) {
            stickyViajeros.textContent = viajeros;
        }
        if (stickyBase) {
            stickyBase.textContent = formatearPrecio(precioBase);
        }
        if (stickyAdicionales) {
            stickyAdicionales.textContent = formatearPrecio(adicionales);
        }
        if (stickyPorPersona) {
            stickyPorPersona.textContent = formatearPrecio(porPersona);
        }
    }

    document.querySelectorAll(
        'input[name="alimentacion"], input[name="transporte"], ' +
        'input[name="actividades"], input[name="seguros"], input[name="extras"], ' +
        '[name="adultos"], [name="menores"], [name="bebes"]'
    ).forEach(elemento => {
        elemento.addEventListener("change", actualizarPrecioTotal);
        elemento.addEventListener("input", actualizarPrecioTotal);
    });

    stickyToggle?.addEventListener("click", () => {
        if (!stickyDetail) return;

        const abierto = !stickyDetail.hidden;
        stickyDetail.hidden = abierto;
        stickyToggle.setAttribute("aria-expanded", String(!abierto));
        stickyToggle.textContent = abierto ? "Ver desglose" : "Ocultar desglose";
    });

    actualizarPrecioTotal();

    renderTravelers();
    actualizarAlertaEdades();
});