import streamlit as st
import pandas as pd
import json
import os
import re

# Configuración inicial de la página
st.set_page_config(page_title="Comparador de Precios", layout="wide")

st.title("🛒 Comparador Inteligente de Precios")

# --- 1. GESTIÓN DE DATOS (JSON y Session State) ---
ARCHIVO_CONFIG = "config_opciones.json"

def listas_por_defecto():
    return {
        "marcas": ["Coca Cola", "Arcor", "Campanita", "Ayudin", "Cif", "Palmolive", "Carrefour", "Coto", "La Serenisima"],
        "productos": ["Gaseosa 1.5 Lts", "Aceite 1.5 Lts", "Lavandina 1 Lt", "Rollo de cocina x 3", "Jabon Liquido 500ml", "Leche 1 Lt"],
        "supermercados": ["Coto", "Carrefour", "Jumbo", "Dia", "ChangoMas", "Disco"],
        "promociones": ["Sin Promo", "2do 80% Off", "2do 70% Off", "2do 50% Off", "3x2", "4x3", "2x1", "10% Off", "20% Off", "25% Off", "30% Off", "40% Off", "50% Off"],
        "promos_pago": ["0%", "15%", "20%", "25%", "30%", "35%", "40%"],
        "medios_pago": ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Mercado Pago", "MODO", "Cuenta DNI", "Personal Pay"],
        "topes": ["Sin Tope", "3000", "5000", "8000", "10000", "15000", "20000"]
    }

def cargar_configuracion():
    default_data = listas_por_defecto()
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in default_data.keys():
                    if key not in data:
                        data[key] = default_data[key]
                return data
        except Exception:
            return default_data
    return default_data

def guardar_configuracion():
    data = {key: st.session_state[key] for key in listas_por_defecto().keys()}
    with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

config_data = cargar_configuracion()

# Inicializar listas en memoria
for key, values in config_data.items():
    if key not in st.session_state:
        st.session_state[key] = sorted(values)

if "datos_alv" not in st.session_state:
    st.session_state.datos_alv = []

if "num_opciones" not in st.session_state:
    st.session_state.num_opciones = 2

# Extraer número de un string
def extraer_numero(texto, default=0.0):
    nums = re.findall(r'\d+', str(texto).replace('.', ''))
    return float(nums[0]) if nums else default

# --- 2. LÓGICA DE CÁLCULO DE ARTÍCULOS ---
def calcular_promo(cantidad, precio, promo):
    if cantidad == 0 or precio == 0.0: return 0.0, 0.0, 0.0
    total_sin_promo = cantidad * precio
    
    if promo == "Sin Promo":
        total_con_promo = total_sin_promo
    elif promo == "2do 80% Off":
        pares, sobra = cantidad // 2, cantidad % 2
        total_con_promo = (pares * 1.2 * precio) + (sobra * precio)
    elif promo == "2do 70% Off":
        pares, sobra = cantidad // 2, cantidad % 2
        total_con_promo = (pares * 1.3 * precio) + (sobra * precio)
    elif promo == "2do 50% Off":
        pares, sobra = cantidad // 2, cantidad % 2
        total_con_promo = (pares * 1.5 * precio) + (sobra * precio)
    elif promo == "3x2":
        trios, sobra = cantidad // 3, cantidad % 3
        total_con_promo = (trios * 2 * precio) + (sobra * precio)
    elif promo == "4x3":
        cuartetos, sobra = cantidad // 4, cantidad % 4
        total_con_promo = (cuartetos * 3 * precio) + (sobra * precio)
    elif promo == "2x1":
        pares, sobra = cantidad // 2, cantidad % 2
        total_con_promo = (pares * 1 * precio) + (sobra * precio)
    elif "%" in promo:
        descuento = extraer_numero(promo) / 100
        total_con_promo = total_sin_promo * (1 - descuento)
    else:
        total_con_promo = total_sin_promo
        
    return total_con_promo / cantidad, total_sin_promo, total_con_promo

# --- 3. MENÚ LATERAL: ADMINISTRACIÓN ---
def panel_administracion(clave, titulo):
    with st.expander(f"⚙️ {titulo}"):
        nuevo = st.text_input(f"Agregar {titulo}:", key=f"add_in_{clave}")
        if st.button("Agregar", key=f"btn_add_{clave}") and nuevo:
            if nuevo not in st.session_state[clave]:
                st.session_state[clave].append(nuevo)
                st.session_state[clave].sort()
                guardar_configuracion()
                st.rerun()
        
        if st.session_state[clave]:
            st.divider()
            a_borrar = st.selectbox(f"Eliminar {titulo}:", ["-"] + st.session_state[clave], key=f"del_sel_{clave}")
            if st.button("Eliminar", key=f"btn_del_{clave}") and a_borrar != "-":
                st.session_state[clave].remove(a_borrar)
                guardar_configuracion()
                st.rerun()

