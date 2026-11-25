import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


SECRET_KEY = os.getenv("SECRET_KEY", "mareva_secret_2026")
TOKEN_SALT = "turismo-magico-pago"
TOKEN_MAX_AGE = 3600

BENEFICIARIO_NOMBRE = "Turismo Mágico"
BENEFICIARIO_CUENTA = os.getenv("PAGO_CUENTA_BENEFICIARIO", "910 456 7281")

PSE_BANCOS = (
    "Bancolombia",
    "Davivienda",
    "Banco de Bogotá",
    "BBVA Colombia",
    "Banco de Occidente",
    "Banco Popular",
    "Banco Caja Social",
    "Banco Agrario de Colombia",
    "Banco Pichincha",
    "Scotiabank Colpatria",
    "Banco Santander de Negocios Colombia",
    "Banco Itaú",
    "Banco de Comercio",
    "Banco ProCredit",
    "Banco Falabella",
    "Banco Ripley",
    "Banco W",
    "Banco Compartir",
    "Banco Mundo Mujer",
    "Banco Finandina",
    "Banco HSBC",
    "Citibank",
)

TIPOS_DOCUMENTO = ("CC", "CE", "TI", "NIT")
TIPOS_TARJETA = ("credito", "debito")

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt=TOKEN_SALT)


def crear_token(datos):
    return _serializer.dumps(datos)


def leer_token(token):
    try:
        return _serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
