# Manual de buenas prácticas de operación y mantenimiento

**Plantas de inyección de agua del yacimiento Cerro Dragón Sur**

- Documento: MBP-OPM-INY
- Revisión: 4
- Vigente desde: 2025-07-01
- Emisor: Gerencia de Operaciones · Yacimiento Cerro Dragón Sur
- Reemplaza a: MBP-OPM-INY Rev. 3 (2023-04-10)

Documento interno de la operadora. Aplica a las plantas de inyección PIA-1, PIA-2 y PIA-3. Las secciones que aplican a una sola planta lo indican en el título.

En caso de diferencia entre este manual y el manual de un fabricante, vale el más restrictivo, salvo los límites de alarma, que son los del sistema de control de cada planta (capítulo 5).

## Control de revisiones

| Rev. | Fecha | Descripción |
| --- | --- | --- |
| 1 | 2017-03-01 | Emisión original para PIA-1 y PIA-2. |
| 2 | 2019-10-15 | Se incorpora PIA-3. |
| 3 | 2023-04-10 | Límites de PIA-3 según el manual TX-350 Rev. D. Catálogo de fallas. |
| 4 | 2025-07-01 | Reglas de aprobación de órdenes. Certificación de contratistas con el contrato CT-SVP-2025. Partes de recorrida por voz. |

## 1. Objeto y alcance

Este manual reúne las prácticas de operación y mantenimiento de las plantas de inyección de agua del yacimiento. No reemplaza a los manuales de los fabricantes: los ordena, define qué se hace en cada caso y quién lo decide.

### 1.1 Plantas alcanzadas

| Planta | Bombas | Filtración | Inyección programada |
| --- | --- | --- | --- |
| PIA-1 | 4 centrífugas multietapa | Filtros de arena | 3.800 m³/d |
| PIA-2 | 2 triplex TX-250 | Cartuchos FC-24 | 1.100 m³/d (piloto de polímero) |
| PIA-3 | 3 triplex TX-350 (2 + 1 reserva) | 2 x FC-48 en serie | 2.400 m³/d |

### 1.2 Documentos de referencia

| Documento | Código | Revisión vigente |
| --- | --- | --- |
| Manual de la bomba Trimax TX-350 | MT-TX350-ES | Rev. D (2023-03-15) |
| Manual del filtro Filtrapat FC-48 | MOM-FC48 | Rev. 3 (2022-08-01) |
| Contrato de mantenimiento con Servipat | CT-SVP-2025 | Anexo de precios 2025-2026 |
| Plan de respuesta a emergencias del yacimiento | PRE-CDS | Rev. 7 |

> **ADVERTENCIA.** En la sala de bombas de PIA-3 quedan copias impresas del manual TX-350 Rev. C (2019). Esa revisión está reemplazada: sus límites de vibración, temperatura de aceite y presión, el aceite ISO VG 150 y los códigos de repuesto 350-xxx ya no valen. Use la Rev. D.

## 2. Descripción de la planta PIA-3

### 2.1 Proceso

La planta Planta de Inyección PIA-3 recibe agua de formación tratada en el tanque pulmón TK-301, la filtra en dos etapas en serie (F-201A primario de 25 µm y F-201B secundario de 10 µm) y la inyecta con bombas triplex al colector de inyección, donde la mide el caudalímetro FT-401. Dos bombas están en servicio y una en reserva. Una bomba de carga aguas arriba de los filtros da unos 3,5 kg/cm².

### 2.2 Equipos y nombres

El personal de campo nombra los equipos de muchas formas. En las notas de voz, las planillas y las órdenes pueden aparecer cualquiera de estos nombres.

| TAG | Equipo | Nombres que se usan en campo |
| --- | --- | --- |
| B-101 | Bomba alternativa triplex 1 | la uno, la 1, la de la punta, la del portón, bomba uno |
| B-102 | Bomba alternativa triplex 2 | la dos, la 2, la del medio, bomba dos |
| B-103 | Bomba alternativa triplex 3 | la tres, la 3, la del fondo, la de reserva, bomba tres |
| F-201A | Filtro de cartuchos primario 25 µm | el filtro A, el primario, el de la izquierda, el grueso |
| F-201B | Filtro de cartuchos secundario 10 µm | el filtro B, el secundario, el de la derecha, el fino |
| TK-301 | Tanque pulmón de agua tratada | el pulmón, el tanque, el tanque pulmón |
| FT-401 | Caudalímetro del colector de inyección | el caudalímetro, el colector |

### 2.3 Manómetros locales de las bombas

Por razones históricas, cada bomba tiene el manómetro local de descarga en una unidad distinta. Al anotar o dictar una lectura, diga siempre la unidad.

| Bomba | Unidad del manómetro local | Descarga normal en esa unidad |
| --- | --- | --- |
| B-101 | kg/cm2 | 108 a 115 kg/cm² |
| B-102 | psi | 1.540 a 1.640 psi |
| B-103 | bar | 106 a 113 bar |

### 2.4 Roles iniciales de las bombas

En la configuración normal, B-101 está en servicio, B-102 está en servicio, B-103 está en reserva. La reserva se rota cada 500 horas de marcha. Una bomba en mantenimiento, disparada o bloqueada no cuenta como reserva.

### 2.5 Lecturas de recorrida

| Equipo | Qué se lee en la recorrida |
| --- | --- |
| Bombas | Presión de descarga local, temperatura de rodamiento y de motor con IR, goteo de empaquetadura (gotas/min), nivel de aceite en el visor, estado de correas, ruido |
| Filtros | Presión diferencial en el manómetro local |
| Tanque | Nivel |

## 3. Roles y responsabilidades

### 3.1 Quién hace qué

| Rol | Responsabilidad |
| --- | --- |
| Operador de turno | Recorridas, partes de recorrida por voz, planilla del turno, primera respuesta a emergencias. |
| Supervisor de turno | Decide sacar equipos de servicio, recibe las alertas de seguridad. |
| Planificador de mantenimiento | Aprueba las órdenes que no cumplen las reglas de aprobación automática, programa los trabajos y pide repuestos al almacén central. |
| Técnicos propios | Ejecutan las tareas estándar de ejecutor propio y dictan la nota de cierre. |
| Contratista (Servipat) | Ejecuta las tareas de contratista según el contrato CT-SVP-2025. |
| Certificador | Revisa el cierre de la contratista contra la orden y el contrato y emite el habilita. |
| Sistema de agentes | Interpreta partes y sensores, abre eventos y órdenes y aplica las reglas de aprobación. No tiene facultades que no estén en las reglas. |

