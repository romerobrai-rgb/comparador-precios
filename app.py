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

def cargar_configuracion():
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "marcas": ["Coca Cola", "Arcor", "Campanita", "Ayudin", "Cif", "Palmolive", "Carrefour", "Coto", "La Serenisima"],
        "productos": ["Gaseosa 1.5 Lts", "Aceite 1.5 Lts", "Lavandina 1 Lt", "Rollo de cocina x 3", "Jabon Liquido 500ml", "Leche 1 Lt"],
        "supermercados": ["Coto", "Carrefour", "Jumbo", "Dia", "ChangoMas", "Disco"]
    }

def guardar_configuracion(data):
    with open(ARCHIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

config_data = cargar_configuracion()

# Inicializar listas en memoria
for key in ["marcas", "productos", "supermercados"]:
    if key not in st.session_state:
        st.session_state[key] = sorted(config_data[key])

if "datos_alv" not in st.session_state:
    st.session_state.datos_alv = []

if "num_opciones" not in st.session_state:
    st.session_state.num_opciones = 2

promociones = [
    "Sin Promo", "2do 80% Off", "2do 70% Off", "2do 50% Off", 
    "3x2", "4x3", "2x1", "10% Off", "20% Off", "25% Off", "30% Off", "40% Off", "50% Off"
]

# --- 2. LÓGICA DE CÁLCULO ---
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
    elif promo.endswith("% Off"):
        descuento = float(promo.replace("% Off", "")) / 100
        total_con_promo = total_sin_promo * (1 - descuento)
    else:
        total_con_promo = total_sin_promo
        
    return total_con_promo / cantidad, total_sin_promo, total_con_promo

# --- 3. MENÚ LATERAL: ADMINISTRACIÓN ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    with st.expander("Administrar Marcas"):
        nueva_marca = st.text_input("Nueva Marca:")
        if st.button("Agregar Marca") and nueva_marca:
            if nueva_marca not in st.session_state.marcas:
                st.session_state.marcas.append(nueva_marca)
                guardar_configuracion({"marcas": st.session_state.marcas, "productos": st.session_state.productos, "supermercados": st.session_state.supermercados})
                st.rerun()
                
    with st.expander("Administrar Productos"):
        nuevo_prod = st.text_input("Nuevo Producto:")
        if st.button("Agregar Producto") and nuevo_prod:
            if nuevo_prod not in st.session_state.productos:
                st.session_state.productos.append(nuevo_prod)
                guardar_configuracion({"marcas": st.session_state.marcas, "productos": st.session_state.productos, "supermercados": st.session_state.supermercados})
                st.rerun()

    with st.expander("Administrar Supermercados"):
        nuevo_super = st.text_input("Nuevo Supermercado:")
        if st.button("Agregar Super") and nuevo_super:
            if nuevo_super not in st.session_state.supermercados:
                st.session_state.supermercados.append(nuevo_super)
                guardar_configuracion({"marcas": st.session_state.marcas, "productos": st.session_state.productos, "supermercados": st.session_state.supermercados})
                st.rerun()

# --- 4. INTERFAZ PRINCIPAL ---
st.subheader("Ingreso de Datos")
col_m, col_p, col_c = st.columns([1, 2, 1])
with col_m: marca = st.selectbox("Marca", sorted(st.session_state.marcas))
with col_p: producto = st.selectbox("Producto", sorted(st.session_state.productos))
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

for i in range(st.session_state.num_opciones):
    with cols_super[i]:
        st.markdown(f"**Opción {i+1}**")
        superm = st.selectbox(f"Supermercado {i+1}", ["-"] + sorted(st.session_state.supermercados), index=0, key=f"sup_{i}")
        precio_base = st.number_input(f"Precio Base $", min_value=0.0, step=100.0, key=f"precio_{i}")
        promo = st.selectbox(f"Promoción", promociones, key=f"promo_{i}")
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
                # Flag invisible para saber si tuvo promo al calcular el medio de pago
                f"Tuvo Promo {i+1}": op["promo"] != "Sin Promo" 
            })
            
    ahorro = max(mejor_sp - mejor_precio, 0.0) if mejor_precio != float('inf') else 0.0
    fila_export["Mejor Opción"] = mejor_opcion
    fila_export["Ahorro Generado"] = ahorro
    
    st.session_state.datos_alv.append(fila_export)
    st.success("¡Producto agregado!")

# --- 5. VISUALIZADOR Y EXPORTACIÓN ---
if st.session_state.datos_alv:
    st.subheader("Lista de Compras Acumulada")
    df = pd.DataFrame(st.session_state.datos_alv)
    
    # Ocultar las columnas internas de "Tuvo Promo" para la vista de la tabla
    cols_visibles = [c for c in df.columns if "Tuvo Promo" not in c]
    df_visual = df[cols_visibles]
    
    column_config = {}
    for col in df_visual.columns:
        if "Precio Base" in col:
            column_config[col] = st.column_config.NumberColumn("Precio Base", format="$ %.2f")
        elif any(kw in col for kw in ["Unitario", "Total", "Ahorro"]):
            column_config[col] = st.column_config.NumberColumn(format="$ %.2f")
            
    st.dataframe(df_visual, use_container_width=True, column_config=column_config)
    
    # --- 6. DESCUENTOS BANCARIOS / MEDIOS DE PAGO ---
    st.divider()
    st.subheader("💳 Descuentos por Medio de Pago (Final del Carrito)")
    
    super_cols = [c for c in df.columns if re.match(r"Supermercado \d+", c)]
    num_supermercados_df = len(super_cols)
    cols_pagos = st.columns(num_supermercados_df)
    
    for idx, col_name in enumerate(super_cols):
        i = idx + 1
        # Obtener el nombre del super predominante en esa columna
        super_nombre = df[col_name].mode()[0] if not df[col_name].dropna().empty else f"Opción {i}"
        
        with cols_pagos[idx]:
            st.markdown(f"#### {super_nombre}")
            desc_str = st.selectbox("Descuento Bancario:", ["0%", "15%", "20%", "30%"], key=f"desc_pago_{i}")
            acumulable = st.checkbox("Acumula con otras promos", value=True, key=f"acum_{i}")
            
            porc = int(desc_str.replace("%", "")) / 100
            
            # Asegurar que las columnas existan antes de sumar
            if f"Total c/Promo {i}" in df.columns and f"Tuvo Promo {i}" in df.columns:
                total_bruto = df[f"Total c/Promo {i}"].fillna(0).sum()
                items_sin_promo = df[df[f"Tuvo Promo {i}"] == False][f"Total c/Promo {i}"].fillna(0).sum()
                
                if acumulable:
                    descuento = total_bruto * porc
                else:
                    descuento = items_sin_promo * porc
                    
                total_final = total_bruto - descuento
                
                st.write(f"Total Carrito: **${total_bruto:,.2f}**")
                st.write(f"Descuento Extra: **-${descuento:,.2f}**")
                st.success(f"**Total a Pagar: ${total_final:,.2f}**")
            else:
                st.info("Sin artículos")

    st.divider()
    # Exportar a Excel (Limpiando las columnas ocultas)
    @st.cache_data
    def convertir_df(df_limpio):
        return df_limpio.to_csv(index=False).encode('utf-8')
        
    csv = convertir_df(df_visual)
    
    col_dl, col_del = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Descargar Lista (CSV para Excel)",
            data=csv,
            file_name='lista_de_compras.csv',
            mime='text/csv',
        )
    with col_del:
        if st.button("🗑️ Borrar Lista Completa"):
            st.session_state.datos_alv = []
            st.rerun()
