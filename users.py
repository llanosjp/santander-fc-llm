"""
Mapeo de números de WhatsApp a usuarios de Santander.
Usado para filtrar los datos que retorna la API.
"""

# Formato: número WhatsApp (sin +) -> (usuario, rol, nombre)
WHATSAPP_USERS = {
    # Ejecutivos
    "51902735404": ("jvelez", "ejecutivo", "Jose Velez"),
    # Agreg más usuarios aquí:
    # "51999999999": ("usuario2", "jefe", "Nombre Apellido"),
    # "51988888888": ("usuario3", "lider", "Nombre Lider"),
}

def get_user_by_phone(phone: str) -> tuple[str, str, str] | None:
    """
    Retorna (usuario, rol, nombre) dado un número de teléfono.
    
    Args:
        phone: Número con formato +51 o sin código de país
               ej: "+51902735404" o "51902735404"
    
    Returns:
        Tupla (usuario, rol, nombre) o None si no existe
    """
    # Normalizar: quitar + y espacios
    normalized = phone.replace("+", "").replace(" ", "")
    
    return WHATSAPP_USERS.get(normalized)


def get_filtros_from_phone(phone: str) -> dict:
    """
    Retorna los filtros para la API de Santander basados en el número.
    
    Args:
        phone: Número de WhatsApp
    
    Returns:
        Diccionario con FILTRO_EJECUTIVO, FILTRO_JEFE, FILTRO_LIDER, USUARIO
    """
    user_data = get_user_by_phone(phone)
    
    if user_data is None:
        # Si no está mapeado, devolver null (para ver todos los datos)
        return {
            "USUARIO": None,
            "FILTRO_EJECUTIVO": None,
            "FILTRO_JEFE": None,
            "FILTRO_LIDER": None,
        }
    
    usuario, rol, nombre = user_data
    
    # Mapear rol a filtro
    if rol == "ejecutivo":
        return {
            "USUARIO": usuario,
            "FILTRO_EJECUTIVO": usuario,
            "FILTRO_JEFE": None,
            "FILTRO_LIDER": None,
        }
    elif rol == "jefe":
        return {
            "USUARIO": usuario,
            "FILTRO_EJECUTIVO": None,
            "FILTRO_JEFE": usuario,
            "FILTRO_LIDER": None,
        }
    elif rol == "lider":
        return {
            "USUARIO": usuario,
            "FILTRO_EJECUTIVO": None,
            "FILTRO_JEFE": None,
            "FILTRO_LIDER": nombre,  # El nombre del líder para filtrar
        }
    elif rol == "gerente":
        return {
            "USUARIO": usuario,
            "FILTRO_EJECUTIVO": None,
            "FILTRO_JEFE": None,
            "FILTRO_LIDER": None,
        }
    
    # Por defecto, ver todo
    return {
        "USUARIO": None,
        "FILTRO_EJECUTIVO": None,
        "FILTRO_JEFE": None,
        "FILTRO_LIDER": None,
    }