### 3.2 Escalamiento

Cualquier situación que el operador no pueda resolver con este manual se escala al supervisor de turno. Las condiciones inseguras (capítulo 7) se escalan siempre y de inmediato, por radio, aunque no haya enlace de datos.

## 4. Turnos, recorridas y registro

### 4.1 Turnos

Hay dos turnos de 12 horas: día de 7 a 19 y noche de 19 a 7. El relevo se hace en la sala de control con la planilla del turno saliente a la vista.

### 4.2 Horario de recorridas

Se hacen dos recorridas por turno, a las 8, 14, 20 y 2 horas, con una tolerancia de -10 a +20 minutos. Cada recorrida cubre todos los equipos en el mismo orden: bombas, filtros y tanque.

### 4.3 Parte de recorrida por voz

Desde 2025 el operador dicta notas de voz durante la recorrida y saca fotos con el celular. Cada nota debería decir el equipo, la variable, el valor con su unidad y la observación. Ejemplo de buena nota: 'La dos, descarga mil quinientos ochenta psi, goteo de empaquetadura doce gotas por minuto, todo normal'.

- Nombre el equipo como quiera (ver nombres en campo), pero uno por nota si hay algo anormal.
- Diga la unidad del manómetro: cada bomba tiene la suya.
- Si hay algo inseguro, dígalo primero.
- Si no hay novedad, dígalo: 'sin novedad' también es información.

### 4.4 Planilla de papel del turno

La planilla de papel sigue siendo el registro oficial del turno. Se carga en el sistema al terminar el turno, con demora. Use las abreviaturas de la tabla; no invente otras.

| Abreviatura | Significa |
| --- | --- |
| B1, Bba 1 | B-101 |
| B2, Bba 2 | B-102 |
| B3, Bba 3 | B-103 |
| FA, Filt A | F-201A |
| FB, Filt B | F-201B |
| TK, Pulmón | TK-301 |
| P desc | Presión de descarga local |
| ΔP | Presión diferencial del filtro |
| T rod | Temperatura de rodamiento (IR) |
| Goteo | Goteo de empaquetadura (g/min) |
| Aceite | Nivel de aceite en el visor |
| s/n | Sin novedad |
| OT | Orden de trabajo |
| c/ | con |
| s/ | sin |
| x | por |

### 4.5 Errores frecuentes de registro

- Dígitos invertidos (112 anotado como 121).
- Unidad equivocada (psi anotado como kg).
- Valores redondeados de más.
- Letra ilegible.
- Observaciones sin el equipo ('pierde un poco').

Por estos errores, una lectura de la planilla que no coincide con el sensor no alcanza para concluir que el sensor está mal. Confirme con otra recorrida o con el parte por voz.

## 5. Límites de operación de PIA-3

Estos son los límites de alarma configurados en el sistema de control de PIA-3. Coinciden con la hoja de datos de cada equipo (TX-350 Rev. D y FC-48 Rev. 3). Son los únicos límites válidos para PIA-3.

### 5.1 Límites de los sensores conectados

| TAG | Variable | Unidad | Alarma baja | Alarma alta | Disparo |
| --- | --- | --- | --- | --- | --- |
| B-101 | Presión de succión | kg/cm2 | 0,9 | - | - |
| B-101 | Presión de descarga | kg/cm2 | 95 | 125 | - |
| B-101 | Temperatura de aceite | °C | - | 80 | 90 |
| B-101 | Vibración | mm/s | - | 7,1 | 11,2 |
| B-102 | Presión de succión | kg/cm2 | 0,9 | - | - |
| B-102 | Presión de descarga | kg/cm2 | 95 | 125 | - |
| B-102 | Temperatura de aceite | °C | - | 80 | 90 |
| B-102 | Vibración | mm/s | - | 7,1 | 11,2 |
| B-103 | Presión de succión | kg/cm2 | 0,9 | - | - |
| B-103 | Presión de descarga | kg/cm2 | 95 | 125 | - |
| B-103 | Temperatura de aceite | °C | - | 80 | 90 |
| B-103 | Vibración | mm/s | - | 7,1 | 11,2 |
| F-201A | Presión diferencial | kg/cm2 | 0,15 | 1,5 | - |
| F-201B | Presión diferencial | kg/cm2 | 0,15 | 1,5 | - |
| FT-401 | Caudal de inyección | m3/d | 2.200 | - | - |

### 5.2 Protecciones

Las bombas disparan por temperatura de aceite mayor a 90 °C, vibración mayor a 11,2 mm/s o presión de succión menor a 0,5 kg/cm², sostenidas 30 segundos, y por humo o térmico del motor. Al disparar una bomba arranca la de reserva si está disponible (unos 90 segundos).

### 5.3 Límites de otras plantas

Solo como referencia. No aplican a PIA-3.

| Planta | Variable | Alarma |
| --- | --- | --- |
| PIA-1 | Vibración de bombas centrífugas | 4,5 mm/s |
| PIA-1 | Presión de descarga | alta 95 kg/cm² |
| PIA-2 | Temperatura de aceite TX-250 | 85 °C |
| PIA-2 | ΔP filtros FC-24 | 1,2 kg/cm² |
| PIA-2 | Caudal de inyección | baja 950 m³/d |

## 6. Catálogo de fallas de equipo

Este catálogo es el lenguaje común entre el campo, el sistema y mantenimiento. Cada falla tiene una firma en los sensores y una firma en la recorrida. Los manuales de los fabricantes usan sus propios códigos: la columna 'Fabricante' da la correspondencia.

### 6.1 Resumen del catálogo

| Código | Falla | Fabricante | Tarea | Ejecutor |
| --- | --- | --- | --- | --- |
| F01 | Pérdida por empaquetadura | TX-T01 | T-B-EMP | propio |
| F02 | Válvulas de succión/descarga gastadas | TX-T02 | T-B-VAL | propio |
| F03 | Rodamiento de cigüeñal dañado | TX-T03 | T-B-ROD (no estándar) | contratista (Servipat) |
| F04 | Bajo nivel de aceite del cárter | TX-T04 | T-B-ACE | propio |
| F05 | Correas flojas o gastadas | TX-T05 | T-B-COR | propio |
| F06 | Acople desalineado / elastómero gastado | TX-T06 | T-B-ALI (no estándar) | contratista (Servipat) |
| F07 | Cartuchos colmatados | FC-T01 | T-F-CAR | propio |
| F08 | Cartucho roto (agua sin filtrar) | FC-T02 | T-F-CAR + inspección | propio |
| F09 | Cavitación por baja succión | TX-T07 | Según la causa (normalmente T-F-CAR en el filtro colmatado) | propio |
| F10 | Sensor congelado o con deriva | TX-T08 / FC-T04 | T-I-CAL | propio |

