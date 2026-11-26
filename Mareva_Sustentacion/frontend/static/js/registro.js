function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const mostrar = input.type === "password";
    input.type = mostrar ? "text" : "password";

    if (button) {
        button.setAttribute(
            "aria-label",
            mostrar ? "Ocultar contraseña" : "Mostrar contraseña"
        );
        button.textContent = mostrar ? "🙈" : "👁";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    let ultimoElementoActivo = null;

    document.querySelectorAll("[data-open-dialog]").forEach((boton) => {
        boton.addEventListener("click", () => {
            const dialogId = boton.dataset.openDialog;
            const dialogo = document.getElementById(dialogId);

            if (!dialogo || typeof dialogo.showModal !== "function") return;

            document.querySelectorAll(".legal-dialog[open]").forEach((abierto) => {
                if (abierto !== dialogo) abierto.close();
            });

            ultimoElementoActivo = boton;
            if (!dialogo.open) dialogo.showModal();
        });
    });

    document.querySelectorAll(".legal-dialog").forEach((dialogo) => {
        dialogo.querySelectorAll("[data-close-dialog]").forEach((boton) => {
            boton.addEventListener("click", () => {
                if (dialogo.open) dialogo.close();
            });
        });

        dialogo.addEventListener("click", (evento) => {
            if (evento.target === dialogo && dialogo.open) dialogo.close();
        });

        dialogo.addEventListener("close", () => {
            if (ultimoElementoActivo && ultimoElementoActivo.isConnected) {
                ultimoElementoActivo.focus();
            }
        });
    });

    const form = document.getElementById("registroForm");
    if (!form) return;

    function obtenerCampo(id) {
        return document.getElementById(id);
    }

    function mostrarError(campo, mensaje) {
        if (!campo) return;

        campo.classList.add("invalid");
        campo.setAttribute("aria-invalid", "true");

        const error = obtenerCampo("error-" + campo.id);
        if (error) {
            error.textContent = mensaje;
            error.classList.add("visible");
            error.style.display = "block";
        }
    }

    function limpiarError(campo) {
        if (!campo) return;

        campo.classList.remove("invalid");
        campo.removeAttribute("aria-invalid");

        const error = obtenerCampo("error-" + campo.id);
        if (error) {
            error.textContent = "";
            error.classList.remove("visible");
            error.style.display = "none";
        }
    }

    const campos = [
        "nombre",
        "apellido",
        "tipo",
        "numero",
        "telefono",
        "correo",
        "codigo",
        "registroPassword",
        "confirmPassword"
    ];

    const nombre = obtenerCampo("nombre");
    const apellido = obtenerCampo("apellido");
    const tipo = obtenerCampo("tipo");
    const numero = obtenerCampo("numero");
    const telefono = obtenerCampo("telefono");
    const codigoPais = obtenerCampo("codigoPais");
    const telefonoCompleto = obtenerCampo("telefono_completo");
    const correo = obtenerCampo("correo");
    const codigoReferido = obtenerCampo("codigo");
    const password = obtenerCampo("registroPassword");
    const confirmarPassword = obtenerCampo("confirmPassword");
    const terminos = obtenerCampo("terminos");
    const politica = obtenerCampo("politica_no_reembolso");

    const esGoogle = Boolean(correo && correo.readOnly);
    const bloqueVerificacion = obtenerCampo("verificacionCorreo");
    const marcaVerificado = obtenerCampo("correoVerificado");
    const estadoVerificacion = obtenerCampo("estadoVerificacion");
    const enviarCodigoBtn = obtenerCampo("enviarCodigoBtn");
    const verificarCodigoBtn = obtenerCampo("verificarCodigoBtn");
    const codigoVerificacion = obtenerCampo("codigoVerificacion");
    const reenviarBtn = obtenerCampo("reenviarConfirmacionBtn");
    let temporizadorReenvio = null;
    let correoVerificadoValor = correo?.value.trim() || "";

    const correoValido = (valor) =>
        /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(valor.trim());

    function actualizarTelefonoCompleto() {
        if (!telefono || !telefonoCompleto) return "";

        const indicativo = codigoPais?.value || "+57";
        const numero = telefono.value.replace(/\D/g, "");
        telefonoCompleto.value = numero ? indicativo + numero : "";
        return numero;
    }

    function mensajeValidacion(id) {
        const valor = obtenerCampo(id)?.value.trim() || "";

        if (id === "nombre") {
            if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$/.test(valor)) {
                return "Solo letras y espacios, entre 2 y 50 caracteres.";
            }
        }

        if (id === "apellido") {
            if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$/.test(valor)) {
                return "Solo letras y espacios, entre 2 y 50 caracteres.";
            }
        }

        if (id === "tipo") {
            if (!valor) return "Selecciona un tipo de documento.";
        }

        if (id === "numero") {
            const reglas = {
                CC: /^\d{6,10}$/,
                TI: /^\d{10}$/,
                CE: /^\d{6,7}$/,
                PA: /^[A-Za-z0-9]{6,12}$/
            };
            const tipoSeleccionado = tipo?.value || "";
            if (tipoSeleccionado in reglas && !reglas[tipoSeleccionado].test(valor)) {
                return "El número de documento no es válido para ese tipo.";
            }
        }

        if (id === "telefono") {
            const texto = obtenerCampo("telefono")?.value || "";
            const soloDigitos = texto.replace(/\D/g, "");
            if (/[A-Za-zÁÉÍÓÚáéíóúÑñ]/.test(texto)) {
                return "El teléfono solo puede contener números.";
            }
            if (soloDigitos.length < 6 || soloDigitos.length > 15) {
                return "Ingresa entre 6 y 15 dígitos, sin el indicativo.";
            }
        }

        if (id === "correo") {
            if (!correoValido(valor)) return "Ingresa un correo electrónico válido.";
        }

        if (id === "codigo") {
            if (valor && !/^[A-Za-z0-9]{1,20}$/.test(valor)) {
                return "El código de referido solo permite letras y números.";
            }
        }

        if (id === "registroPassword") {
            if (valor.length < 8) return "Mínimo 8 caracteres.";
            if (!/[A-ZÁÉÍÓÚÑ]/.test(valor)) return "Debe incluir una mayúscula.";
            if (!/\d/.test(valor)) return "Debe incluir un número.";
            if (!/[^A-Za-z0-9]/.test(valor)) return "Debe incluir un carácter especial.";
        }

        if (id === "confirmPassword") {
            if (!valor) return "Confirma tu contraseña.";
            if (password && valor !== password.value) {
                return "Las contraseñas no coinciden.";
            }
        }

        return "";
    }

    function validarCampo(id, mostrarSiempre = false) {
        const campo = obtenerCampo(id);
        if (!campo) return true;

        const mensaje = mensajeValidacion(id);

        if (mensaje) {
            if (mostrarSiempre || campo.value.trim()) {
                mostrarError(campo, mensaje);
            }
            return false;
        }

        limpiarError(campo);
        return true;
    }

    function establecerEstado(mensaje, tipo = "") {
        if (!estadoVerificacion) return;

        estadoVerificacion.textContent = mensaje;
        estadoVerificacion.classList.remove("es-error", "es-ok");
        if (tipo) estadoVerificacion.classList.add("es-" + tipo);
    }

    function detenerContador() {
        if (temporizadorReenvio) {
            clearInterval(temporizadorReenvio);
            temporizadorReenvio = null;
        }
    }

    function restablecerVerificacion(mensaje) {
        detenerContador();
        if (marcaVerificado) marcaVerificado.value = "0";
        if (bloqueVerificacion) {
            bloqueVerificacion.dataset.estado = "pendiente";
            bloqueVerificacion.classList.remove("verificacion-correo--ok");
        }
        if (codigoVerificacion) {
            codigoVerificacion.hidden = false;
            codigoVerificacion.disabled = false;
            codigoVerificacion.value = "";
        }
        if (enviarCodigoBtn) {
            enviarCodigoBtn.hidden = false;
            enviarCodigoBtn.disabled = false;
            enviarCodigoBtn.textContent = "Enviar código";
        }
        if (verificarCodigoBtn) {
            verificarCodigoBtn.hidden = false;
            verificarCodigoBtn.disabled = true;
        }
        if (reenviarBtn) reenviarBtn.hidden = true;
        establecerEstado(mensaje || "Ingresa un correo válido para verificarlo.", "error");
    }

    function aplicarEstadoVerificado(mensaje, actualizarMensaje = true) {
        detenerContador();
        if (marcaVerificado) marcaVerificado.value = "1";
        if (bloqueVerificacion) {
            bloqueVerificacion.dataset.estado = "verificado";
            bloqueVerificacion.classList.add("verificacion-correo--ok");
        }
        if (enviarCodigoBtn) enviarCodigoBtn.hidden = true;
        if (codigoVerificacion) codigoVerificacion.hidden = true;
        if (verificarCodigoBtn) verificarCodigoBtn.hidden = true;
        if (reenviarBtn) reenviarBtn.hidden = false;
        if (actualizarMensaje) {
            establecerEstado(mensaje || "Tu correo quedó verificado. Puedes continuar.", "ok");
        }
    }

    function actualizarVerificacion() {
        if (esGoogle || !bloqueVerificacion || !correo) return;

        const valido = validarCampo("correo", false);
        bloqueVerificacion.style.display = valido ? "flex" : "none";

        if (!valido && bloqueVerificacion.dataset.estado !== "verificado") {
            restablecerVerificacion("Ingresa un correo válido para verificarlo.");
        }
    }

    function iniciarContador() {
        if (!enviarCodigoBtn || esGoogle) return;

        detenerContador();
        let segundos = 60;
        enviarCodigoBtn.disabled = true;
        enviarCodigoBtn.textContent = `Reenviar en ${segundos}s`;

        temporizadorReenvio = setInterval(() => {
            segundos -= 1;
            if (segundos <= 0) {
                detenerContador();
                enviarCodigoBtn.disabled = false;
                enviarCodigoBtn.textContent = "Enviar código";
                return;
            }
            enviarCodigoBtn.textContent = `Reenviar en ${segundos}s`;
        }, 1000);
    }

    async function enviarCodigo() {
        if (!validarCampo("correo", true)) {
            actualizarVerificacion();
            return;
        }

        detenerContador();
        if (enviarCodigoBtn) {
            enviarCodigoBtn.disabled = true;
            enviarCodigoBtn.textContent = "Enviando...";
        }

        try {
            const respuesta = await fetch("/auth/verificar-correo/enviar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ correo: correo.value.trim() })
            });
            const datos = await respuesta.json();

            if (!respuesta.ok || !datos.ok) {
                establecerEstado(datos.error || "No fue posible enviar el código.", "error");
                if (enviarCodigoBtn) {
                    enviarCodigoBtn.disabled = false;
                    enviarCodigoBtn.textContent = "Enviar código";
                }
                return;
            }

            if (datos.verificado) {
                aplicarEstadoVerificado(datos.mensaje);
                return;
            }

            if (verificarCodigoBtn) verificarCodigoBtn.disabled = false;
            if (codigoVerificacion) codigoVerificacion.disabled = false;
            establecerEstado(datos.mensaje || "Código enviado. Revisa tu correo.", "ok");
            iniciarContador();
        } catch (error) {
            establecerEstado("No fue posible conectar con el servidor.", "error");
            if (enviarCodigoBtn) {
                enviarCodigoBtn.disabled = false;
                enviarCodigoBtn.textContent = "Enviar código";
            }
        }
    }

    async function verificarCodigo() {
        const valor = codigoVerificacion?.value.trim() || "";

        if (!/^\d{6}$/.test(valor)) {
            establecerEstado("El código debe tener 6 dígitos.", "error");
            return;
        }

        if (verificarCodigoBtn) verificarCodigoBtn.disabled = true;

        try {
            const respuesta = await fetch("/auth/verificar-correo/confirmar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ codigo: valor })
            });
            const datos = await respuesta.json();

            if (!respuesta.ok || !datos.ok) {
                establecerEstado(datos.error || "El código no es correcto.", "error");
                if (verificarCodigoBtn) verificarCodigoBtn.disabled = false;
                return;
            }

            aplicarEstadoVerificado(datos.mensaje || "Correo verificado correctamente.");
        } catch (error) {
            establecerEstado("No fue posible conectar con el servidor.", "error");
            if (verificarCodigoBtn) verificarCodigoBtn.disabled = false;
        }
    }

    campos.forEach((id) => {
        const campo = obtenerCampo(id);
        if (!campo) return;

        campo.addEventListener("input", () => {
            if (id === "telefono") actualizarTelefonoCompleto();
            validarCampo(id, false);

            if (id === "correo") {
                const correoActual = correo.value.trim();

                if (
                    marcaVerificado &&
                    marcaVerificado.value === "1" &&
                    correoActual !== correoVerificadoValor
                ) {
                    restablecerVerificacion("El correo cambió; vuelve a verificarlo.");
                }

                correoVerificadoValor = correoActual;
                actualizarVerificacion();
            }
            if (id === "password" && confirmarPassword && confirmarPassword.value) {
                validarCampo("confirmPassword", true);
            }
        });

        campo.addEventListener("blur", () => {
            if (id === "telefono") actualizarTelefonoCompleto();
            validarCampo(id, true);
        });
    });

    if (tipo) {
        tipo.addEventListener("change", () => {
            if (numero && numero.value) validarCampo("numero", true);
        });
    }

    if (enviarCodigoBtn) enviarCodigoBtn.addEventListener("click", enviarCodigo);
    if (verificarCodigoBtn) verificarCodigoBtn.addEventListener("click", verificarCodigo);
    if (reenviarBtn) reenviarBtn.addEventListener("click", enviarCodigo);

    if (!esGoogle && marcaVerificado && marcaVerificado.value === "1") {
        aplicarEstadoVerificado("Tu correo quedó verificado. Puedes continuar.", false);
    }

    actualizarTelefonoCompleto();
    actualizarVerificacion();

    function validarConsentimiento(campo, mensaje) {
        if (!campo) return true;

        const error = obtenerCampo("error-" + campo.id);
        if (!campo.checked) {
            if (error) {
                error.textContent = mensaje;
                error.classList.add("visible");
                error.style.display = "block";
            }
            campo.setAttribute("aria-invalid", "true");
            return false;
        }

        if (error) {
            error.textContent = "";
            error.classList.remove("visible");
            error.style.display = "none";
        }
        campo.removeAttribute("aria-invalid");
        return true;
    }

    if (terminos) {
        terminos.addEventListener("change", () => {
            validarConsentimiento(
                terminos,
                "Debes aceptar los Términos y Condiciones para continuar."
            );
        });
    }

    if (politica) {
        politica.addEventListener("change", () => {
            validarConsentimiento(
                politica,
                "Debes aceptar la Política de No Reembolso para continuar."
            );
        });
    }

    form.addEventListener("submit", (evento) => {
        let formularioValido = true;

        actualizarTelefonoCompleto();

        campos.forEach((id) => {
            if (!validarCampo(id, true)) formularioValido = false;
        });

        if (
            !validarConsentimiento(
                terminos,
                "Debes aceptar los Términos y Condiciones."
            )
        ) {
            formularioValido = false;
        }

        if (
            !validarConsentimiento(
                politica,
                "Debes aceptar la Política de No Reembolso."
            )
        ) {
            formularioValido = false;
        }

        if (!esGoogle && marcaVerificado && marcaVerificado.value !== "1") {
            formularioValido = false;
            establecerEstado("Verifica tu correo antes de crear la cuenta.", "error");
            if (bloqueVerificacion) {
                bloqueVerificacion.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        }

        if (!formularioValido) {
            evento.preventDefault();

            const primerError = form.querySelector(
                ".invalid, input:invalid, select:invalid"
            );

            if (primerError) {
                primerError.focus();
                primerError.scrollIntoView({ behavior: "smooth", block: "center" });
            } else if (terminos && !terminos.checked) {
                terminos.focus();
            } else if (politica && !politica.checked) {
                politica.focus();
            }
        }
    });
});
