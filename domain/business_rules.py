from datetime import datetime

def evaluar_estado_financiero(casa):
    """
    Motor inteligente basado en el reloj de la PC.
    Determina el semestre actual y evalúa la deuda histórica para 
    asignar el estado de prepago. Ahora discrimina conceptos de pago.
    """
    
    # --- NUEVA REGLA CERO: EL FILTRO DE SERVICIO (N/A) ---
    if not casa.acceso_base:
        return "🔳 N/A", "#333333", 0.0  # Gris oscuro neutro elegante
    
    cargos_totales = 0
    abonos_totales = 0
    cargos_semestre_actual = 0
    
    # Detector estricto: Solo se activa si paga Mantenimiento o Acceso Base
    pago_semestre_actual_encontrado = False 
    
    hoy = datetime.now()
    mes_hoy = hoy.month
    anio_hoy = hoy.year
    
    for p in casa.pagos:
        abonos_totales += p.monto_abonado
        if p.concepto != "Liquidación de Adeudo":
            cargos_totales += p.monto_total
            
            # --- DETECCIÓN DEL SEMESTRE BASADA EN EL RELOJ ---
            mes_pago = p.mes_cubierto
            anio_pago = p.anio_cubierto
            es_actual = False
            
            if 3 <= mes_hoy <= 8:
                if 3 <= mes_pago <= 8 and anio_pago == anio_hoy: es_actual = True
            elif mes_hoy >= 9:
                if (mes_pago >= 9 and anio_pago == anio_hoy) or (mes_pago <= 2 and anio_pago == anio_hoy + 1): es_actual = True
            else: 
                if (mes_pago >= 9 and anio_pago == anio_hoy - 1) or (mes_pago <= 2 and anio_pago == anio_hoy): es_actual = True
                    
            if es_actual:
                cargos_semestre_actual += p.monto_total
                
                # --- NUEVO: AUDITORÍA DE CONCEPTO ---
                # Validamos si la transacción le otorga privilegios de acceso
                otorga_acceso = False
                
                if "Mantenimiento" in p.concepto:
                    otorga_acceso = True
                elif p.concepto == "Venta de Hardware" and p.detalles:
                    # Buscamos en el desglose de su ticket si pagó el "Acceso Base"
                    for det in p.detalles:
                        if "Acceso Base" in det.descripcion:
                            otorga_acceso = True
                            break
                            
                if otorga_acceso:
                    pago_semestre_actual_encontrado = True

    deuda_total = cargos_totales - abonos_totales
    
    # --- REGLA DE NEGOCIO ESTRICTA CORREGIDA ---
    if deuda_total <= 0:
        # No debe nada, ¿pero pagó su acceso/mantenimiento de este semestre?
        if pago_semestre_actual_encontrado:
            return "🟢 Vigente", "#104A20", deuda_total
        else:
            # Compró algo, lo liquidó, pero no es mantenimiento. Se queda sin acceso.
            return "🛑 Restringido", "#4A1010", deuda_total
            
    elif deuda_total > cargos_semestre_actual:
        return "🛑 Restringido", "#4A1010", deuda_total
    else:
        return "⚠️ Parcial", "#b8860b", deuda_total