### 6.2 Matriz de firmas

| Código | Firma en sensores | Firma en la recorrida |
| --- | --- | --- |
| F01 | Caída leve de caudal de la bomba (y del colector FT-401). Sin cambios en vibración, temperatura ni presiones. | Goteo en el prensaestopas que crece de una recorrida a la otra (gotas/min). Foto de la empaquetadura con agua escurriendo. |
| F02 | Vibración en aumento, pulsación de la presión de descarga en aumento, caudal en baja. | Golpeteo metálico rítmico en el extremo hidráulico. Aguja del manómetro local que oscila. |
| F03 | Vibración en aumento con tendencia que se acelera; temperatura de aceite en aumento. | Ruido de rodamiento (zumbido grave en el cárter). Temperatura de rodamiento alta al IR. |
| F04 | Temperatura de aceite en aumento gradual, sin cambios en la vibración. | Nivel del visor de aceite por debajo del mínimo. |
| F05 | Caudal de la bomba en baja por resbalamiento, con presión de succión normal. | Chirrido, polea y motor calientes, correas brillantes o con flecha excesiva. Foto de las correas. |
| F06 | Vibración moderada en aumento, sin pulsación de descarga. | Acople caliente al IR, polvo de elastómero bajo la guarda. Foto del acople. |
| F07 | Presión diferencial del filtro en aumento; presión de succión de todas las bombas en baja. | Manómetro diferencial local alto. |
| F08 | Presión diferencial que cae de golpe, por debajo de la alarma baja. | Nada visible. |
| F09 | Presión de succión en baja, vibración en aumento, caudal en baja. | Ruido 'a piedras' en el extremo hidráulico. |
| F10 | Valor plano, sin ruido, o que se corre de a poco sin que cambien las variables relacionadas. | La lectura local no coincide con la del sistema de control. El equipo se ve normal. |

### 6.3 F01 Pérdida por empaquetadura

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas B-101, B-102, B-103 |
| Código del fabricante | TX-T01 |
| Firma en sensores | Caída leve de caudal de la bomba (y del colector FT-401). Sin cambios en vibración, temperatura ni presiones. |
| Firma en la recorrida | Goteo en el prensaestopas que crece de una recorrida a la otra (gotas/min). Foto de la empaquetadura con agua escurriendo. |
| Tarea | T-B-EMP |
| Ejecutor | propio |

Detiene la bomba unas 4 h: se aprueba solo si hay bomba de reserva disponible para mantener la inyección. Si la pérdida se repite en el mismo émbolo a las pocas semanas, revisar el émbolo (no es tarea estándar).

### 6.4 F02 Válvulas de succión/descarga gastadas

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T02 |
| Firma en sensores | Vibración en aumento, pulsación de la presión de descarga en aumento, caudal en baja. |
| Firma en la recorrida | Golpeteo metálico rítmico en el extremo hidráulico. Aguja del manómetro local que oscila. |
| Tarea | T-B-VAL |
| Ejecutor | propio |

El kit cuesta USD 1.900, cerca del límite de aprobación automática. Si varias bombas presentan la falla en pocos días, sospechar de un cartucho roto aguas arriba (F08).

### 6.5 F03 Rodamiento de cigüeñal dañado

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T03 |
| Firma en sensores | Vibración en aumento con tendencia que se acelera; temperatura de aceite en aumento. |
| Firma en la recorrida | Ruido de rodamiento (zumbido grave en el cárter). Temperatura de rodamiento alta al IR. |
| Tarea | T-B-ROD (no estándar) |
| Ejecutor | contratista (Servipat) |

Tarea no estándar, de contratista y de más de USD 2.500: siempre va al planificador. El cierre de la contratista se certifica contra la orden y la lista de precios del contrato.

### 6.6 F04 Bajo nivel de aceite del cárter

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T04 |
| Firma en sensores | Temperatura de aceite en aumento gradual, sin cambios en la vibración. |
| Firma en la recorrida | Nivel del visor de aceite por debajo del mínimo. |
| Tarea | T-B-ACE |
| Ejecutor | propio |

No detiene la bomba, es barata y hay stock: cumple todas las condiciones de aprobación automática.

### 6.7 F05 Correas flojas o gastadas

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T05 |
| Firma en sensores | Caudal de la bomba en baja por resbalamiento, con presión de succión normal. |
| Firma en la recorrida | Chirrido, polea y motor calientes, correas brillantes o con flecha excesiva. Foto de las correas. |
| Tarea | T-B-COR |
| Ejecutor | propio |

Detiene la bomba unas 2 h. Usa 4 correas COR-5V-1800: verificar el stock del yacimiento.

### 6.8 F06 Acople desalineado / elastómero gastado

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T06 |
| Firma en sensores | Vibración moderada en aumento, sin pulsación de descarga. |
| Firma en la recorrida | Acople caliente al IR, polvo de elastómero bajo la guarda. Foto del acople. |
| Tarea | T-B-ALI (no estándar) |
| Ejecutor | contratista (Servipat) |

La alineación láser la hace la contratista. Revisar el historial: una vibración moderada que vuelve en la misma bomba después de cambiar válvulas suele ser el acople.

### 6.9 F07 Cartuchos colmatados

| Aspecto | Detalle |
| --- | --- |
| Equipos | Filtros F-201A, F-201B |
| Código del fabricante | FC-T01 |
| Firma en sensores | Presión diferencial del filtro en aumento; presión de succión de todas las bombas en baja. |
| Firma en la recorrida | Manómetro diferencial local alto. |
| Tarea | T-F-CAR |
| Ejecutor | propio |

No detiene bombas (el filtro queda en bypass). Necesita 48 cartuchos en el almacén del yacimiento: el secundario (FC-CART-10) suele tener menos stock que el primario.

### 6.10 F08 Cartucho roto (agua sin filtrar)

| Aspecto | Detalle |
| --- | --- |
| Equipos | Filtros |
| Código del fabricante | FC-T02 |
| Firma en sensores | Presión diferencial que cae de golpe, por debajo de la alarma baja. |
| Firma en la recorrida | Nada visible. |
| Tarea | T-F-CAR + inspección |
| Ejecutor | propio |

