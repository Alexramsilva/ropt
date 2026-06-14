
import streamlit as st
import pandas as pd
import pulp
from datetime import datetime

st.set_page_config(page_title="Pedido Óptimo - Marisquería Ramírez", layout="wide")
st.title("📦 Marisquería Ramírez - Pedido Óptimo")

st.image(
    "mr.jpeg",
    caption="",
    use_container_width=False,
    width=200
)

# -------------------------
# Datos
# -------------------------
data = [
#["MARISCOS","Camarón Seco","250 Gramos",0,1,1,70],
["SAMS","CLORO","10 LITROS",0,1,1,119],
["SAMS","FABULOSO (LAVANDA)","10 LITROS",0,1,1,179],
["SAMS","ACEITE 1-2-3","PAQUETE 3 LITROS",0,3,24,42],
["SAMS","VALENTINA ROJA","350 ML (6 PZAS)",0,6,6,15],
["MATERIA PRIMA","CHAROLA 835","FILETES",0,1,1,35],
["MATERIA PRIMA","CHAROLA 855","PEDIDOS GRANDES",0,1,1,35],
["MATERIA PRIMA","CHAROLA 066","PEDIDOS MEDIANOS",0,1,1,35],
["MATERIA PRIMA","BOLSA CHICA (1)","PEDIDOS CHICOS",0,1,1,40],
["MATERIA PRIMA","BOLSA (3)","PEDIDOS GRANDES",0,1,1,40],
["MATERIA PRIMA","TAZÓN (MEDIO LITRO)","PAQUETE",0,1,1,35],
["MATERIA PRIMA","TAZÓN (LITRO)","PAQUETE",0,1,1,35],
["MATERIA PRIMA","TAPA TAZÓN","PAQUETE",0,1,1,50],
["MATERIA PRIMA","ROLLO BOLSA POLIPAPEL","PAQUETE",0,1,1,80],
["MATERIA PRIMA","ROYAL","1 KILO",0,1,1,40],
["SALSAS","VALENTINA NEGRA","350 ML",0,1,2,20],
["SALSAS","VALENTINA AZUL","350 ML",0,1,2,25],
["SALSAS","LA GLORIA (ROJA)","250 ML",0,1,2,40],
["SALSAS","LA GLORIA (AMARILLA)","250 ML",0,1,5,40],
["SALSAS","LOP JU (ROJA)","250 ML",0,1,2,40],
["SALSAS","LOP JU (AMARILLA)","250 ML",0,1,5,40],
["SALSAS","LOS JAROCHOS (AMARILLA)","150 ML",0,1,5,40],
["SALSAS","SALSA INGLESA","250 ML",0,1,1,70],
["SALSAS","SALSA BRUJA","40 ML",0,1,1,30],
["SALSAS","ACEITE DE OLIVO","350 ML",0,1,1,105],
["SALSAS","VALENTINA BOLSITA","1 KG",0,1,2,50],
["SALSAS","SALADITAS","1 PAQUETE",0,1,2,60],
["CENTRAL","SAL DE AJO","1 KG",0,1,1,50],
["CENTRAL","CHILE PUYA","GRAMAJE",0,1,1,20],
["CENTRAL","CHILE GUAJIYO","GRAMAJE",0,1,1,20],
["3B","HARINA 3 SOLES","1 KILO",0,1,12,16],
["3B","MAYONESA CHICA","CHICA",0,1,3,30],
["3B","MAYONESA MEDIANA","MEDIANA",0,1,3,49],
["3B","SERVILLETA_SERVICIO","PAQUETE",0,1,2,42],
["3B","CATSUP","1 LITRO",0,1,3,30],
["3B","GEL ANTIBACTERIAL","200 ML",0,1,1,20],
["3B","ARROZ VALLE VERDE","1 KILO",0,1,7,17],
]

columns = ["Familia","Producto","Especificación","Inventario","CMVP","Consumo mensual","Costo unitario"]
df = pd.DataFrame(data, columns=columns)

# -------------------------
# Habilitar familias
# -------------------------
st.subheader("📂 Habilita las familias que usarás")

familias = sorted(df["Familia"].unique())
familias_activas = []

cols = st.columns(3)
for i, familia in enumerate(familias):
    with cols[i % 3]:
        if st.checkbox(familia, value=False, key=f"familia_{familia}"):
            familias_activas.append(familia)

if len(familias_activas) == 0:
    st.info("Selecciona al menos una familia para continuar.")
    st.stop()

df = df[df["Familia"].isin(familias_activas)].reset_index(drop=True)

st.success("Familias activas: " + ", ".join(familias_activas))

# -------------------------
# Captura de inventario
# -------------------------
st.subheader("✏️ Ingresa el inventario actual")
inventario_usuario = []

for i, row in df.iterrows():
    inventario = st.number_input(
        label=f"{row['Familia']} - {row['Producto']}",
        min_value=0,
        value=int(row["Inventario"]),
        step=1,
        key=f"inventario_{i}"
    )
    inventario_usuario.append(inventario)

df["Inventario"] = inventario_usuario

st.write("📊 Inventario capturado:")
st.dataframe(df[["Familia","Producto","Inventario"]])

# -------------------------
# Optimización con PuLP
# -------------------------
if st.button("🚀 Calcular pedido óptimo"):
    model = pulp.LpProblem("Pedido_Optimo", pulp.LpMinimize)
    k = {i: pulp.LpVariable(f"k_{i}", lowBound=0, cat="Integer") for i in df.index}

    model += pulp.lpSum(
        df.loc[i,"Costo unitario"] * df.loc[i,"CMVP"] * k[i]
        for i in df.index
    )

    for i in df.index:
        necesidad = max(0, df.loc[i,"Consumo mensual"] - df.loc[i,"Inventario"])
        model += df.loc[i,"CMVP"] * k[i] >= necesidad

    model.solve()

    df["Lotes"] = [pulp.value(k[i]) for i in df.index]
    df["Pedido óptimo"] = df["Lotes"] * df["CMVP"]
    df["Costo pedido"] = df["Pedido óptimo"] * df["Costo unitario"]

    st.subheader("📊 Pedido Óptimo")
    st.dataframe(df[["Familia","Producto","Inventario","Lotes","Pedido óptimo","Costo pedido"]])

    subtotal_familia = df.groupby("Familia")["Costo pedido"].sum().reset_index()
    subtotal_familia.rename(columns={"Costo pedido":"Subtotal"}, inplace=True)

    st.subheader("💰 Subtotal por Familia")
    st.dataframe(subtotal_familia)

    total = df["Costo pedido"].sum()
    st.subheader("💵 Total general del pedido")
    st.metric("Total", f"${total:,.2f}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    csv_detalle = df[["Familia","Producto","Inventario","Lotes","Pedido óptimo","Costo pedido"]]

    csv_total = pd.concat(
        [
            csv_detalle,
            pd.DataFrame([["","","","","",""]], columns=csv_detalle.columns),
            pd.DataFrame(
                [["SUBTOTAL " + row["Familia"], "", "", "", "", row["Subtotal"]]
                 for _, row in subtotal_familia.iterrows()],
                columns=csv_detalle.columns
            )
        ],
        ignore_index=True
    )

    csv_data = csv_total.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Descargar CSV completo con subtotales",
        csv_data,
        file_name=f"pedido_optimo_{timestamp}.csv",
        mime="text/csv"
    )
