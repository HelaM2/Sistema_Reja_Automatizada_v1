# 🏘️ Sistema de Reja Automatizada v1.0

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-UI-darkgreen?style=for-the-badge)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?style=for-the-badge)

Aplicación de escritorio robusta diseñada para la gestión integral de una privada residencial de 70 casas. Este sistema centraliza el control financiero, la auditoría de accesos IoT y la emisión de comprobantes mediante una arquitectura de software moderna y modular.

## 🚀 Características Principales

*   **Gestión Vecinal Dinámica:** Panel de control visual interactivo para consultar el estatus de residentes y viviendas (Lote y Casa).
*   **Motor Financiero Automatizado:** Cálculo de adeudos, registro de cuotas de mantenimiento y liquidaciones con generación de historial.
*   **Auditoría IoT y Accesos:** Sincronización manual y gestión de estado (Alta/Baja/Bloqueo) para Chips Peatonales, Controles Vehiculares y Accesos Wi-Fi.
*   **Notificaciones SMTP:** Sistema integrado ("El Cartero") para el envío automatizado de recibos de pago y notificaciones de bloqueo a morosos.
*   **Arquitectura MVC Desacoplada:** Interfaz gráfica libre de cuellos de botella con prevención activa de importaciones circulares y gestión de memoria optimizada.

## 📁 Arquitectura del Sistema (Topología)

El proyecto está diseñado bajo los principios de Inversión de Control (IoC) y Separación de Responsabilidades (SoC).

```text
SISTEMA_REJA_AUTOMATIZADA_v1/
│
├── core/                       # Infraestructura base de bajo nivel
│   ├── database.py             # Configuración, motor y conexión con SQLite
│   └── security.py             # Encriptación y validación de seguridad
│
├── domain/                     # Capa de Dominio (Modelos y Reglas)
│   ├── models.py               # Esquema relacional de la BD (Clases de SQLAlchemy)
│   └── business_rules.py       # Lógica financiera pura (Ej. evaluar_estado_financiero)
│
├── services/                   # Controladores Backend y Lógica de Negocio
│   ├── hardware_service.py     # Gestión de altas, bajas y validación de dispositivos
│   ├── notification_service.py # "El Cartero": Enrutamiento y envío de correos SMTP
│   ├── payment_service.py      # Procesamiento, cálculo y registro de transacciones
│   └── tuya_service.py         # Integración y sincronización de estados con la nube
│
├── ui/                         # Capa de Presentación (Interfaz Gráfica Modular)
│   ├── app_controller.py       # Orquestador principal y enrutador de vistas
│   ├── components/             # Componentes reutilizables
│   │   ├── __init__.py
│   │   └── panel_detalle.py    # Sub-controlador: Panel lateral deslizable de viviendas
│   ├── modals/                 # Ventanas emergentes (Toplevels)
│   │   ├── __init__.py
│   │   ├── estado_cuenta.py    # Historial transaccional detallado
│   │   └── lista_negra.py      # Generador de reportes y envío de correos SMTP
│   └── views/                  # Vistas a pantalla completa
│       ├── __init__.py
│       ├── vista_lotes.py      # Dashboard vecinal (Cuadrícula semaforizada)
│       ├── vista_dispositivos.py # Gestor de hardware (Altas/Bajas de RFID y WiFi)
│       ├── vista_finanzas.py   # Punto de venta, cobros y comprobantes
│       └── vista_auditoria.py  # Comparativa local vs Tuya y tareas pendientes
│
├── manual_usuario/             # Documentación y guías para el usuario final
│
├── main.py                     # Punto de entrada (Bootstrapper y anclaje PyInstaller)
├── requirements.txt            # Dependencias exactas del entorno de desarrollo
├── residencial.db              # Base de datos SQLite (Externa al empaquetado)
└── seed_db.py                  # Script para poblar la base de datos inicial
```

## 🛠️ Instalación y Ejecución

1. Clona este repositorio.
2. Crea un entorno virtual: `python -m venv venv`
3. Activa el entorno virtual.
4. Instala las dependencias: `pip install -r requirements.txt`
5. Ejecuta el sistema: `python main.py`

## 🗺️ Roadmap y Próximas Mejoras (Fase 2)

El desarrollo de este sistema es iterativo. Las siguientes características están programadas para futuras actualizaciones:

*   **🔧 Módulo de Mantenimiento:** Nueva vista dividida para registrar el Mantenimiento Preventivo (Checklist semestral de la reja) y Mantenimiento Correctivo (Registro libre de incidencias y bitácora).
*   **🎨 Refinamiento UI/UX:** Rediseño estético de paletas de colores, revisión de etiquetas, botones y diseño general para una experiencia de usuario más elegante y moderna.
*   **📧 Plantillas de Correo Premium:** Modernización del código inyectado en los correos electrónicos enviados a los residentes para mejorar su presentación.
*   **⚙️ Hardware Propietario (Sustitución de Tuya/Seg):** Migración hacia una placa de control de hardware de diseño propio. Esto permitirá al software otorgar y revocar permisos físicos de la reja directamente en tiempo real, eliminando la dependencia de servicios de terceros y automatizando por completo la gestión.

---

## 👨‍💻 Autor

**Hugo Helaman Meneses Maldonado**
*Ingeniería Mecatrónica | UPIITA - IPN*

*   **Email:** <menesesh01@gmail.com> | <hmenesesm1600@alumno.ipn.mx>
*   **LinkedIn:** (próximamente)
*   **GitHub:** <https://github.com/HelaM2/>