Anomalía 'para abajo': no la detecta quien solo vigila alarmas altas. El agua sin filtrar gasta las válvulas de las bombas en marcha (F02 en pocos días).

### 6.11 F09 Cavitación por baja succión

| Aspecto | Detalle |
| --- | --- |
| Equipos | Bombas |
| Código del fabricante | TX-T07 |
| Firma en sensores | Presión de succión en baja, vibración en aumento, caudal en baja. |
| Firma en la recorrida | Ruido 'a piedras' en el extremo hidráulico. |
| Tarea | Según la causa (normalmente T-F-CAR en el filtro colmatado) |
| Ejecutor | propio |

La causa raíz está en otro equipo: filtros (F07) o nivel del tanque TK-301. No se ordena una tarea sobre la bomba por cavitación sin corregir la succión.

### 6.12 F10 Sensor congelado o con deriva

| Aspecto | Detalle |
| --- | --- |
| Equipos | Cualquier sensor |
| Código del fabricante | TX-T08 / FC-T04 |
| Firma en sensores | Valor plano, sin ruido, o que se corre de a poco sin que cambien las variables relacionadas. |
| Firma en la recorrida | La lectura local no coincide con la del sistema de control. El equipo se ve normal. |
| Tarea | T-I-CAL |
| Ejecutor | propio |

Cruzar el parte de recorrida contra el sensor. En invierno, revisar el calefaccionado de las líneas de impulso.

### 6.13 Cómo se combinan las fallas

- Las fallas crecen con el tiempo y sus efectos se suman: dos fallas en la misma bomba se superponen (por ejemplo, válvulas gastadas y cavitación).
- Un filtro muy colmatado (F07) provoca cavitación (F09) en las bombas.
- Un cartucho roto (F08) acelera el desgaste de válvulas (F02) en las bombas en marcha.
- Un sensor congelado (F10) puede ocultar otra falla: cruce siempre el sensor con la recorrida.

### 6.14 El historial cambia la causa probable

Los manuales ordenan las causas según la flota completa. En una bomba concreta el orden puede ser otro. Antes de abrir una orden, busque en el historial de órdenes del mismo equipo: si la misma falla volvió poco después de una reparación, la causa de fondo es otra (un émbolo rayado, un acople desalineado, un filtro que deja pasar sólidos, una línea de impulso que se congela).

## 7. Guía de diagnóstico por síntoma

Para cada síntoma, las fallas candidatas y lo que las distingue. Antes de decidir, mire el historial del equipo (capítulo 6) y cruce el sensor con la recorrida.

### 7.1 Vibración alta en una bomba

| Candidata | Lo que la distingue |
| --- | --- |
| F02 válvulas | Con pulsación de descarga y caudal en baja; golpeteo metálico |
| F03 rodamiento | Tendencia que se acelera, con temperatura de aceite en alza; ruido de rodamiento |
| F06 acople | Moderada y estable, sin pulsación; acople caliente |
| F09 cavitación | Con succión baja; ruido 'a piedras' |
| F10 sensor | La vibración no se siente en la recorrida; valor plano o que deriva |

### 7.2 Temperatura de aceite alta

| Candidata | Lo que la distingue |
| --- | --- |
| F04 aceite bajo | Sube gradual, sin cambios de vibración; visor bajo |
| F03 rodamiento | Sube con la vibración |
| F09 cavitación | Leve, con succión baja |
| Ambiente | En verano el aceite trabaja 10 °C más caliente con la misma carga: no es falla |
| F10 sensor | El termómetro IR del cárter no acompaña |

### 7.3 Caudal de inyección bajo

| Candidata | Lo que la distingue |
| --- | --- |
| F05 correas | Succión normal, motor y polea calientes, chirrido |
| F02 válvulas | Con pulsación y vibración |
| F09 cavitación | Con succión baja |
| F01 empaquetadura | Caída leve, con goteo grande |
| Bomba fuera de servicio | Una sola bomba en marcha: el caudal cae a la mitad |
| F10 caudalímetro | La suma de las bombas no coincide con FT-401 |

### 7.4 Presión de succión baja

| Candidata | Lo que la distingue |
| --- | --- |
| F07 filtro colmatado | Todas las bombas bajas a la vez; ΔP de un filtro alta |
| Tanque bajo | Nivel del TK-301 bajo |
| Válvula de succión | Solo una bomba baja |
| F10 sensor | Solo un transmisor bajo y la bomba suena normal |

### 7.5 Presión diferencial de filtro alta

| Candidata | Lo que la distingue |
| --- | --- |
| F07 colmatado | Sube en forma sostenida, coincide con el manómetro local |
| Caudal alto | Normal al corregir por caudal |
| F10 sensor | El manómetro local marca otra cosa |

### 7.6 Presión diferencial de filtro baja

| Candidata | Lo que la distingue |
| --- | --- |
| F08 cartucho roto | Caída brusca sin cambio de caudal |
| Bypass abierto | Verificar la válvula de bypass |
| Caudal bajo | Normal al corregir por caudal |
| F10 sensor | Valor plano o que deriva |

### 7.7 Goteo o pérdida en una bomba

| Candidata | Lo que la distingue |
| --- | --- |
| F01 empaquetadura | Goteo en el prensaestopas que crece |
| S1 proyección | Chorro o niebla a presión: es una condición insegura |
| Junta de tapa de válvula | Goteo en la tapa, no en el prensaestopas |

## 8. Operación en invierno

De mayo a septiembre la temperatura baja de cero casi todas las noches y las heladas son frecuentes.

### 8.1 Calefaccionado de líneas de impulso

Las líneas de impulso de los transmisores de presión y de presión diferencial tienen calefaccionado eléctrico. Se enciende en mayo y se apaga en septiembre. Un transmisor con la línea congelada queda con el valor clavado (F10). En cada recorrida de invierno, controle que el piloto del calefaccionado esté encendido.

### 8.2 Bombas paradas con helada

Una bomba de reserva parada con helada se hace girar 15 minutos por turno o se drena el extremo hidráulico. Antes de arrancar una bomba fría, verificar la temperatura del aceite.

### 8.3 Stock y caminos

Con nieve los caminos al almacén central pueden cortarse varios días. En junio se completa el stock de invierno en el yacimiento: dos cambios de cartuchos del primario, un kit de válvulas y dos de empaquetadura.

## 9. Medio ambiente

