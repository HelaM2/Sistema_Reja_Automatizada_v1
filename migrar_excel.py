# migrar_excel.py
import pandas as pd
from core.database import SessionLocal
from domain.models import Lote, Casa, Residente, Dispositivo, Pago

def migrar_datos_historicos():
    db = SessionLocal()
    print(">>> [MIGRACIÓN] Abriendo archivo ChipsCerrada.xlsx...")
    
    try:
        df = pd.read_excel("ChipsCerrada.xlsx")
    except Exception as e:
        print(f"Error al leer el Excel: {e}\n(Asegúrate de tener instalados pandas y openpyxl)")
        return
        
    # Limpiamos los "NaN" de pandas transformándolos en "None" nativos de Python para evitar errores
    df = df.where(pd.notnull(df), None)
    
    registros_procesados = 0
    
    for index, row in df.iterrows():
        lote_num = row['LOTE']
        casa_num = row['CASA']
        
        # Validar que la fila realmente tenga datos de vivienda
        if pd.isna(lote_num) or pd.isna(casa_num):
            continue
            
        lote_num = int(lote_num)
        # Convertimos el número de casa a entero y luego a string (ej. 1.0 -> "1")
        casa_num_str = str(int(casa_num)) 
        
        # Cruzar con nuestra BD para obtener el ID real de la Casa
        casa = db.query(Casa).join(Lote).filter(
            Lote.numero == lote_num,
            Casa.numero_interior == casa_num_str
        ).first()
        
        if not casa:
            print(f" [!] Casa {lote_num}-{casa_num_str} no encontrada en BD. Omitiendo fila.")
            continue
            
        print(f" [+] Procesando Hogar {lote_num}-{casa_num_str}...")
        
        # --- 1. RESIDENTES (Contactos) ---
        nombre = row['NOMBRE']
        if nombre:
            # Si hay teléfono o correo, los pasamos a string
            telefono = str(row['NUMERO DE CEL']) if row['NUMERO DE CEL'] else None
            email = str(row['MAIL']) if row['MAIL'] else None
            
            nuevo_residente = Residente(
                casa_id=casa.id,
                nombre_completo=str(nombre).strip(),
                telefono=telefono,
                email=email,
                es_propietario=True
            )
            db.add(nuevo_residente)
            
        # --- 2. DISPOSITIVOS PEATONALES (CHIPS) ---
        chips_str = row['NO. CHIP']
        if chips_str:
            # Separamos por comas y limpiamos espacios
            lista_chips = str(chips_str).split(',')
            for chip_id in lista_chips:
                chip_id = chip_id.strip()
                if chip_id:
                    nuevo_chip = Dispositivo(
                        casa_id=casa.id,
                        identificador_hardware=chip_id,
                        tipo_dispositivo="RFID"
                    )
                    db.add(nuevo_chip)
                    
        # --- 3. PAGOS DE CHIPS ---
        pago_chip = row['PAGO\nCHIP']
        if pago_chip and float(pago_chip) > 0:
            pago_c = Pago(
                casa_id=casa.id,
                concepto="Venta de Hardware (Chips)",
                monto_total=float(pago_chip),
                monto_abonado=float(pago_chip),
                mes_cubierto=8,  # Fijamos Agosto como mes de corte/arranque
                anio_cubierto=2026,
                estado="LIQUIDADO"
            )
            db.add(pago_c)
            
        # --- 4. ACCESO BASE (PISTONES Y WI-FI) ---
        pistones = row['PISTO-NES']
        if pistones and float(pistones) > 0:
            pago_p = Pago(
                casa_id=casa.id,
                concepto="Acceso Base (Pistones y 2 Wi-Fi)",
                monto_total=float(pistones),
                monto_abonado=float(pistones),
                mes_cubierto=8,
                anio_cubierto=2026,
                estado="LIQUIDADO"
            )
            db.add(pago_p)
            
            # Se generan los 2 "espacios" de Wi-Fi temporales en el inventario
            for i in range(1, 3):
                wifi_base = Dispositivo(
                    casa_id=casa.id,
                    identificador_hardware=f"WIFI-PENDIENTE-{lote_num}-{casa_num_str}-{i}",
                    tipo_dispositivo="WIFI_PERMIT"
                )
                db.add(wifi_base)
                
        # --- 5. CONTROLES VEHICULARES (RF) ---
        controles = row['CRTLS']
        if controles and float(controles) > 0:
            monto_controles = float(controles)
            # Deducimos la cantidad física dividiendo entre $250
            cantidad_rf = int(monto_controles // 250)
            
            pago_rf = Pago(
                casa_id=casa.id,
                concepto="Venta de Hardware (Controles Vehiculares)",
                monto_total=monto_controles,
                monto_abonado=monto_controles,
                mes_cubierto=8,
                anio_cubierto=2026,
                estado="LIQUIDADO"
            )
            db.add(pago_rf)
            
            # Generamos los IDs temporales según la cantidad deducida
            for i in range(cantidad_rf):
                nuevo_rf = Dispositivo(
                    casa_id=casa.id,
                    identificador_hardware=f"RF-PENDIENTE-{lote_num}-{casa_num_str}-{i+1}",
                    tipo_dispositivo="RF_VEHICULAR"
                )
                db.add(nuevo_rf)
                
        registros_procesados += 1
        
    try:
        # Commit atómico: o se guarda todo el Excel, o no se guarda nada (evita datos corruptos)
        db.commit()
        print(f"\n>>> [ÉXITO] Migración finalizada. Se procesaron y estructuraron {registros_procesados} hogares.")
    except Exception as e:
        db.rollback()
        print(f"\n>>> [ERROR CRÍTICO] Fallo transaccional al guardar en la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrar_datos_historicos()