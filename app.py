import streamlit as st
import pandas as pd
import json
import os
import re

# Configuración inicial de la página
st.set_page_config(page_title="Comparador de Precios Inteligente", layout="wide")

st.title("🛒 Comparador Inteligente de Precios")

# --- 1. GESTIÓN DE DATOS (JSON y Session State) ---
ARCHIVO_CONFIG = "config_opciones.json"
ARCHIVO_CARRITO = "carrito_actual.json"
ARCHIVO_SETUP = "setup_supermercados.json"

def listas_por_defecto():
    return {
        "marcas": ["Coca Cola", "Arcor", "Campanita", "Ayudin", "Cif", "Palmolive", "Carrefour", "Coto", "La Serenisima"],
        "productos": ["Gaseosa 1.5 Lts", "Aceite 1.5 Lts", "Lavandina 1 Lt", "Rollo de cocina x 3", "Jabon Liquido 500ml", "Leche 1 Lt"],
        "supermercados": ["Coto", "Carrefour", "Jumbo", "Dia", "ChangoMas", "Disco"],
        "promociones": ["Sin Promo", "2do 80% Off", "2do 70% Off", "2do 50% Off", "3x2", "4x3", "2x1", "10% Off", "20% Off", "25% Off", "30% Off", "40% Off", "50% Off"],
        "promos_pago": ["0%", "15%", "20%", "25%", "30%", "35%", "40%"],
        "medios_pago": ["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Mercado Pago", "MODO", "Cuenta DNI", "Personal Pay"],
        "topes": ["Sin Tope", "3000", "5000", "8000", "10000", "15000", "20000"],
        "precios_historicos": {} 
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

def cargar_carrito():
    if os.path.exists(ARCHIVO_CARRITO):
        try:
            with open(ARCHIVO_CARRITO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_carrito(carrito_actual):
    with open(ARCHIVO_CARRITO, 'w', encoding='utf-8') as f:
        json.dump(carrito_actual, f, ensure_ascii=False, indent=4)

def cargar_setup():
    if os.path.exists(ARCHIVO_SETUP):
        try:
            with open(ARCHIVO_SETUP, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def guardar_setup(num_opciones, setup_data):
    data = {
        "num_opciones": num_opciones,
        "config_super": setup_data
    }
    with open(ARCHIVO_SETUP, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

config_data = cargar_configuracion()

for key, values in config_data.items():
    if key not in st.session_state:
        st.session_state[key] = values if isinstance(values, dict) else sorted(values)

if "datos_alv" not in st.session_state:
    st.session_state.datos_alv = cargar_carrito()

saved_setup = cargar_setup()
if "num_opciones" not in st.session_state:
    st.session_state.num_opciones = saved_setup["num_opciones"] if saved_setup else 2

def extraer_numero(texto, default=0.0):
    nums = re.findall(r'\d+', str(texto).replace('.', ''))
    return float(nums[0]) if nums else default

# --- 2. LÓGICA MATEMÁTICA DE PRODUCTOS ---
def calcular_promo_producto(cantidad, precio, promo):
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

# --- 3. MENÚ LATERAL: ADMINISTRACIÓN Y RESET ---
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
    
    st.divider()
    st.warning("⚠️ Zona de Peligro")
    if st.button("🔄 REINICIO TOTAL DE COMPRA"):
        if os.path.exists(ARCHIVO_CARRITO): os.remove(ARCHIVO_CARRITO)
        if os.path.exists(ARCHIVO_SETUP): os.remove(ARCHIVO_SETUP)
        st.session_state.datos_alv = []
        st.session_state.num_opciones = 2
        st.success("¡Sistema reiniciado por completo!")
        st.rerun()

# --- 4. CONFIGURACIÓN GLOBAL DE LA COMPRA ---
st.subheader("1️⃣ Configuración de Supermercados y Medios de Pago")
st.caption("Definí dónde y cómo vas a pagar hoy. Estos descuentos se aplicarán automáticamente a cada producto.")

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

config_super = []
cols_setup = st.columns(st.session_state.num_opciones)

for i in range(st.session_state.num_opciones):
    saved_opt = saved_setup["config_super"][i] if saved_setup and "config_super" in saved_setup and i < len(saved_setup["config_super"]) else {}
    
    def_sup = saved_opt.get("nombre", "-")
    def_med = saved_opt.get("medio", "-")
    def_dcto = f"{int(saved_opt.get('dcto_pct', 0)*100)}%" if saved_opt.get('dcto_pct', 0) > 0 else "0%"
    def_tope = str(int(saved_opt.get('tope', 0))) if saved_opt.get('tope', float('inf')) != float('inf') else "Sin Tope"
    def_acum = saved_opt.get("acumulable", True)

    with cols_setup[i]:
        st.markdown(f"**Opción {i+1}**")
        
        sup_idx = st.session_state.supermercados.index(def_sup) + 1 if def_sup in st.session_state.supermercados else 0
        med_idx = st.session_state.medios_pago.index(def_med) + 1 if def_med in st.session_state.medios_pago else 0
        dcto_idx = ["0%"] + st.session_state.promos_pago
        dcto_select_idx = dcto_idx.index(def_dcto) if def_dcto in dcto_idx else 0
        tope_idx = st.session_state.topes.index(def_tope) if def_tope in st.session_state.topes else 0

        s_nombre = st.selectbox(f"Supermercado", ["-"] + st.session_state.supermercados, index=sup_idx, key=f"g_sup_{i}")
        s_medio = st.selectbox(f"Medio de Pago", ["-"] + st.session_state.medios_pago, index=med_idx, key=f"g_med_{i}")
        c1, c2 = st.columns(2)
        with c1: s_dcto = st.selectbox(f"Dcto %", ["0%"] + st.session_state.promos_pago, index=dcto_select_idx, key=f"g_dcto_{i}")
        with c2: s_tope = st.selectbox(f"Tope $", st.session_state.topes, index=tope_idx, key=f"g_tope_{i}")
        s_acum = st.checkbox("Acumula con otras promos", value=def_acum, key=f"g_acum_{i}")
        
        config_super.append({
            "nombre": s_nombre,
            "medio": s_medio,
            "dcto_pct": extraer_numero(s_dcto) / 100,
            "tope": extraer_numero(s_tope, default=float('inf')) if "Sin Tope" not in str(s_tope) else float('inf'),
            "acumulable": s_acum
        })

guardar_setup(st.session_state.num_opciones, config_super)

st.divider()

# --- 5. INGRESO DE PRODUCTOS ---
st.subheader("2️⃣ Carga de Productos")
st.caption("Los precios se autocompletarán automáticamente con lo último que hayas registrado para cada producto.")
col_m, col_p, col_c = st.columns([1, 2, 1])
with col_m: marca = st.selectbox("Marca", st.session_state.marcas)
with col_p: producto = st.selectbox("Producto", st.session_state.productos)
with col_c: cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

cols_items = st.columns(st.session_state.num_opciones)
opciones_item = []

lista_promos = st.session_state.promociones.copy()
if "Sin Promo" in lista_promos:
    lista_promos.remove("Sin Promo")
    lista_promos.insert(0, "Sin Promo")

for i in range(st.session_state.num_opciones):
    nombre_display = config_super[i]["nombre"] if config_super[i]["nombre"] != "-" else f"Opción {i+1}"
    
    # Memoria inteligente de precios previos por producto y supermercado
    precio_guardado = float(st.session_state.precios_historicos.get(producto, {}).get(nombre_display, 0.0))
    
    with cols_items[i]:
        st.markdown(f"**🛒 {nombre_display}**")
        key_input_precio = f"p_base_{producto}_{i}"
        
        precio_base = st.number_input(
            f"Precio Base $", 
            min_value=0.0, 
            step=100.0, 
            value=precio_guardado, 
            key=key_input_precio
        )
        promo = st.selectbox(f"Promo Góndola", lista_promos, key=f"p_promo_{i}")
        opciones_item.append({"precio": precio_base, "promo": promo})

if st.button("Calcular y Agregar a la Lista", type="primary"):
    mejor_precio_final = float('inf')
    mejor_opcion_nombre = "-"
    
    fila_export = {"Marca": marca, "Producto": producto, "Cantidad": cantidad}
    
    if producto not in st.session_state.precios_historicos:
        st.session_state.precios_historicos[producto] = {}
        
    for i, item in enumerate(opciones_item):
        conf = config_super[i]
        if conf["nombre"] != "-":
            # Guarda automáticamente el precio ingresado en la memoria histórica
            st.session_state.precios_historicos[producto][conf["nombre"]] = item["precio"]
            guardar_configuracion()
            
            unit_cp, tot_sp, tot_cp = calcular_promo_producto(cantidad, item["precio"], item["promo"])
            tuvo_promo_gondola = item["promo"] != "Sin Promo"
            
            descuento_banco_teorico = 0.0
            pct_banco = conf["dcto_pct"]
            if pct_banco > 0:
                if conf["acumulable"]:
                    descuento_banco_teorico = tot_cp * pct_banco
                elif not tuvo_promo_gondola:
                    descuento_banco_teorico = tot_sp * pct_banco
                    
            reintegro_consumido = sum(float(fila.get(f"Dcto Banco {i+1}", 0)) for fila in st.session_state.datos_alv)
            reintegro_disponible = max(0.0, conf["tope"] - reintegro_consumido)
            
            descuento_banco_real = min(descuento_banco_teorico, reintegro_disponible)
            total_final_bolsillo = tot_cp - descuento_banco_real
            
            ahorro_super = max((item["precio"] * cantidad) - total_final_bolsillo, 0.0)

            partes_promo = []
            if tuvo_promo_gondola:
                partes_promo.append(f"Góndola ({item['promo']})")
            if descuento_banco_real > 0:
                pct_str = f"{int(pct_banco*100)}%"
                partes_promo.append(f"Banco {conf['medio']} ({pct_str})")
            
            texto_promo_usada = " + ".join(partes_promo) if partes_promo else "Sin Descuento"

            if total_final_bolsillo > 0 and total_final_bolsillo < mejor_precio_final:
                mejor_precio_final = total_final_bolsillo
                mejor_opcion_nombre = conf["nombre"]
                
            fila_export.update({
                f"Supermercado {i+1}": conf["nombre"],
                f"Precio Base {i+1}": item["precio"],
                f"Total FINAL {i+1}": total_final_bolsillo,
                f"Ahorrado {i+1}": ahorro_super,
                f"Promo Usada {i+1}": texto_promo_usada,
                f"Dcto Banco {i+1}": descuento_banco_real
            })
            
    ahorro_real = 0.0
    precio_base_mejor = 0.0
    for i, item in enumerate(opciones_item):
        if config_super[i]["nombre"] == mejor_opcion_nombre:
            precio_base_mejor = item["precio"]
            ahorro_real = max((item["precio"] * cantidad) - mejor_precio_final, 0.0)
            break
            
    fila_export["🏆 Mejor Opción"] = mejor_opcion_nombre
    fila_export["Precio Base Mejor"] = precio_base_mejor
    fila_export["Precio Final Mejor"] = mejor_precio_final
    fila_export["💰 Ahorro Real"] = ahorro_real
    
    st.session_state.datos_alv.append(fila_export)
    guardar_carrito(st.session_state.datos_alv)
    st.success("¡Producto agregado y precios guardados en la memoria correctamente!")

# --- 6. VISUALIZADOR Y EXPORTACIÓN ---
if st.session_state.datos_alv:
    df = pd.DataFrame(st.session_state.datos_alv)
    
    st.divider()
    st.subheader("📊 Análisis del Carrito por Supermercado")
    
    super_cols = [c for c in df.columns if re.match(r"Supermercado \d+", c)]
    num_supermercados_df = len(super_cols)
    cols_vista = st.columns(num_supermercados_df)
    
    for idx, col_name in enumerate(super_cols):
        i = idx + 1
        super_nombre = df[col_name].mode()[0] if not df[col_name].dropna().empty else f"Opción {i}"
        
        with cols_vista[idx]:
            st.markdown(f"### 🛒 {super_nombre}")
            cols_to_keep = ["Producto", "Cantidad", f"Precio Base {i}", f"Total FINAL {i}", f"Ahorrado {i}", f"Promo Usada {i}"]
            cols_exist = [c for c in cols_to_keep if c in df.columns]
            
            if cols_exist:
                mini_df = df[cols_exist].copy()
                mini_df.rename(columns={
                    f"Precio Base {i}": "Precio Base", 
                    f"Total FINAL {i}": "Precio Final",
                    f"Ahorrado {i}": "Ahorrado",
                    f"Promo Usada {i}": "Promo Usada"
                }, inplace=True)
                
                st.dataframe(
                    mini_df, 
                    hide_index=True, 
                    use_container_width=True, 
                    column_config={
                        "Precio Base": st.column_config.NumberColumn(format="$ %.2f"),
                        "Precio Final": st.column_config.NumberColumn(format="$ %.2f"),
                        "Ahorrado": st.column_config.NumberColumn(format="$ %.2f")
                    }
                )
                
                subtotal_base = (mini_df["Precio Base"] * mini_df["Cantidad"]).sum() if "Precio Base" in mini_df.columns else 0
                subtotal_pagar = mini_df["Precio Final"].sum() if "Precio Final" in mini_df.columns else 0
                subtotal_ahorrado = mini_df["Ahorrado"].sum() if "Ahorrado" in mini_df.columns else 0
                
                st.info(f"**Base Sin Promo:** ${subtotal_base:,.2f}  \n**Total a Pagar:** ${subtotal_pagar:,.2f}  \n**Ahorrado:** ${subtotal_ahorrado:,.2f}")

    st.divider()
    st.subheader("🏆 Resumen de Compras Inteligentes")
    
    resumen_df = df[["Producto", "Cantidad", "🏆 Mejor Opción", "Precio Base Mejor", "Precio Final Mejor", "💰 Ahorro Real"]].copy()
    resumen_df.rename(columns={
        "Precio Base Mejor": "Precio Base",
        "Precio Final Mejor": "Precio Final",
        "💰 Ahorro Real": "Ahorrado"
    }, inplace=True)
    
    st.dataframe(
        resumen_df, 
        hide_index=True, 
        use_container_width=True,
        column_config={
            "Precio Base": st.column_config.NumberColumn(format="$ %.2f"),
            "Precio Final": st.column_config.NumberColumn(format="$ %.2f"),
            "Ahorrado": st.column_config.NumberColumn(format="$ %.2f")
        }
    )
    
    tot_base_res = (resumen_df["Precio Base"] * resumen_df["Cantidad"]).sum()
    tot_final_res = resumen_df["Precio Final"].sum()
    tot_ahorro_res = resumen_df["Ahorrado"].sum()
    
    st.success(f"🛒 **Total Base Original:** ${tot_base_res:,.2f} | 💳 **Total a Pagar:** ${tot_final_res:,.2f} | 🔥 **AHORRO TOTAL:** ${tot_ahorro_res:,.2f}")
    
    st.divider()
    
    st.subheader("✏️ Editar / Exportar Carrito")
    opciones_borrar = [f"Fila {i+1}: {d['Producto']} ({d['Marca']})" for i, d in enumerate(st.session_state.datos_alv)]
    c_sel, c_btn = st.columns([3, 1])
    with c_sel:
        item_a_borrar = st.selectbox("Seleccioná el producto para eliminarlo:", ["-"] + opciones_borrar)
    with c_btn:
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button("❌ Eliminar Producto"):
            if item_a_borrar != "-":
                idx = int(item_a_borrar.split(":")[0].replace("Fila ", "")) - 1
                st.session_state.datos_alv.pop(idx)
                guardar_carrito(st.session_state.datos_alv)
                st.rerun()

    st.write("") 
    
    @st.cache_data
    def convertir_df(df_exportar):
        return df_exportar.to_csv(index=False).encode('utf-8')
        
    csv = convertir_df(df)
    
    col_dl, col_del = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Descargar Análisis Completo (Excel)",
            data=csv,
            file_name='analisis_inteligente_compras.csv',
            mime='text/csv',
        )
    with col_del:
        if st.button("🗑️ Borrar Lista Completa"):
            st.session_state.datos_alv = []
            guardar_carrito([])
            st.rerun()