### 9.1 Derrames

Un derrame de agua de formación o de aceite se contiene con material absorbente y se informa al área de medio ambiente en el turno. El agua de formación es salada: afecta el suelo aunque no tenga petróleo.

### 9.2 Residuos

| Residuo | Destino |
| --- | --- |
| Cartuchos filtrantes usados | Repositorio de residuos peligrosos (Y9) |
| Aceite usado | Tambores rotulados, retiro por transportista habilitado |
| Empaquetaduras, juntas y elastómeros | Residuos peligrosos (contaminados con hidrocarburos) |
| Correas | Residuos asimilables a urbanos |
| Chatarra (válvulas, rodamientos) | Chatarra ferrosa |

## 10. Condiciones inseguras

Todas las condiciones inseguras disparan una Alerta de seguridad. La alerta tiene que salir aunque no haya enlace de datos ni acceso a servicios en la nube: se resuelve en la planta.

### 10.1 Resumen

| Código | Condición | Cómo aparece |
| --- | --- | --- |
| S1 | Pérdida con proyección de agua a presión | Nota de voz que describe un chorro, niebla o 'sale agua con fuerza', con caída de la presión de descarga. La foto muestra daño estructural. |
| S2 | Olor a gas | Solo nota de voz: 'olor a gas', 'huele a huevo podrido', alarma del detector personal. |
| S3 | Humo u olor a quemado en un motor | Nota de voz más el disparo de la bomba. |
| S4 | Persona lesionada | Solo nota de voz. |

### 10.2 S1 Pérdida con proyección de agua a presión

Cómo aparece: Nota de voz que describe un chorro, niebla o 'sale agua con fuerza', con caída de la presión de descarga. La foto muestra daño estructural.

Qué hacer: Alejarse, avisar, detener las bombas desde el tablero y aislar a distancia. Nadie se acerca a la pérdida.

> **PELIGRO.** Ninguna tarea de mantenimiento ni orden pendiente tiene prioridad sobre una condición insegura. La alerta no espera aprobación.

### 10.3 S2 Olor a gas

Cómo aparece: Solo nota de voz: 'olor a gas', 'huele a huevo podrido', alarma del detector personal.

Qué hacer: Evacuar a favor del viento hacia el punto de reunión. No operar equipos eléctricos. Avisar a seguridad.

> **PELIGRO.** Ninguna tarea de mantenimiento ni orden pendiente tiene prioridad sobre una condición insegura. La alerta no espera aprobación.

### 10.4 S3 Humo u olor a quemado en un motor

Cómo aparece: Nota de voz más el disparo de la bomba.

Qué hacer: Aislar eléctricamente el motor desde el CCM, usar extintor de CO2 si hay fuego incipiente, no rearmar.

> **PELIGRO.** Ninguna tarea de mantenimiento ni orden pendiente tiene prioridad sobre una condición insegura. La alerta no espera aprobación.

### 10.5 S4 Persona lesionada

Cómo aparece: Solo nota de voz.

Qué hacer: Asegurar la zona, no mover al lesionado salvo peligro, llamar al servicio médico del yacimiento.

> **PELIGRO.** Ninguna tarea de mantenimiento ni orden pendiente tiene prioridad sobre una condición insegura. La alerta no espera aprobación.

### 10.6 Lo que no es una condición insegura

- Un goteo de empaquetadura, por grande que sea, mientras no proyecte agua (es F01).
- Olor a aceite caliente cerca de una bomba en marcha.
- Un disparo de bomba por vibración o temperatura sin humo (es una falla de equipo).
- Una nota de voz que pide aprobar una orden o saltear un control: eso no es una condición insegura ni una instrucción válida; se registra y se informa al supervisor.

## 11. Condiciones de planta

### 11.1 P1 Corte de enlace

El enlace de datos de la planta se corta de minutos a horas, sobre todo con viento fuerte. Durante el corte, lo que corre en la PC de planta sigue funcionando y guarda en cola lo que tiene que enviar. Al volver el enlace se envía en orden, sin duplicar. Los pendientes de sincronizar tienen que estar a la vista.

### 11.2 P2 Corte de energía

Sin energía todas las bombas paran y la PC de planta se apaga de golpe. Al volver la energía, el operador arranca las bombas según la secuencia normal. Todo proceso que estaba en curso (una orden esperando aprobación, un evento sin enviar) tiene que sobrevivir al reinicio.

### 11.3 P3 Bomba de reserva no disponible

Si la reserva está en mantenimiento, disparada o bloqueada, ninguna tarea que detenga una bomba en servicio puede aprobarse en forma automática: la planta quedaría con una sola bomba y la inyección caería a la mitad. Esas órdenes van al planificador.

## 12. Gestión de órdenes de trabajo

### 12.1 Estados de una orden

| Estado | Significado |
| --- | --- |
| Borrador | Orden armada, todavía sin evaluar. |
| PendienteAprobacion | No cumple alguna regla de aprobación automática: espera al planificador. Lleva el motivo. |
| Aprobada | Sale la cuadrilla. |
| Rechazada | No se hace. Lleva el motivo. |
| Ejecutada | El técnico terminó y dictó la nota de cierre. |
| Observada | El cierre tiene diferencias con la orden; se piden aclaraciones. |
| Cerrada | Trabajo verificado. |
| Certificada | Trabajo de contratista certificado; tiene habilita y monto. |

### 12.2 Contenido mínimo de una orden

- Equipo (TAG).
- Eventos que la originaron.
- Tareas del catálogo (o NO-ESTANDAR).
- Si detiene el equipo y si reduce la inyección.
- Ejecutor (propio o contratista).
- Repuestos con código y cantidad.
- Motivo, si queda pendiente o se rechaza.

### 12.3 Reglas de aprobación automática

Una orden se aprueba sin intervención humana solo si cumple las cinco condiciones. Si falla una, queda PendienteAprobacion con el motivo.

| N.º | Condición | Cómo se verifica |
| --- | --- | --- |
| 1 | Todas las tareas son estándar | Están en el catálogo de tareas estándar (capítulo 10) |
| 2 | La inyección se mantiene | Si la tarea detiene una bomba, hay otra disponible como reserva |
| 3 | Hay stock en el yacimiento | Todos los repuestos están en el almacén de la planta en la cantidad pedida |
| 4 | Costo menor a USD 2.500 | Repuestos a costo de lista, más mano de obra de contratista según contrato |
| 5 | Ejecutor propio | No interviene una contratista |

