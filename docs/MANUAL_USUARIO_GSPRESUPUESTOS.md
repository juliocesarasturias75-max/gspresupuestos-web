# Manual de usuario — GSpresupuestos Web

**Versión:** 2.0  
**Empresa:** SECO PVC / Aluminios Seco  
**Acceso:** https://www.gspresupuestos.aluminiosseco.com  

---

## 1. ¿Qué es GSpresupuestos?

GSpresupuestos es una herramienta web para que los **distribuidores autorizados** generen presupuestos de ventanas a partir de los archivos exportados por Aluminios Seco, apliquen márgenes y colocación, y obtengan un **PDF profesional** con su logo y datos de empresa.

---

## 2. Acceso y primer uso

### 2.1 Entrar en la aplicación

1. Abra el navegador (Chrome, Edge o Firefox recomendados).
2. Vaya a: **https://www.gspresupuestos.aluminiosseco.com**
3. Introduzca el **email** y **contraseña** que le haya facilitado el administrador.
4. Pulse **Entrar**.

> **Importante:** Use siempre la dirección con **www**. Guarde la página en favoritos.

### 2.2 Si olvida la contraseña

Contacte con el administrador de SECO PVC para que le restablezca la clave. No hay recuperación automática por email.

---

## 3. Flujo de trabajo (paso a paso)

### Paso 1 — Cargar archivos

| Botón | Archivo | ¿Obligatorio? |
|-------|---------|---------------|
| **Subir TXT** | Archivo de presupuesto de Aluminios Seco | **Sí** |
| **Subir PDF (dibujos)** | PDF con dibujos de las ventanas | Recomendado |
| **Subir Condiciones** | Texto de condiciones de venta | Opcional |

- El **TXT** debe ser el generado por el sistema de Aluminios Seco (contiene partidas y precios).
- El **PDF** asocia los dibujos a cada partida por orden.
- Si el número de partidas del TXT y de dibujos del PDF **no coincide**, la aplicación mostrará un **aviso de desajuste**. Revíselo antes de enviar el presupuesto al cliente.

### Paso 2 — Datos del cliente

Rellene en el panel izquierdo:

- **Nº Oferta**
- **Cliente**
- **Dirección, Teléfono, Email** (recomendado)
- **Referencia** (obra, vivienda, etc.)

### Paso 3 — Aplicar márgenes

1. Indique **Beneficio (%)** — por defecto 20 %.
2. Indique **Colocación (€)** — por defecto 50 €.
3. Pulse **Aplicar márgenes**.

La tabla mostrará coste, colocación, margen, PVP y total por partida, además de los totales del presupuesto.

> Puede editar márgenes o colocación **por partida** haciendo clic en las celdas de la tabla o con **Editar partida**.

### Paso 4 — Notas (opcional)

- **Nota para todos los modelos:** aparece al final de cada partida en el PDF.
- **Nota por partida:** desde **Editar partida**.

### Paso 5 — Generar PDF

| Botón | Qué hace |
|-------|----------|
| **Generar PDF** | Presupuesto para el cliente |
| **Resumen Cálculos (PDF interno)** | Resumen con costes y márgenes (uso interno) |
| **PDF + Fichas técnicas** | Presupuesto + fichas PDF que el admin haya subido (si están disponibles) |

El PDF incluirá su **logo** y **pie de página** configurados en **Mi perfil**.

---

## 4. Guardar y cargar ofertas

### Guardar una oferta

1. Pulse **Guardar oferta**.
2. Ponga un nombre claro (ej.: `120_PEPE_GARAJE`).
3. Pulse **Guardar**.

### Cargar una oferta guardada

1. Pulse **Cargar oferta**.
2. Elija la oferta de la lista.
3. Pulse **Abrir**.

> Al cargar una oferta guardada, **no podrá volver a subir TXT ni PDF** (para evitar mezclar datos). Si necesita archivos nuevos, pulse **Nueva oferta**.

### Nueva oferta

Borra lo que hay en pantalla y empieza de cero. **No elimina** las ofertas ya guardadas.

---

## 5. Mi perfil

Desde el menú superior → **Mi perfil**:

- **Logo** para el PDF (PNG o JPG).
- **Datos de empresa** (nombre, teléfono, email, dirección, CIF).
- **Pie de página** del PDF.
- Hasta **3 plantillas de condiciones** reutilizables.

Configure el perfil **antes** de generar el primer presupuesto.

---

## 6. Alertas y controles

La aplicación puede mostrar **avisos** (cantidades raras, PVP por debajo del coste, presupuesto con pérdida, etc.).

- Los **errores graves** bloquean la generación del PDF hasta corregirlos.
- Los **avisos** permiten continuar bajo su responsabilidad tras confirmar.

**Revise siempre** los importes antes de enviar el presupuesto al cliente.

---

## 7. Consejos prácticos

1. **Revise el PDF** antes de enviarlo al cliente.
2. Use nombres claros al guardar ofertas.
3. Si cambia el TXT de Aluminios Seco, cree una **nueva oferta**.
4. Compruebe que el **número de dibujos** coincide con las partidas.
5. No comparta su usuario y contraseña con otras personas.

---

## 8. Problemas frecuentes

| Problema | Solución |
|----------|----------|
| No carga el TXT | Compruebe que es archivo `.txt` de Aluminios Seco |
| Desajuste TXT/PDF | Verifique que subió el PDF correcto para ese TXT |
| No aparece el logo en el PDF | Suba el logo en **Mi perfil** |
| Botón PDF desactivado | Pulse primero **Aplicar márgenes** |
| No ve mis ofertas | Compruebe que entró con su usuario (cada uno ve solo las suyas) |
| La web tarda en cargar | Espere unos segundos y recargue la página |

---

## 9. Soporte

Para incidencias técnicas, nuevos usuarios o restablecer contraseña, contacte con:

**SECO PVC / Administrador GSpresupuestos**  
presupuestos1@aluminiosseco.com

---

*Documento de uso interno para distribuidores autorizados.*
