document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("formPago");
  if (!form) return;

  const radios = Array.from(form.querySelectorAll("input[name='metodo_pago']"));
  const sections = Array.from(form.querySelectorAll(".payment-form-section"));
  const boton = document.getElementById("btnPagar");

  const nequi = document.getElementById("nequiTelefono");
  const pseBanco = document.getElementById("pseBanco");
  const pseTipo = document.getElementById("pseTipoDocumento");
  const pseDocumento = document.getElementById("pseDocumento");
  const tarjetaTipo = document.getElementById("tarjetaTipo");
  const tarjetaNumero = document.getElementById("tarjetaNumero");
  const tarjetaTitular = document.getElementById("tarjetaTitular");
  const tarjetaVencimiento = document.getElementById("tarjetaVencimiento");
  const tarjetaCvv = document.getElementById("tarjetaCvv");

  const previewNumber = document.getElementById("cardPreviewNumber");
  const previewName = document.getElementById("cardPreviewName");
  const previewExpiry = document.getElementById("cardPreviewExpiry");
  const previewType = document.getElementById("cardPreviewType");

  const soloDigitos = (valor) => valor.replace(/\D/g, "");

  const metodoSeleccionado = () => {
    const activo = radios.find((radio) => radio.checked);
    return activo ? activo.value : null;
  };

  const limpiarErrores = () => {
    form.querySelectorAll(".field-error").forEach((nodo) => {
      nodo.textContent = "";
    });
    form.querySelectorAll(".input-invalid").forEach((nodo) => {
      nodo.classList.remove("input-invalid");
    });
  };

  const marcarError = (input, idError, mensaje) => {
    const error = document.getElementById(idError);
    if (error) error.textContent = mensaje;
    if (input) input.classList.add("input-invalid");
  };

  const actualizarVista = () => {
    const metodo = metodoSeleccionado();
    sections.forEach((seccion) => {
      seccion.classList.toggle("is-active", seccion.dataset.metodo === metodo);
    });
    if (boton) boton.disabled = !metodo;
  };

  radios.forEach((radio) => {
    radio.addEventListener("change", actualizarVista);
  });
  actualizarVista();

  if (nequi) {
    nequi.addEventListener("input", () => {
      nequi.value = soloDigitos(nequi.value).slice(0, 10);
    });
  }

  if (pseDocumento) {
    pseDocumento.addEventListener("input", () => {
      pseDocumento.value = soloDigitos(pseDocumento.value).slice(0, 12);
    });
  }

  if (tarjetaNumero) {
    tarjetaNumero.addEventListener("input", () => {
      const digitos = soloDigitos(tarjetaNumero.value).slice(0, 16);
      tarjetaNumero.value = digitos.replace(/(.{4})/g, "$1 ").trim();
      if (previewNumber) {
        previewNumber.textContent = digitos
          ? digitos.replace(/(.{4})/g, "$1 ").trim()
          : "•••• •••• •••• ••••";
      }
    });
  }

  if (tarjetaTitular) {
    tarjetaTitular.addEventListener("input", () => {
      if (previewName) {
        previewName.textContent =
          tarjetaTitular.value.trim().toUpperCase() || "NOMBRE DEL TITULAR";
      }
    });
  }

  if (tarjetaVencimiento) {
    tarjetaVencimiento.addEventListener("input", () => {
      const digitos = soloDigitos(tarjetaVencimiento.value).slice(0, 4);
      tarjetaVencimiento.value =
        digitos.length > 2 ? `${digitos.slice(0, 2)}/${digitos.slice(2)}` : digitos;
      if (previewExpiry) {
        previewExpiry.textContent = tarjetaVencimiento.value || "MM/AA";
      }
    });
  }

  if (tarjetaCvv) {
    tarjetaCvv.addEventListener("input", () => {
      tarjetaCvv.value = soloDigitos(tarjetaCvv.value).slice(0, 4);
    });
  }

  if (tarjetaTipo) {
    tarjetaTipo.addEventListener("change", () => {
      if (previewType) {
        previewType.textContent =
          tarjetaTipo.value === "credito"
            ? "CRÉDITO"
            : tarjetaTipo.value === "debito"
              ? "DÉBITO"
              : "TARJETA";
      }
    });
  }

  const validar = () => {
    const metodo = metodoSeleccionado();
    let primeroInvalido = null;

    if (!metodo) {
      marcarError(null, "error-metodo", "Selecciona un método de pago.");
      return false;
    }

    if (metodo === "nequi") {
      const valor = nequi ? soloDigitos(nequi.value) : "";
      let telefono = valor;
      if (telefono.startsWith("57") && telefono.length === 12) {
        telefono = telefono.slice(2);
      }
      if (telefono.length !== 10 || !telefono.startsWith("3")) {
        marcarError(
          nequi,
          "error-nequi-telefono",
          "Ingresa un celular colombiano válido de 10 dígitos."
        );
        primeroInvalido = nequi;
      }
    }

    if (metodo === "pse") {
      if (!pseBanco || !pseBanco.value) {
        marcarError(pseBanco, "error-pse-banco", "Selecciona un banco.");
        primeroInvalido = pseBanco;
      }
      if (!pseTipo || !pseTipo.value) {
        marcarError(pseTipo, "error-pse-tipo", "Selecciona el tipo de documento.");
        if (!primeroInvalido) primeroInvalido = pseTipo;
      }
      const documento = pseDocumento ? soloDigitos(pseDocumento.value) : "";
      if (documento.length < 6 || documento.length > 12) {
        marcarError(
          pseDocumento,
          "error-pse-documento",
          "El documento debe tener entre 6 y 12 dígitos."
        );
        if (!primeroInvalido) primeroInvalido = pseDocumento;
      }
    }

    if (metodo === "tarjeta") {
      if (!tarjetaTipo || !tarjetaTipo.value) {
        marcarError(
          tarjetaTipo,
          "error-tarjeta-tipo",
          "Selecciona crédito o débito."
        );
        primeroInvalido = tarjetaTipo;
      }

      const numero = tarjetaNumero ? soloDigitos(tarjetaNumero.value) : "";
      if (numero.length !== 16) {
        marcarError(
          tarjetaNumero,
          "error-tarjeta-numero",
          "El número de tarjeta debe tener 16 dígitos."
        );
        if (!primeroInvalido) primeroInvalido = tarjetaNumero;
      }

      if (!tarjetaTitular || tarjetaTitular.value.trim().length < 3) {
        marcarError(
          tarjetaTitular,
          "error-tarjeta-titular",
          "Ingresa el nombre del titular."
        );
        if (!primeroInvalido) primeroInvalido = tarjetaTitular;
      }

      const vencimiento = tarjetaVencimiento
        ? tarjetaVencimiento.value.trim()
        : "";
      const coincide = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(vencimiento);
      let vencida = false;
      if (coincide) {
        const mes = Number(coincide[1]);
        const anio = 2000 + Number(coincide[2]);
        const ahora = new Date();
        vencida =
          anio < ahora.getFullYear() ||
          (anio === ahora.getFullYear() && mes < ahora.getMonth() + 1);
      }
      if (!coincide || vencida) {
        marcarError(
          tarjetaVencimiento,
          "error-tarjeta-vencimiento",
          "Ingresa un vencimiento válido en formato MM/AA."
        );
        if (!primeroInvalido) primeroInvalido = tarjetaVencimiento;
      }

      const cvv = tarjetaCvv ? soloDigitos(tarjetaCvv.value) : "";
      if (cvv.length < 3 || cvv.length > 4) {
        marcarError(
          tarjetaCvv,
          "error-tarjeta-cvv",
          "El CVV debe tener 3 o 4 dígitos."
        );
        if (!primeroInvalido) primeroInvalido = tarjetaCvv;
      }
    }

    if (primeroInvalido) primeroInvalido.focus();
    return !primeroInvalido;
  };

  form.addEventListener("submit", (evento) => {
    limpiarErrores();
    if (!validar()) {
      evento.preventDefault();
      return;
    }
    if (boton) {
      boton.disabled = true;
      boton.textContent = "Procesando…";
    }
  });
});