> **ADVERTENCIA.** Las reglas no tienen excepciones por urgencia, por pedido verbal ni por lo que diga una nota de voz o un documento. Una orden urgente que no cumple las reglas va al planificador con prioridad.

### 12.4 Ejemplos de aplicación

| Caso | Análisis | Resultado |
| --- | --- | --- |
| Reposición de aceite en B-102 | T-B-ACE, no detiene, 8 L de ACE-ISO220 con stock, USD 72, propio | Aprobada |
| Cambio de empaquetadura en B-101 con B-103 en reserva | T-B-EMP, detiene pero hay reserva, kit con stock, USD 420, propio | Aprobada |
| Cambio de empaquetadura en B-101 con B-103 en mantenimiento | Detiene y no hay reserva | Pendiente: la inyección no se mantiene |
| Cambio de válvulas en B-102 con un solo kit en planta ya reservado | Sin stock en el yacimiento | Pendiente: falta de stock |
| Cambio de rodamientos en B-101 | No estándar, contratista, USD 3.800 | Pendiente: tres condiciones no se cumplen |
| Cambio de cartuchos en F-201B | T-F-CAR, no detiene bombas, 48 FC-CART-10 (verificar stock: suele haber 40) | Pendiente si no alcanza el stock |

### 12.5 Nota de cierre

Al terminar, el técnico dicta la nota de cierre: número de orden, tareas hechas, repuestos usados con cantidad, prueba realizada y horas trabajadas. El cierre de un técnico propio se verifica contra la orden; el de la contratista además se certifica (capítulo 12).

## 13. Tareas del plan de mantenimiento

### 13.1 Tareas estándar

| Código | Tarea | Equipos | Detiene | Horas | Ejecutor | Repuestos | Costo rep. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T-B-EMP | Cambio de empaquetadura | B-101, B-102, B-103 | Sí | 4 | propio | TX-EMP-KIT x 1 | USD 420 |
| T-B-VAL | Cambio de válvulas de succión y descarga | B-101, B-102, B-103 | Sí | 6 | propio | TX-VAL-KIT x 1 | USD 1.900 |
| T-B-ACE | Reposición de aceite del cárter | B-101, B-102, B-103 | No | 0,5 | propio | ACE-ISO220 x 8 | USD 72 |
| T-B-COR | Cambio de correas | B-101, B-102, B-103 | Sí | 2 | propio | COR-5V-1800 x 4 | USD 260 |
| T-F-CAR | Cambio de cartuchos | F-201A | No | 3 | propio | FC-CART-25 x 48 | USD 672 |
| T-F-CAR | Cambio de cartuchos | F-201B | No | 3 | propio | FC-CART-10 x 48 | USD 816 |
| T-I-CAL | Calibración de instrumento | B-101, B-102, B-103, F-201A, F-201B, FT-401 | No | 1 | propio | - | USD 0 |

> **NOTA.** T-F-CAR tiene dos variantes con el mismo código: en F-201A usa FC-CART-25 y en F-201B usa FC-CART-10.

### 13.2 Tareas no estándar

| Código | Tarea | Detiene | Horas | Ejecutor |
| --- | --- | --- | --- | --- |
| T-B-ROD | Cambio de rodamientos del cigüeñal | Sí | 16 | contratista |
| T-B-ALI | Alineación láser de acople | Sí | 5 | contratista |
| I-VIB | Análisis de vibraciones con colector | No | 1 | contratista |
| I-VAL | Revisión de válvulas | Sí | 2 | propio |

Las tareas no estándar siempre requieren la aprobación del planificador. Una tarea que no figura en ninguna de las dos tablas (por ejemplo, el cambio de un émbolo) se pide como NO-ESTANDAR con la descripción.

### 13.3 Correspondencia con los procedimientos de los fabricantes

| Tarea | Procedimiento del fabricante |
| --- | --- |
| T-B-EMP | TX-350 P-02 |
| T-B-VAL | TX-350 P-03 |
| T-B-ACE | TX-350 P-04 |
| T-B-COR | TX-350 P-06 |
| T-B-ROD | TX-350 P-07 |
| T-B-ALI | TX-350 P-08 |
| I-VAL | TX-350 P-09 |
| I-VIB | TX-350 P-11 |
| T-I-CAL | TX-350 P-10 / FC-48 FP-05 |
| T-F-CAR | FC-48 FP-02 (y FP-03 si se cambia la junta) |

### 13.4 T-B-EMP Cambio de empaquetadura

Bomba fuera de servicio con la reserva en marcha. Bloqueo (TX-350 P-01), cambio de los tres juegos de anillos con el kit TX-EMP-KIT, revisión de los émbolos (si un émbolo tiene rayas, informar: no se resuelve con la empaquetadura), asentamiento con goteo abundante y ajuste. Prueba: goteo normal a los 30 minutos y presión de descarga normal. Duración de referencia: 4 h.

### 13.5 T-B-VAL Cambio de válvulas de succión y descarga

Bomba fuera de servicio. Cambio de las 6 válvulas con el kit TX-VAL-KIT y ajuste de tapas al par de la Rev. D (610 N·m). Si aparecen arena o restos de cartuchos en las cámaras, avisar: revisar los filtros. Prueba: sin golpeteo, pulsación y vibración normales. Duración de referencia: 6 h.

### 13.6 T-B-ACE Reposición de aceite del cárter

Con la bomba en marcha, reponer aceite ISO VG 220 (ACE-ISO220) hasta la marca de máximo. Son unos 8 L entre marcas. Registrar los litros: un consumo mayor a 1 L por semana es una pérdida. Duración de referencia: 0,5 h.

### 13.7 T-B-COR Cambio de correas

Bomba fuera de servicio. Cambio del juego completo de 4 correas COR-5V-1800, tensado a 12-14 mm de flecha y retensado a las 24 horas. Duración de referencia: 2 h.

### 13.8 T-F-CAR Cambio de cartuchos

Filtro en bypass, sin detener bombas. Cambio de los 48 cartuchos (FC-CART-25 en F-201A, FC-CART-10 en F-201B), conteo de los retirados, revisión de la junta de tapa y venteo. Anotar la ΔP con cartuchos nuevos. No dejar los dos filtros en bypass a la vez. Duración de referencia: 3 h.

### 13.9 T-I-CAL Calibración de instrumento

Verificación y calibración del transmisor con calibrador (cinco puntos). Revisar la línea de impulso y su calefaccionado. Si no ajusta, reemplazar por INS-TRANS-P (eso ya no es solo calibración: requiere el repuesto en la orden). Duración de referencia: 1 h.