with st.sidebar:
    st.header("Panel de Configuración")
    panel_administracion("marcas", "Marcas")
    panel_administracion("productos", "Productos")
    panel_administracion("supermercados", "Supermercados")
    panel_administracion("promociones", "Promociones de Producto")
    panel_administracion("medios_pago", "Medios de Pago")
    panel_administracion("promos_pago", "Descuentos de Pago (%)")
    panel_administracion("topes", "Topes de Reintegro ($)")

# --- 4. INTERFAZ PRINCIPAL ---
st.subheader("Ingreso de Datos")
col_m, col_p, col_c = st.columns([1, 2, 1])
with col_m: marca = st.selectbox("Marca", st.session_state.marcas)
with col_p: producto = st.selectbox("Producto", st.session_state.productos)
with col_c: cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

st.subheader("Comparativa por Supermercado")

col_btn_add, col_btn_rem, _ = st.columns([2, 2, 6])
with col_btn_add:
    if st.button("➕ Agregar Supermercado"):
        st.session_state.num_opciones += 1
        st.rerun()
with col_btn_rem:
    if st.button("➖ Quitar Supermercado"):
        if st.session_state.num_opciones > 2:
            st.session_state.num_opciones -= 1
            st.rerun()
        else:
            st.warning("Debe haber un mínimo de 2 opciones.")

cols_super = st.columns(st.session_state.num_opciones)
opciones = []

lista_promos = st.session_state.promociones.copy()
if "Sin Promo" in lista_promos:
    lista_promos.remove("Sin Promo")
    lista_promos.insert(0, "Sin Promo")

for i in range(st.session_state.num_opciones):
    with cols_super[i]:
        st.markdown(f"**Opción {i+1}**")
        superm = st.selectbox(f"Supermercado {i+1}", ["-"] + st.session_state.supermercados, index=0, key=f"sup_{i}")
        precio_base = st.number_input(f"Precio Base $", min_value=0.0, step=100.0, key=f"precio_{i}")
        promo = st.selectbox(f"Promoción", lista_promos, key=f"promo_{i}")
        opciones.append({"super": superm, "precio": precio_base, "promo": promo})

if st.button("Calcular y Agregar a la Lista", type="primary"):
    mejor_precio = float('inf')
    mejor_opcion = "-"
    mejor_sp = 0.0
    
    fila_export = {"Marca": marca, "Producto": producto, "Cantidad": cantidad}
    
    for i, op in enumerate(opciones):
        if op["super"] != "-":
            unit_cp, tot_sp, tot_cp = calcular_promo(cantidad, op["precio"], op["promo"])
            if tot_cp > 0 and tot_cp < mejor_precio:
                mejor_precio = tot_cp
                mejor_opcion = op["super"]
                mejor_sp = tot_sp
                
            fila_export.update({
                f"Supermercado {i+1}": op["super"],
                f"Precio Base {i+1}": op["precio"],
                f"Unitario c/Promo {i+1}": unit_cp,
                f"Total s/Promo {i+1}": tot_sp,
                f"Total c/Promo {i+1}": tot_cp,
                f"Tuvo Promo {i+1}": op["promo"] != "Sin Promo" 
            })
            
    ahorro = max(mejor_sp - mejor_precio, 0.0) if mejor_precio != float('inf') else 0.0
    fila_export["Mejor Opción"] = mejor_opcion
    fila_export["Ahorro Producto"] = ahorro
    
    st.session_state.datos_alv.append(fila_export)
    st.success("¡Producto agregado!")

