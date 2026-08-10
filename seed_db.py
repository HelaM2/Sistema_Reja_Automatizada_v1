# seed_db.py
from core.database import SessionLocal, init_db
from domain.models import Lote, Casa, CatalogoPrecios

LOTES_TUYA_MAPPING = {
    27: "vdevo178560393117461",
    28: "vdevo178560399754129",
    29: "vdevo178560403781507",
    30: "vdevo178560411077579",
    31: "vdevo178560414254851",
    32: "vdevo178560419162939",
    33: "vdevo178560423294709",
    34: "vdevo178560427305618",
    35: "vdevo178560431801046",
    36: "vdevo178560435545929",
    37: "vdevo178560442841041",
    38: "vdevo178560447863999",
    39: "vdevo178560460741916",
    40: "vdevo178560453274067",
    41: "vdevo178560464243889",
    42: "vdevo178560470065075",
    43: "vdevo178560479628579",
    44: "vdevo178560483231593",
    45: "vdevo178560488532186"
}

def poblar_catalogo_precios():
    db = SessionLocal()
    print(">>> [SEED] Iniciando inyección del catálogo de precios...")
    
    precios_base = [
        {"dispositivo": "Acceso Base (Pistones y 2 WiFi)", "precio": 400.0},
        {"dispositivo": "Chip Peatonal", "precio": 100.0},
        {"dispositivo": "Control Vehicular", "precio": 250.0},
        {"dispositivo": "Acceso WiFi Extra", "precio": 200.0},
        {"dispositivo": "Mantenimiento Base", "precio": 200.0},
        {"dispositivo": "Mantenimiento Extra (WiFi)", "precio": 100.0}
    ]
    
    for item in precios_base:
        existe = db.query(CatalogoPrecios).filter_by(dispositivo=item["dispositivo"]).first()
        if not existe:
            nuevo_precio = CatalogoPrecios(dispositivo=item["dispositivo"], precio_unitario=item["precio"])
            db.add(nuevo_precio)
            print(f" [+] Añadido al catálogo: {item['dispositivo']} -> ${item['precio']}")
        else:
            existe.precio_unitario = item["precio"]
            print(f" [~] Actualizado en catálogo: {item['dispositivo']} -> ${item['precio']}")
            
    db.commit()
    db.close()
    print(">>> [SEED] Catálogo de precios listo.")

def poblar_lotes_reales():
    db = SessionLocal()
    
    print(">>> [SEED] Iniciando inyección de infraestructura en base de datos...")
    
    for num_lote, tuya_id in LOTES_TUYA_MAPPING.items():
        lote_existente = db.query(Lote).filter(Lote.numero == num_lote).first()
        
        if not lote_existente:
            nuevo_lote = Lote(numero=num_lote, tuya_virtual_id=tuya_id)
            db.add(nuevo_lote)
            print(f" [+] Lote {num_lote} registrado exitosamente con ID: {tuya_id}")
                
        else:
            lote_existente.tuya_virtual_id = tuya_id
            print(f" [~] Lote {num_lote} actualizado con el ID: {tuya_id}")

    db.commit()
    db.close()
    print(">>> [SEED] ¡Mapeo completado! Base de datos lista para operar.")

def poblar_casas_reales():
    db = SessionLocal()
    print(">>> [SEED] Iniciando generación automática de viviendas (4 por lote)...")
    
    lotes_en_bd = db.query(Lote).all()
    
    casas_creadas = 0
    for lote in lotes_en_bd:
        for num_casa in ["1", "2", "3", "4"]:
            casa_existente = db.query(Casa).filter_by(lote_id=lote.id, numero_interior=num_casa).first()
            
            if not casa_existente:
                nueva_casa = Casa(lote_id=lote.id, numero_interior=num_casa)
                db.add(nueva_casa)
                casas_creadas += 1
                
    db.commit()
    db.close()
    print(f">>> [SEED] ¡Infraestructura lista! Se registraron {casas_creadas} casas exitosamente.")

if __name__ == "__main__":
    init_db()
    poblar_catalogo_precios()
    poblar_lotes_reales()
    poblar_casas_reales()