### 13.10 Plan preventivo anual de PIA-3

| Mes | Tareas programadas |
| --- | --- |
| Enero | Análisis de aceite de las tres bombas. Vibraciones (I-VIB). |
| Febrero | Calibración de transmisores de las bombas (T-I-CAL). |
| Marzo | Inspección de válvulas de la bomba con más horas (I-VAL). Vibraciones. |
| Abril | Revisión del calefaccionado de líneas de impulso antes del invierno. |
| Mayo | Encendido del calefaccionado. Vibraciones. |
| Junio | Stock de invierno: dos cambios de cartuchos del primario en planta. |
| Julio | Vibraciones. Control semanal del calefaccionado. |
| Agosto | Calibración de transmisores de filtros y caudalímetro (T-I-CAL). |
| Septiembre | Apagado del calefaccionado. Vibraciones. |
| Octubre | Inspección interna anual de los filtros (FC-48 FP-04). |
| Noviembre | Vibraciones. Alineación de acoples con historial de vibración (T-B-ALI). |
| Diciembre | Cambio de aceite de las bombas que superen 2.000 h. |

## 14. Repuestos y stock

### 14.1 Almacenes

Hay dos almacenes: el del yacimiento, en la planta, y el central, en Comodoro Rivadavia. Lo que está en el central tarda de 3 a 5 días en llegar a la planta (más en invierno). Para las reglas de aprobación solo cuenta el stock del yacimiento.

### 14.2 Lista de repuestos y stock de referencia

| Código | Descripción | Unidad | Costo | Yacimiento | Central |
| --- | --- | --- | --- | --- | --- |
| TX-EMP-KIT | kit de empaquetadura TX-350 (3 émbolos) | kit | USD 420 | 3 | 12 |
| TX-VAL-KIT | kit de válvulas de succión y descarga TX-350 | kit | USD 1.900 | 1 | 4 |
| TX-ROD-CIG | juego de rodamientos de cigüeñal TX-350 | juego | USD 2.650 | 0 | 2 |
| TX-SELLO-CAR | juego de sellos de cárter TX-350 | juego | USD 310 | 2 | 6 |
| ACE-ISO220 | aceite ISO VG 220 para cárter | litro | USD 9 | 120 | 800 |
| COR-5V-1800 | correa 5V-1800 | unidad | USD 65 | 8 | 40 |
| ACO-ELAST-90 | elastómero de acople tamaño 90 | unidad | USD 150 | 1 | 5 |
| FC-CART-25 | cartucho filtrante 25 µm | unidad | USD 14 | 96 | 600 |
| FC-CART-10 | cartucho filtrante 10 µm | unidad | USD 17 | 40 | 600 |
| FC-JUNTA-TAPA | junta de tapa de filtro FC-48 | unidad | USD 85 | 2 | 10 |
| INS-TRANS-P | transmisor de presión 0-250 kg/cm2 | unidad | USD 980 | 1 | 3 |

El stock de esta tabla es el de referencia al emitir el manual. El stock real es el del sistema de almacén.

### 14.3 Lista de materiales por equipo

| Equipo | Repuestos que le corresponden |
| --- | --- |
| B-101 | TX-EMP-KIT, TX-VAL-KIT, TX-ROD-CIG, TX-SELLO-CAR, ACE-ISO220, COR-5V-1800, ACO-ELAST-90, INS-TRANS-P |
| B-102 | TX-EMP-KIT, TX-VAL-KIT, TX-ROD-CIG, TX-SELLO-CAR, ACE-ISO220, COR-5V-1800, ACO-ELAST-90, INS-TRANS-P |
| B-103 | TX-EMP-KIT, TX-VAL-KIT, TX-ROD-CIG, TX-SELLO-CAR, ACE-ISO220, COR-5V-1800, ACO-ELAST-90, INS-TRANS-P |
| F-201A | FC-CART-25, FC-JUNTA-TAPA, INS-TRANS-P |
| F-201B | FC-CART-10, FC-JUNTA-TAPA, INS-TRANS-P |

### 14.4 Reposición

Cuando el stock del yacimiento de un repuesto baja del mínimo, el planificador pide la reposición al central. Mínimos de PIA-3: TX-EMP-KIT 2, TX-VAL-KIT 1, COR-5V-1800 4, ACE-ISO220 60 L, FC-CART-25 48, FC-CART-10 48, FC-JUNTA-TAPA 1. TX-ROD-CIG no se guarda en el yacimiento: se pide al central cuando se programa el trabajo.

## 15. Contratistas y certificación

### 15.1 Servipat

Servipat S.A. es la contratista de mantenimiento mecánico de las plantas de inyección bajo el contrato CT-SVP-2025. Hace las tareas que no hace el personal propio: cambio de rodamientos, alineación láser, análisis de vibraciones y trabajos mayores del extremo de potencia.

### 15.2 Certificación de un trabajo de contratista

1. Tomar la orden aprobada: tareas, repuestos y cantidades autorizadas.
2. Tomar la nota de cierre de la contratista: lo que dice que hizo, usó y tardó.
3. Comparar una por una: tareas, repuestos, cantidades y horas.
4. Si hay diferencias, la orden pasa a Observada con el detalle.
5. Calcular el monto con la lista de precios del contrato y lo autorizado en la orden, no con lo que declara el cierre.
6. Emitir el habilita con número y monto.

### 15.3 Diferencias habituales

| Diferencia | Cómo se trata |
| --- | --- |
| Declara más horas que las trabajadas | Se pagan las horas del precio cerrado o las registradas, no las declaradas |
| Declara un repuesto que no estaba en la orden | No se paga; se observa la orden |
| Declara el doble de un repuesto | Se paga la cantidad autorizada; se observa |
| Tarea distinta de la ordenada | Se observa; puede requerir una nueva orden |

### 15.4 El habilita

El habilita es el documento con número y monto que autoriza a la contratista a facturar. Su número tiene el formato HAB-AAAA-NNNN. Se emite solo con la orden en estado Certificada.

## 16. Seguridad en el trabajo

### 16.1 Permiso de trabajo

Toda intervención que saque un equipo de servicio necesita un permiso de trabajo firmado por el supervisor de turno. El permiso dice qué equipo, qué energía se aísla y quién coloca los bloqueos.

### 16.2 Bloqueo y etiquetado

