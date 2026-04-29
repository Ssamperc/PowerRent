"""
Consumo de servicios externos (APIs de terceros).
"""
import json
import urllib.request


def obtener_tasas_cambio():
    """
    Consume Open Exchange Rates API (gratis, sin API key).
    Retorna cuántos COP equivalen a 1 USD y 1 EUR.
    Se muestra en la barra superior como utilidad para clientes internacionales.
    """
    try:
        # USD base: cuántos COP por 1 USD
        url = 'https://open.er-api.com/v6/latest/USD'
        req = urllib.request.Request(url, headers={'User-Agent': 'PowerRent/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            rates = data.get('rates', {})
            cop_usd = rates.get('COP', 4200)  # COP por 1 USD
            cop_eur = cop_usd / rates.get('EUR', 0.92) if rates.get('EUR') else 4600
            return {
                'ok': True,
                'usd': round(cop_usd),
                'eur': round(cop_eur),
            }
    except Exception:
        return {'ok': False, 'usd': 4200, 'eur': 4600}


def consumir_servicio_aliado():
    """
    Servicio aliado: maquinaria pesada complementaria.
    En producción reemplazar con la URL real del equipo anterior.
    """
    items = [
        {'id': 1, 'titulo': 'Retroexcavadora CAT 320', 'descripcion': 'Excavadora hidráulica 20 ton, ideal para movimiento de tierras y excavaciones profundas.', 'precio_dia': 850000, 'disponible': True, 'categoria': 'Maquinaria Pesada'},
        {'id': 2, 'titulo': 'Bulldozer Komatsu D65', 'descripcion': 'Tractor de orugas para nivelación de terrenos y empuje de materiales en construcción.', 'precio_dia': 1200000, 'disponible': True, 'categoria': 'Maquinaria Pesada'},
        {'id': 3, 'titulo': 'Grúa Torre 40m', 'descripcion': 'Alcance de 40 metros y capacidad de 3 toneladas para proyectos de gran altura.', 'precio_dia': 2500000, 'disponible': False, 'categoria': 'Elevación'},
        {'id': 4, 'titulo': 'Volqueta 14m³', 'descripcion': 'Camión volqueta de gran capacidad para transporte de materiales y escombros.', 'precio_dia': 450000, 'disponible': True, 'categoria': 'Transporte'},
        {'id': 5, 'titulo': 'Motoniveladora Caterpillar', 'descripcion': 'Conformación y perfilado de vías, terrenos y subrasantes con precisión.', 'precio_dia': 980000, 'disponible': True, 'categoria': 'Maquinaria Pesada'},
        {'id': 6, 'titulo': 'Miniexcavadora Kubota', 'descripcion': 'Compacta e ideal para trabajos en espacios reducidos y obras urbanas.', 'precio_dia': 380000, 'disponible': True, 'categoria': 'Maquinaria Compacta'},
    ]
    return {
        'ok': True,
        'empresa_aliada': 'HeavyRent Colombia',
        'descripcion': 'Especialistas en alquiler de maquinaria pesada para construcción',
        'contacto': '+57 310 987 6543',
        'items': items,
    }