# --- 5. VISUALIZADOR Y EXPORTACIÓN (NUEVO FORMATO DE CUADROS) ---
if st.session_state.datos_alv:
    df = pd.DataFrame(st.session_state.datos_alv)
    
    st.divider()
    st.subheader("📊 Análisis por Supermercado")
    
    super_cols = [c for c in df.columns if re.match(r"Supermercado \d+", c)]
    num_supermercados_df = len(super_cols)
    cols_vista = st.columns(num_supermercados_df)
    
    for idx, col_name in enumerate(super_cols):
        i = idx + 1
        super_nombre = df[col_name].mode()[0] if not df[col_name].dropna().empty else f"Opción {i}"
        
        with cols_vista[idx]:
            # Construimos un mini cuadro para este supermercado
            st.markdown(f"### 🛒 {super_nombre}")
            cols_to_keep = ["Producto", "Cantidad", f"Precio Base {i}", f"Total c/Promo {i}"]
            cols_exist = [c for c in cols_to_keep if c in df.columns]
            
            if cols_exist:
                mini_df = df[cols_exist].copy()
                mini_df.rename(columns={f"Precio Base {i}": "Base", f"Total c/Promo {i}": "Total"}, inplace=True)
                
                # Renderiza la tablita individual limpia y sin el número de fila (hide_index)
                st.dataframe(
                    mini_df, 
                    hide_index=True, 
                    use_container_width=True, 
                    column_config={
                        "Base": st.column_config.NumberColumn(format="$ %.2f"),
                        "Total": st.column_config.NumberColumn(format="$ %.2f")
                    }
                )
                total_super = mini_df["Total"].sum() if "Total" in mini_df.columns else 0
                st.info(f"**Subtotal:** ${total_super:,.2f}")

    st.divider()
    
    # Cuadro Final: Producto vs Mejor Opción
    st.subheader("🏆 Resumen de Mejor Opción por Producto")
    
    resumen_df = df[["Marca", "Producto", "Cantidad", "Mejor Opción", "Ahorro Producto"]].copy()
    st.dataframe(
        resumen_df, 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Ahorro Producto": st.column_config.NumberColumn("Ahorro Producto", format="$ %.2f")
        }
    )
    
    ahorro_total = df["Ahorro Producto"].sum()
    st.success(f"💰 **Ahorro Total Estimado (sin tarjetas):** ${ahorro_total:,.2f}")
    
    # --- 6. DESCUENTOS BANCARIOS / MEDIOS DE PAGO ---
    st.divider()
    st.subheader("💳 Calculadora de Pagos (Final del Carrito)")
    
    cols_pagos = st.columns(num_supermercados_df)
    
    for idx, col_name in enumerate(super_cols):
        i = idx + 1
        super_nombre = df[col_name].mode()[0] if not df[col_name].dropna().empty else f"Opción {i}"
        
        with cols_pagos[idx]:
            st.markdown(f"#### {super_nombre}")
            st.selectbox("Medio de Pago:", ["-"] + st.session_state.medios_pago, key=f"medio_pago_{i}")
            
            c1, c2 = st.columns(2)
            with c1: desc_str = st.selectbox("Dcto Banco:", ["0%"] + st.session_state.promos_pago, key=f"desc_pago_{i}")
            with c2: tope_str = st.selectbox("Tope $:", st.session_state.topes, key=f"tope_{i}")
            
            acumulable = st.checkbox("Acumula con otras promos", value=True, key=f"acum_{i}")
            
            porc_descuento = extraer_numero(desc_str) / 100
            tope_reintegro = extraer_numero(tope_str, default=float('inf')) if "Sin Tope" not in str(tope_str) else float('inf')
            
            if f"Total c/Promo {i}" in df.columns and f"Tuvo Promo {i}" in df.columns:
                total_bruto = df[f"Total c/Promo {i}"].fillna(0).sum()
                items_sin_promo = df[df[f"Tuvo Promo {i}"] == False][f"Total c/Promo {i}"].fillna(0).sum()
                
                if acumulable:
                    descuento_calculado = total_bruto * porc_descuento
                else:
                    descuento_calculado = items_sin_promo * porc_descuento
                
                descuento_final = min(descuento_calculado, tope_reintegro)
                total_a_pagar = total_bruto - descuento_final
                
                st.write(f"Total Bruto: **${total_bruto:,.2f}**")
                st.write(f"Reintegro Bancario: **-${descuento_final:,.2f}**")
                st.success(f"🔥 **Total Final a Pagar: ${total_a_pagar:,.2f}**")
            else:
                st.info("Sin artículos cargados")

    st.divider()
    
    # Exportación (El DataFrame crudo, para que Excel tenga todas las columnas)
    cols_visibles_export = [c for c in df.columns if "Tuvo Promo" not in c]
    df_export = df[cols_visibles_export]
    
    @st.cache_data
    def convertir_df(df_limpio):
        return df_limpio.to_csv(index=False).encode('utf-8')
        
    csv = convertir_df(df_export)
    
    col_dl, col_del = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Descargar Análisis Completo (CSV para Excel)",
            data=csv,
            file_name='analisis_supermercados.csv',
            mime='text/csv',
        )
    with col_del:
        if st.button("🗑️ Borrar Lista Completa"):
            st.session_state.datos_alv = []
            st.rerun()