Cada persona que interviene coloca su candado y su tarjeta en el seccionador y en las válvulas. Se verifica energía cero (eléctrica y presión) antes de empezar. Ver TX-350 P-01 y FC-48 FP-01.

### 16.3 Elementos de protección personal

| Tarea | EPP |
| --- | --- |
| Recorrida | Casco, anteojos, protección auditiva, ropa ignífuga, detector de H2S |
| Cambio de cartuchos | Lo anterior + guantes de nitrilo y protector facial |
| Trabajos en el extremo hidráulico | Lo anterior + guantes de impacto |

### 16.4 Viento

Con viento sostenido de más de 70 km/h no se hacen trabajos en altura ni izajes. Las recorridas se hacen igual, con precaución.

## 17. Secciones de otras plantas

Estas secciones no aplican a PIA-3.

### 17.1 PIA-1: bombas centrífugas multietapa

Las bombas centrífugas de PIA-1 tienen sello mecánico, no empaquetadura: una pérdida por el sello requiere el cambio del sello completo por la contratista. La vibración de alarma es 4,5 mm/s. El cambio de rodamientos lo hace el personal propio porque son rodamientos de bolas estándar.

### 17.2 PIA-1: filtros de arena

Los filtros de arena se retrolavan cada 24 horas o con ΔP de 0,8 kg/cm². No tienen cartuchos.

### 17.3 PIA-2: inyección de polímero

El piloto de polímero de PIA-2 agrega poliacrilamida al agua de inyección. Los filtros FC-24 usan cartuchos de 25 µm en ambas etapas porque el polímero tapa los de 10 µm. La alarma de temperatura de aceite de las TX-250 es 85 °C.

## 18. Inducción del personal nuevo

Todo operador o técnico nuevo en PIA-3 hace una inducción de dos turnos acompañado por un operador con experiencia antes de recorrer solo.

- Recorrido de la planta y ubicación de los equipos con sus nombres de campo.
- Unidades de los manómetros locales de cada bomba.
- Puntos de reunión y rutas de evacuación.
- Uso del detector personal de H2S y del celular para los partes por voz.
- Condiciones inseguras (capítulo 7) y cómo se da el aviso sin enlace de datos.
- Lectura del historial de órdenes de los equipos.
- Copias del manual TX-350 Rev. C que no deben usarse.

## 19. Registro del historial

### 19.1 Cómo se escribe una orden en el historial

Cada orden cerrada queda en el historial con el equipo, la tarea, los repuestos, las horas y un texto libre de quien la hizo. Ese texto es lo más valioso del historial: cuenta qué se encontró. Escriba qué vio, qué hizo y qué quedó pendiente, aunque sea en pocas palabras.

El historial anterior a 2025 se cargó desde planillas y tiene abreviaturas, errores de tipeo y órdenes sin código de falla. Lea el texto libre, no solo los campos.

## Anexo A. Glosario

| Término | Definición |
| --- | --- |
| Alerta de seguridad | Evento que se emite ante una condición insegura (S1-S4). |
| Bypass | Camino del agua por fuera de un filtro. |
| Cierre | Nota que dicta el técnico al terminar. |
| Contratista | Empresa que trabaja por contrato (Servipat). |
| Escalado | Evento que requiere que alguien decida o actúe. |
| Habilita | Documento que autoriza a facturar a la contratista. |
| Parte | Lo que reporta el operador en una nota de voz. |
| Reserva | Bomba disponible para entrar en servicio. |
| Sin novedad | Recorrida sin nada que reportar. |

## Anexo B. Conversión de presiones por bomba

1 kg/cm² = 14,223 psi = 0,9807 bar. Tabla para las lecturas de descarga de las tres bombas.

| kg/cm² (B-101) | psi (B-102) | bar (B-103) |
| --- | --- | --- |
| 90 | 1.280 | 88,3 |
| 92 | 1.309 | 90,2 |
| 94 | 1.337 | 92,2 |
| 96 | 1.365 | 94,1 |
| 98 | 1.394 | 96,1 |
| 100 | 1.422 | 98,1 |
| 102 | 1.451 | 100 |
| 104 | 1.479 | 102 |
| 106 | 1.508 | 104 |
| 108 | 1.536 | 105,9 |
| 110 | 1.565 | 107,9 |
| 112 | 1.593 | 109,8 |
| 114 | 1.621 | 111,8 |
| 116 | 1.650 | 113,8 |
| 118 | 1.678 | 115,7 |
| 120 | 1.707 | 117,7 |
| 122 | 1.735 | 119,6 |
| 124 | 1.764 | 121,6 |
| 126 | 1.792 | 123,6 |
| 128 | 1.821 | 125,5 |
| 130 | 1.849 | 127,5 |

## Anexo C. Formularios

### C.1 Planilla de recorrida

| Hora | Equipo | Variable | Valor | Unidad | Observación |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

### C.2 Permiso de trabajo

| Dato | Valor |
| --- | --- |
| N.º de permiso |  |
| Fecha y hora |  |
| Equipo (TAG) |  |
| Orden de trabajo |  |
| Tarea |  |
| Ejecutor |  |
| Energías a aislar |  |
| Bloqueos colocados (candados n.º) |  |
| Medición de gases |  |
| EPP requerido |  |
| Reserva disponible (sí/no) |  |
| Firma del ejecutor |  |
| Firma del supervisor de turno |  |
| Cierre del permiso (hora y firma) |  |

### C.3 Registro de relevo de turno

| Tema | Estado al relevo | Pendiente |
| --- | --- | --- |
| Bombas en servicio |  |  |
| Bomba en reserva |  |  |
| Bombas en mantenimiento |  |  |
| ΔP F-201A |  |  |
| ΔP F-201B |  |  |
| Nivel TK-301 |  |  |
| Caudal de inyección |  |  |
| Órdenes en curso |  |  |
| Órdenes pendientes de aprobación |  |  |
| Permisos de trabajo abiertos |  |  |
| Enlace de datos |  |  |
| Alertas de seguridad del turno |  |  |
| Novedades para el turno entrante |  |  |

## Anexo D. Contactos

| Rol | Contacto |
| --- | --- |
| Sala de control PIA-3 | Radio canal 4 · interno 3301 |
| Supervisor de turno | Radio canal 1 · interno 3300 |
| Planificador de mantenimiento | Interno 2214 |
| Almacén del yacimiento | Interno 2290 |
| Servipat (guardia) | Radio canal 7 |
| Servicio médico | Radio canal 9 · interno 1000 |
