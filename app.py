import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

st.set_page_config(page_title="AI Smart Home Generator", layout="wide", page_icon="🏗️")

st.title("🏗️ AI Smart Home Generator & Estimator (Civil Engineer Edition v2)")
st.markdown("**Aplikasi BIM sederhana: Denah per Lantai, Tampak, Potongan, 3D, Struktur & Preliminary Design (Sistem Pakar)**")
st.markdown("---")

# ==========================================
# SIDEBAR INPUT
# ==========================================
st.sidebar.header("📐 1. Geometri Ruang & Denah")
bentuk_denah = st.sidebar.selectbox("Bentuk Bangunan:", ["Bentuk Kotak (Standard)", "Bentuk 'L' (L-Shape)", "Bentuk 'U' (U-Shape)", "Bentuk Custom (Poligon Bebas)"])

if bentuk_denah != "Bentuk Custom (Poligon Bebas)":
    panjang = st.sidebar.number_input("Panjang Lahan (X) (m)", min_value=6.0, value=12.0, step=1.0)
    lebar = st.sidebar.number_input("Lebar Lahan (Y) (m)", min_value=6.0, value=10.0, step=1.0)
else:
    st.sidebar.info("Masukkan titik sudut denah (berurutan searah/berlawanan jarum jam). Titik terakhir otomatis menyambung ke titik pertama.")
    teks_titik = st.sidebar.text_area("Titik sudut (satu baris = satu titik, format: x,y — pakai titik untuk desimal)",
                                      value="0,0\n8,0\n8,4\n4,4\n4,8\n0,8", height=170)

jumlah_lantai = st.sidebar.slider("Jumlah Lantai", 1, 4, 2)
tinggi_lantai = st.sidebar.slider("Tinggi Antar Lantai (m)", 3.0, 5.0, 4.0, 0.1)
jumlah_ruangan = st.sidebar.slider("Rata-rata Jumlah Ruangan per Lantai", 1, 10, 3)

st.sidebar.header("🏗️ 2. Struktur Dasar & Pembebanan")
kondisi_tanah = st.sidebar.selectbox("Kondisi Tanah:", ["Tanah Keras (Pegunungan)", "Tanah Sedang (Perumahan)", "Tanah Lunak (Rawa)"])
jenis_atap = st.sidebar.selectbox("Kategori Atap:", ["Dak Beton (Datar)", "Atap Pelana", "Atap Limasan"])
fungsi_ruang = st.sidebar.selectbox("Fungsi Ruangan (SNI 1727):", ["Rumah Tinggal (Beban Standar)", "Perkantoran/Sekolah (Beban Menengah)", "Gudang/Toko (Beban Berat)"])

st.sidebar.header("🧱 3. Material Finishing")
material_dinding = st.sidebar.selectbox("Material Dinding:", ["Bata Merah", "Bata Ringan (Hebel)"])
jenis_lantai = st.sidebar.selectbox("Pilihan Ukuran Keramik:", ["Keramik 40x40 cm", "Granit 60x60 cm", "Vinyl Planks"])

# ==========================================
# ENGINE GEOMETRI (KOTAK/L/U vs CUSTOM)
# ==========================================
rects = None  # dekomposisi denah menjadi persegi panjang (untuk bentuk preset)

if bentuk_denah == "Bentuk Kotak (Standard)":
    xs, ys = [0, panjang, panjang, 0, 0], [0, 0, lebar, lebar, 0]
    rects = [(0.0, 0.0, panjang, lebar)]
    luas_lantai = panjang * lebar

elif bentuk_denah == "Bentuk 'L' (L-Shape)":
    px, ly = panjang * 0.5, lebar * 0.5
    xs, ys = [0, panjang, panjang, px, px, 0, 0], [0, 0, ly, ly, lebar, lebar, 0]
    rects = [(0.0, 0.0, panjang, ly), (0.0, ly, px, lebar)]
    luas_lantai = (panjang * ly) + (px * (lebar - ly))

elif bentuk_denah == "Bentuk 'U' (U-Shape)":
    px1, px2 = panjang * 0.3, panjang * 0.7
    ly = lebar * 0.4
    xs, ys = [0, panjang, panjang, px2, px2, px1, px1, 0, 0], [0, 0, lebar, lebar, ly, ly, lebar, lebar, 0]
    rects = [(0.0, 0.0, panjang, ly), (0.0, ly, px1, lebar), (px2, ly, panjang, lebar)]
    luas_lantai = (panjang * lebar) - ((px2 - px1) * (lebar - ly))

else:
    xs, ys = [], []
    try:
        for baris in teks_titik.splitlines():
            baris = baris.strip().replace(";", ",").replace("\t", ",")
            if not baris:
                continue
            bagian = [q for q in baris.replace(" ", ",").split(",") if q != ""]
            if len(bagian) != 2:
                raise ValueError(baris)
            xs.append(float(bagian[0]))
            ys.append(float(bagian[1]))
    except ValueError:
        st.warning("⚠️ Format titik salah. Tulis satu titik per baris, contoh: 4.5,3 (gunakan titik, bukan koma, untuk desimal).")
        st.stop()
    if len(xs) < 3:
        st.warning("⚠️ Masukkan minimal 3 titik koordinat di menu samping (Bentuk Custom) agar bangunan terbentuk!")
        st.stop()
    if xs[0] != xs[-1] or ys[0] != ys[-1]:
        xs.append(xs[0])
        ys.append(ys[0])
    luas_lantai = 0.0
    for i in range(len(xs) - 1):
        luas_lantai += (xs[i] * ys[i + 1]) - (xs[i + 1] * ys[i])
    luas_lantai = abs(luas_lantai) / 2.0
    if luas_lantai <= 0:
        st.warning("⚠️ Luas denah = 0. Periksa kembali koordinat titik sudut.")
        st.stop()

keliling_luar = sum(math.sqrt((xs[i + 1] - xs[i]) ** 2 + (ys[i + 1] - ys[i]) ** 2) for i in range(len(xs) - 1))

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
panjang = max_x - min_x
lebar = max_y - min_y

luas_total_bangunan = luas_lantai * jumlah_lantai
tinggi_total = tinggi_lantai * jumlah_lantai

# ==========================================
# FUNGSI BANTU GEOMETRI
# ==========================================
def titik_dalam(px_, py_):
    """Ray casting: apakah titik berada di dalam poligon denah."""
    inside = False
    n = len(xs) - 1
    j = n - 1
    for i in range(n):
        xi, yi, xj, yj = xs[i], ys[i], xs[j], ys[j]
        if ((yi > py_) != (yj > py_)) and (px_ < (xj - xi) * (py_ - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def jarak_ke_tepi(px_, py_):
    d_min = 1e9
    for i in range(len(xs) - 1):
        xa, ya, xb, yb = xs[i], ys[i], xs[i + 1], ys[i + 1]
        dx, dy = xb - xa, yb - ya
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((px_ - xa) * dx + (py_ - ya) * dy) / L2))
        d = math.hypot(px_ - (xa + t * dx), py_ - (ya + t * dy))
        d_min = min(d_min, d)
    return d_min


def bagi_grid(x0, y0, x1, y1, n):
    """Membagi persegi panjang menjadi grid ruangan (min. sisi ruangan ± 2.5 m)."""
    w, h = x1 - x0, y1 - y0
    n = max(n, 1)
    maks_x = max(1, int(w // 2.5))
    maks_y = max(1, int(h // 2.5))
    nx = max(1, min(round(math.sqrt(n * w / h)), maks_x))
    ny = max(1, min(math.ceil(n / nx), maks_y))
    cells = []
    for i in range(nx):
        for j in range(ny):
            cells.append((x0 + w * i / nx, y0 + h * j / ny, x0 + w * (i + 1) / nx, y0 + h * (j + 1) / ny))
    return cells


def posisi_bukaan(L):
    """Posisi relatif (0-1) jendela/pintu sepanjang dinding sepanjang L meter."""
    if L < 2.5:
        return []
    n = max(1, int(L // 3))
    return [(k + 0.5) / n for k in range(n)]


def interval_potong(x_cut):
    """Interval Y yang berada di dalam bangunan pada garis potong X = x_cut."""
    cross = []
    for i in range(len(xs) - 1):
        xa, ya, xb, yb = xs[i], ys[i], xs[i + 1], ys[i + 1]
        if (xa <= x_cut < xb) or (xb <= x_cut < xa):
            t = (x_cut - xa) / (xb - xa)
            cross.append(ya + t * (yb - ya))
    cross.sort()
    return [(cross[i], cross[i + 1]) for i in range(0, len(cross) - 1, 2)]


# ==========================================
# GENERATOR RUANGAN (DENAH OTOMATIS)
# ==========================================
ruang_geo = []
if rects is not None:
    total_area = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)
    for r in rects:
        a = (r[2] - r[0]) * (r[3] - r[1])
        n_i = max(1, round(jumlah_ruangan * a / total_area))
        ruang_geo += bagi_grid(r[0], r[1], r[2], r[3], n_i)
else:
    n_target = math.ceil(jumlah_ruangan * (panjang * lebar) / luas_lantai)
    for c in bagi_grid(min_x, min_y, max_x, max_y, n_target):
        if titik_dalam((c[0] + c[2]) / 2, (c[1] + c[3]) / 2):
            ruang_geo.append(c)
    if not ruang_geo:
        ruang_geo = [(min_x, min_y, max_x, max_y)]
ruang_geo.sort(key=lambda r: (round(r[1], 3), round(r[0], 3)))

if "Rumah" in fungsi_ruang:
    NAMA_L1 = ["Ruang Tamu", "Ruang Keluarga", "Dapur", "Ruang Makan", "Kamar Tidur 1", "KM/WC", "Garasi", "Musholla", "Gudang", "R. Kerja"]
    NAMA_ATAS = ["Kamar Utama", "Kamar Tidur 2", "R. Santai", "KM/WC", "R. Kerja", "Balkon", "Kamar Tidur 3", "Perpustakaan", "Gudang", "Laundry"]
elif "Perkantoran" in fungsi_ruang:
    NAMA_L1 = ["Lobby", "Ruang Kerja 1", "Ruang Rapat", "Pantry", "Ruang Kerja 2", "Toilet", "Arsip", "Server", "Gudang", "Musholla"]
    NAMA_ATAS = ["Ruang Kerja 3", "Ruang Direktur", "Ruang Rapat", "Toilet", "Ruang Kerja 4", "Pantry", "Arsip", "Perpustakaan", "Gudang", "R. Santai"]
else:
    NAMA_L1 = ["Area Display", "Gudang Utama", "Kasir", "Loading Dock", "Gudang 2", "Toilet", "Kantor", "Gudang 3", "Pantry", "Arsip"]
    NAMA_ATAS = ["Gudang Atas 1", "Gudang Atas 2", "Kantor", "Toilet", "Arsip", "Pantry", "Gudang Atas 3", "R. Rapat", "Gudang", "R. Santai"]


def daftar_ruang(idx_lantai):
    daftar = NAMA_L1 if idx_lantai == 0 else NAMA_ATAS
    hasil = []
    for k, (x0, y0, x1, y1) in enumerate(ruang_geo):
        hasil.append({"nama": (nama_manual[k] if nama_manual else daftar[k % len(daftar)]), "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                      "w": x1 - x0, "h": y1 - y0, "luas": (x1 - x0) * (y1 - y0)})
    return hasil


# --- Mode ruangan manual (opsional) ---
nama_manual = None
with st.expander("✏️ Atur Ruangan Secara Manual (opsional)"):
    st.caption("Aktifkan untuk mengedit nama & koordinat ruangan sendiri (meter, sistem koordinat sama dengan denah). "
               "Tata ruang yang sama dipakai untuk semua lantai. Baris dengan X1 ≤ X0 atau Y1 ≤ Y0 diabaikan.")
    pakai_manual = st.checkbox("Gunakan ruangan manual", value=False)
    if pakai_manual:
        st.caption("Format tiap baris: Nama; X0; Y0; X1; Y1  (contoh: Kamar Tidur; 0; 0; 4; 3.5). Gunakan titik untuk desimal.")
        teks_awal = "\n".join(f"{r['nama']}; {r['x0']:.2f}; {r['y0']:.2f}; {r['x1']:.2f}; {r['y1']:.2f}" for r in daftar_ruang(0))
        teks_ruang = st.text_area("Daftar ruangan", value=teks_awal, height=220,
                                  key=f"ruang_manual_{bentuk_denah}_{panjang}_{lebar}_{jumlah_ruangan}")
        ruang_baru, nama_baru, baris_salah = [], [], 0
        for baris in teks_ruang.splitlines():
            if not baris.strip():
                continue
            try:
                bagian = [q.strip() for q in baris.split(";")]
                x0_, y0_, x1_, y1_ = [float(v) for v in bagian[1:5]]
                if len(bagian) != 5 or not (x1_ > x0_ and y1_ > y0_):
                    raise ValueError
                ruang_baru.append((x0_, y0_, x1_, y1_))
                nama_baru.append(bagian[0])
            except (ValueError, IndexError):
                baris_salah += 1
        if baris_salah:
            st.warning(f"{baris_salah} baris diabaikan karena formatnya salah.")
        if ruang_baru:
            ruang_geo = ruang_baru
            nama_manual = nama_baru
        else:
            st.warning("Tidak ada ruangan valid, memakai ruangan otomatis.")


# ==========================================
# ESTIMASI BEBAN KASAR & MATERIAL
# ==========================================
LL = 200 if "Rumah" in fungsi_ruang else (250 if "Perkantoran" in fungsi_ruang else 400)
beban_partisi = 250 if material_dinding == "Bata Merah" else 150
SIDL = 120 + beban_partisi

luas_dinding_luar = keliling_luar * tinggi_total
panjang_partisi = (jumlah_ruangan - 1) * (lebar * 0.5) * jumlah_lantai
luas_dinding_bersih = (luas_dinding_luar + (panjang_partisi * tinggi_lantai)) * 0.85

if material_dinding == "Bata Merah":
    kebutuhan_bata = int(luas_dinding_bersih * 70)
    satuan_bata, harga_dinding_m2 = "Buah Bata Merah", 150000
else:
    kebutuhan_bata = round(luas_dinding_bersih / 10, 1)
    satuan_bata, harga_dinding_m2 = "m³ Bata Ringan (Hebel)", 135000

semen_sak = int(luas_dinding_bersih * 0.25)
biaya_dinding = luas_dinding_bersih * harga_dinding_m2

luas_lantai_pengerjaan = luas_total_bangunan * 1.05
luas_per_dus = 1.0 if "40x40" in jenis_lantai else (1.44 if "60x60" in jenis_lantai else 3.0)
kebutuhan_dus_lantai = math.ceil(luas_lantai_pengerjaan / luas_per_dus)
biaya_lantai = luas_lantai_pengerjaan * 220000

panjang_pondasi = keliling_luar + panjang_partisi
harga_pondasi = 450000 if kondisi_tanah == "Tanah Keras (Pegunungan)" else (750000 if kondisi_tanah == "Tanah Sedang (Perumahan)" else 1200000)
biaya_pondasi = panjang_pondasi * harga_pondasi

vol_beton = luas_total_bangunan * 0.25
biaya_beton = vol_beton * 4500000

kemiringan_rad = math.radians(30)
luas_atap = luas_lantai if jenis_atap == "Dak Beton (Datar)" else (panjang * lebar) / math.cos(kemiringan_rad)
biaya_atap = luas_atap * (600000 if jenis_atap == "Dak Beton (Datar)" else 250000)

total_biaya = biaya_dinding + biaya_pondasi + biaya_beton + biaya_atap + biaya_lantai

# Parameter atap (dipakai 3D, tampak, potongan)
ridge_y = min_y + (lebar / 2)
rx_start = min_x if jenis_atap == "Atap Pelana" else min_x + (panjang * 0.2)
rx_end = max_x if jenis_atap == "Atap Pelana" else min_x + (panjang * 0.8)
t_atap = 0.0 if jenis_atap == "Dak Beton (Datar)" else (lebar / 2) * math.tan(kemiringan_rad)

# ==========================================
# PERHITUNGAN STRUKTUR (PRELIMINARY DESIGN)
# ==========================================
bentang_max = max(panjang, lebar)
jarak_kolom_asumsi = 4.0 if bentang_max > 6 else bentang_max

t_sloof = (jarak_kolom_asumsi * 100) / 15
l_sloof = t_sloof / 1.5
t_balok_induk = (jarak_kolom_asumsi * 100) / 12
l_balok_induk = t_balok_induk / 2
t_balok_anak = (jarak_kolom_asumsi * 100) / 15
l_balok_anak = t_balok_anak / 2
tebal_pelat = math.ceil((jarak_kolom_asumsi * 100) / 35)
if "Gudang" in fungsi_ruang:
    tebal_pelat += 3
dim_kolom = max(math.ceil(l_balok_induk / 5) * 5, 15)

# Pembebanan (sekarang termasuk berat sendiri pelat)
berat_pelat = (tebal_pelat / 100) * 2400
DL = berat_pelat + SIDL
kombinasi_ultimate = (1.2 * DL) + (1.6 * LL)
q_layan = DL + LL


def hitung_kolom(jarak):
    """Posisi kolom: sepanjang keliling + grid interior (indikatif)."""
    kol = []

    def tambah(x, y):
        for (a, b) in kol:
            if abs(a - x) < 0.05 and abs(b - y) < 0.05:
                return
        kol.append((x, y))

    for i in range(len(xs) - 1):
        xa, ya, xb, yb = xs[i], ys[i], xs[i + 1], ys[i + 1]
        L = math.hypot(xb - xa, yb - ya)
        if L < 1e-9:
            continue
        n = max(1, math.ceil(L / jarak))
        for k in range(n):
            tambah(xa + (xb - xa) * k / n, ya + (yb - ya) * k / n)
    nxk = max(1, math.ceil(panjang / jarak))
    nyk = max(1, math.ceil(lebar / jarak))
    for i in range(1, nxk):
        for j in range(1, nyk):
            x = min_x + panjang * i / nxk
            y = min_y + lebar * j / nyk
            if titik_dalam(x, y) and jarak_ke_tepi(x, y) >= 1.0:
                tambah(x, y)
    return kol


kolom_list = hitung_kolom(jarak_kolom_asumsi)
jumlah_kolom_estimasi = len(kolom_list)

# Beban per kolom & dimensi pondasi
P_total = q_layan * luas_total_bangunan * 1.15  # +15% berat balok & kolom
P_kolom = P_total / jumlah_kolom_estimasi       # kg
sigma_tanah = {"Tanah Keras (Pegunungan)": 2.5, "Tanah Sedang (Perumahan)": 1.5, "Tanah Lunak (Rawa)": 0.5}[kondisi_tanah]  # kg/cm2
kedalaman_pondasi = {"Tanah Keras (Pegunungan)": 0.8, "Tanah Sedang (Perumahan)": 1.0, "Tanah Lunak (Rawa)": 1.5}[kondisi_tanah]
sisi_footplat_cm = max(60, math.ceil(math.sqrt(P_kolom / sigma_tanah) / 5) * 5)
Q_tiang = 20000  # kg, asumsi daya dukung ijin minipile
jumlah_tiang = max(1, math.ceil(P_kolom / Q_tiang))
tanah_lunak = kondisi_tanah == "Tanah Lunak (Rawa)"

# ==========================================
# DATAFRAME RAB
# ==========================================
df_rab = pd.DataFrame({
    "Pekerjaan": ["Pondasi", "Struktur Beton", f"Dinding ({material_dinding})", f"Lantai ({jenis_lantai})", f"Atap ({jenis_atap})"],
    "Material Utama": [f"{panjang_pondasi:.1f} m'", f"{vol_beton:.1f} m³", f"{kebutuhan_bata:,} {satuan_bata}", f"{kebutuhan_dus_lantai} Dus/Box", f"{luas_atap:.1f} m²"],
    "Estimasi Harga (Rp)": [biaya_pondasi, biaya_beton, biaya_dinding, biaya_lantai, biaya_atap]
})
df_rab.index += 1

# ==========================================
# FUNGSI GAMBAR 2D (UMUM)
# ==========================================
WARNA_RUANG = ["#FDEBD0", "#D6EAF8", "#D5F5E3", "#FCF3CF", "#E8DAEF", "#FADBD8", "#D1F2EB", "#EAEDED"]


def rect(fig, x0, y0, x1, y1, fill, line="#17202A", lw=1.0, dash=None, layer="above"):
    fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=fill, layer=layer,
                  line=dict(color=line, width=lw, dash=dash) if dash else dict(color=line, width=lw))


def poly(fig, px_, py_, fill, line="#17202A", lw=2):
    fig.add_trace(go.Scatter(x=px_, y=py_, mode="lines", fill="toself", fillcolor=fill,
                             line=dict(color=line, width=lw), hoverinfo="skip", showlegend=False))


def dim_h(fig, x0, x1, y, teks, t=0.15):
    fig.add_shape(type="line", x0=x0, y0=y, x1=x1, y1=y, line=dict(color="#555", width=1))
    for xx in (x0, x1):
        fig.add_shape(type="line", x0=xx, y0=y - t, x1=xx, y1=y + t, line=dict(color="#555", width=1))
    fig.add_annotation(x=(x0 + x1) / 2, y=y, text=teks, showarrow=False, yshift=-12, font=dict(size=11, color="#333"))


def dim_v(fig, x, y0, y1, teks, t=0.15):
    fig.add_shape(type="line", x0=x, y0=y0, x1=x, y1=y1, line=dict(color="#555", width=1))
    for yy in (y0, y1):
        fig.add_shape(type="line", x0=x - t, y0=yy, x1=x + t, y1=yy, line=dict(color="#555", width=1))
    fig.add_annotation(x=x, y=(y0 + y1) / 2, text=teks, showarrow=False, xshift=-12, textangle=-90, font=dict(size=11, color="#333"))


def atur_2d(fig, judul, xr, yr, reverse_x=False, height=560):
    fig.update_layout(title=judul, height=height, showlegend=False, plot_bgcolor="white",
                      margin=dict(l=10, r=10, t=50, b=10))
    fig.update_xaxes(range=[xr[1], xr[0]] if reverse_x else [xr[0], xr[1]], visible=False)
    fig.update_yaxes(range=list(yr), visible=False, scaleanchor="x", scaleratio=1)


def tampil_tabel(df, kolom_rp=None):
    """Menampilkan tabel sebagai HTML (tidak butuh pyarrow, aman untuk komputer dengan Application Control)."""
    tabel = df.copy()
    for kol in (kolom_rp or []):
        tabel[kol] = tabel[kol].map(lambda v: f"Rp {v:,.0f}")
    html = tabel.to_html(classes="tabel-app", border=0).replace("\n", "")
    css = ("<style>.tabel-app{border-collapse:collapse;width:100%;font-size:0.9rem}"
           ".tabel-app th,.tabel-app td{border-bottom:1px solid rgba(128,128,128,.35);padding:6px 10px;text-align:left}"
           ".tabel-app th{background:rgba(128,128,128,.15)}</style>")
    st.markdown(css + "<div style='overflow-x:auto'>" + html + "</div>", unsafe_allow_html=True)


def tombol_unduh(fig, nama_file, key):
    st.download_button("📥 Unduh gambar interaktif (HTML)", data=fig.to_html(include_plotlyjs="cdn"),
                       file_name=nama_file, mime="text/html", key=key)


def panah_utara(fig, x, y):
    fig.add_annotation(x=x, y=y + 1.0, ax=0, ay=40, showarrow=True, arrowhead=2, arrowwidth=3, arrowcolor="#17202A", text="")
    fig.add_annotation(x=x, y=y + 1.3, text="<b>U</b>", showarrow=False, font=dict(size=14))


# ==========================================
# GAMBAR: DENAH PER LANTAI
# ==========================================
def gambar_denah(idx_lantai):
    fig = go.Figure()
    ruangan = daftar_ruang(idx_lantai)

    for k, r in enumerate(ruangan):
        rect(fig, r["x0"], r["y0"], r["x1"], r["y1"], WARNA_RUANG[k % len(WARNA_RUANG)], "#566573", 1.5, layer="below")
        ukuran_font = 10 if min(r["w"], r["h"]) >= 3 else 8
        fig.add_annotation(x=(r["x0"] + r["x1"]) / 2, y=(r["y0"] + r["y1"]) / 2 + (0.15 * r["h"] if jumlah_lantai > 1 else 0),
                           text=f"<b>{r['nama']}</b><br>{r['w']:.1f} x {r['h']:.1f} m<br>{r['luas']:.1f} m²",
                           showarrow=False, font=dict(size=ukuran_font, color="#17202A"))

    # Tangga pada ruangan terbesar
    if jumlah_lantai > 1:
        terbesar = max(ruangan, key=lambda r: r["luas"])
        if terbesar["w"] >= 2.5 and terbesar["h"] >= 2.0:
            sx1 = terbesar["x1"] - 0.1
            sx0 = sx1 - 1.1
            sy0 = terbesar["y0"] + 0.1
            sy1 = sy0 + min(3.0, terbesar["h"] - 0.2)
            rect(fig, sx0, sy0, sx1, sy1, "#D5D8DC", "#17202A", 1.2)
            yy = sy0 + 0.25
            while yy < sy1:
                fig.add_shape(type="line", x0=sx0, y0=yy, x1=sx1, y1=yy, line=dict(color="#7B7D7D", width=1))
                yy += 0.25
            fig.add_annotation(x=(sx0 + sx1) / 2, y=sy1, text="Tangga", showarrow=False, yshift=9, font=dict(size=8))

    # Dinding luar
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#17202A", width=5), hoverinfo="skip", showlegend=False))

    # Jendela & pintu pada dinding luar
    for i in range(len(xs) - 1):
        xa, ya, xb, yb = xs[i], ys[i], xs[i + 1], ys[i + 1]
        L = math.hypot(xb - xa, yb - ya)
        if L < 2.5:
            continue
        ux, uy = (xb - xa) / L, (yb - ya) / L
        pos = posisi_bukaan(L)
        depan = abs(ya - yb) < 1e-9 and abs(ya - min_y) < 1e-9
        idx_pintu = -1
        if depan and idx_lantai == 0:
            idx_pintu = min(range(len(pos)), key=lambda q: abs(pos[q] - 0.5))
        for k, f in enumerate(pos):
            cx, cy = xa + ux * L * f, ya + uy * L * f
            half = 0.5 if k == idx_pintu else 0.7
            warna = "#A04000" if k == idx_pintu else "#1ABC9C"
            fig.add_trace(go.Scatter(x=[cx - ux * half, cx + ux * half], y=[cy - uy * half, cy + uy * half],
                                     mode="lines", line=dict(color=warna, width=9), hoverinfo="skip", showlegend=False))

    # Kolom
    fig.add_trace(go.Scatter(x=[k[0] for k in kolom_list], y=[k[1] for k in kolom_list], mode="markers",
                             marker=dict(symbol="square", size=9, color="#C0392B"), hoverinfo="skip", showlegend=False))

    dim_h(fig, min_x, max_x, min_y - 1.2, f"{panjang:.2f} m")
    dim_v(fig, max_x + 1.2, min_y, max_y, f"{lebar:.2f} m")
    panah_utara(fig, max_x + 2.3, max_y - 1.5)
    elv = idx_lantai * tinggi_lantai
    atur_2d(fig, f"Denah Lantai {idx_lantai + 1} (Elv. +{elv:.2f} m)",
            (min_x - 2, max_x + 3.5), (min_y - 2.6, max_y + 2.0), height=620)
    return fig, ruangan


# ==========================================
# GAMBAR: TAMPAK (DEPAN/BELAKANG/KANAN/KIRI)
# ==========================================
def gambar_tampak(arah):
    horiz_x = arah in ("depan", "belakang")
    a0, a1 = (min_x, max_x) if horiz_x else (min_y, max_y)
    W = a1 - a0
    reverse = arah in ("belakang", "kiri")
    H = tinggi_total
    tanah_d = kedalaman_pondasi + 0.5
    fig = go.Figure()

    # Tanah & pondasi
    rect(fig, a0 - 3, -tanah_d, a1 + 3, 0, "#E6D5B8", "#8D6E63", 1, layer="below")
    rect(fig, a0 - 0.2, -kedalaman_pondasi, a1 + 0.2, 0, "#B2BABB", "#566573", 1, dash="dash", layer="below")

    # Badan bangunan
    rect(fig, a0, 0, a1, H, "#FDF2E9", "#17202A", 2)
    for f in range(1, jumlah_lantai + 1):
        rect(fig, a0 - 0.1, f * tinggi_lantai - 0.15, a1 + 0.1, f * tinggi_lantai + 0.05, "#AAB7B8", "#566573", 1)

    # Jendela & pintu
    pos = posisi_bukaan(W)
    for f in range(jumlah_lantai):
        z0 = f * tinggi_lantai
        idx_pintu = -1
        if arah == "depan" and f == 0 and pos:
            idx_pintu = min(range(len(pos)), key=lambda q: abs(pos[q] - 0.5))
        for k, fr in enumerate(pos):
            cx = a0 + W * fr
            if k == idx_pintu:
                rect(fig, cx - 0.55, 0, cx + 0.55, 2.1, "#A04000", "#17202A", 1.5)
            else:
                rect(fig, cx - 0.7, z0 + 1.0, cx + 0.7, z0 + 2.3, "#AED6F1", "#17202A", 1.5)
                fig.add_shape(type="line", x0=cx, y0=z0 + 1.0, x1=cx, y1=z0 + 2.3, line=dict(color="#17202A", width=1))

    # Atap
    if jenis_atap == "Dak Beton (Datar)":
        rect(fig, a0 - 0.15, H, a1 + 0.15, H + 0.5, "#BDC3C7", "#17202A", 1.5)
        puncak = H + 0.5
    else:
        if horiz_x:
            if jenis_atap == "Atap Pelana":
                poly(fig, [a0, a1, a1, a0, a0], [H, H, H + t_atap, H + t_atap, H], "#E74C3C")
            else:
                poly(fig, [a0, a1, rx_end, rx_start, a0], [H, H, H + t_atap, H + t_atap, H], "#E74C3C")
        else:
            poly(fig, [a0, a1, (a0 + a1) / 2, a0], [H, H, H + t_atap, H], "#E74C3C")
        puncak = H + t_atap

    # Level elevasi
    sx = a0 - 0.3 if reverse else a1 + 0.3
    edge = a0 if reverse else a1
    for i in range(jumlah_lantai + 1):
        z = i * tinggi_lantai
        fig.add_shape(type="line", x0=edge, y0=z, x1=sx, y1=z, line=dict(color="#7B7D7D", width=1, dash="dashdot"))
        fig.add_annotation(x=sx, y=z, text="±0.00" if i == 0 else f"+{z:.2f}", showarrow=False, xanchor="left", font=dict(size=10))
    fig.add_annotation(x=sx, y=puncak, text=f"+{puncak:.2f} (puncak)", showarrow=False, xanchor="left", font=dict(size=10, color="#C0392B"))

    # Dimensi
    dim_h(fig, a0, a1, -tanah_d - 0.6, f"{W:.2f} m")
    xv = a1 + 1.4 if reverse else a0 - 1.4
    dim_v(fig, xv, 0, H, f"{H:.2f} m")

    label_arah = {"depan": "Depan (dilihat dari sisi Y min)", "belakang": "Belakang (dilihat dari sisi Y max)",
                  "kanan": "Samping Kanan (dilihat dari sisi X max)", "kiri": "Samping Kiri (dilihat dari sisi X min)"}[arah]
    atur_2d(fig, f"Tampak {label_arah}", (a0 - 3.5, a1 + 4.0), (-tanah_d - 1.6, puncak + 1.5), reverse_x=reverse, height=560)
    return fig


# ==========================================
# GAMBAR: TAMPAK ATAS (DENAH ATAP)
# ==========================================
def gambar_tampak_atas():
    fig = go.Figure()
    fill = "#BDC3C7" if jenis_atap == "Dak Beton (Datar)" else "#F1948A"
    poly(fig, xs, ys, fill, "#17202A", 4)
    if jenis_atap != "Dak Beton (Datar)":
        garis = dict(color="#7B241C", width=3)
        fig.add_trace(go.Scatter(x=[rx_start, rx_end], y=[ridge_y, ridge_y], mode="lines", line=garis, hoverinfo="skip", showlegend=False))
        cx_ = [min_x, max_x, max_x, min_x]
        cy_ = [min_y, min_y, max_y, max_y]
        for i in range(4):
            tx = rx_start if cx_[i] == min_x else rx_end
            fig.add_trace(go.Scatter(x=[cx_[i], tx], y=[cy_[i], ridge_y], mode="lines", line=dict(color="#7B241C", width=2), hoverinfo="skip", showlegend=False))
        fig.add_annotation(x=(min_x + max_x) / 2, y=ridge_y, text=f"Bubungan (kemiringan 30°)", showarrow=False, yshift=12, font=dict(size=10))
        # arah aliran air
        for fx in (0.35, 0.65):
            xx = min_x + panjang * fx
            fig.add_annotation(x=xx, y=min_y + lebar * 0.15, ax=0, ay=-30, showarrow=True, arrowhead=2, arrowcolor="#1F618D", text="")
            fig.add_annotation(x=xx, y=max_y - lebar * 0.15, ax=0, ay=30, showarrow=True, arrowhead=2, arrowcolor="#1F618D", text="")
    else:
        fig.add_annotation(x=(min_x + max_x) / 2, y=(min_y + max_y) / 2, text="Dak Beton<br>(kemiringan ≥ 1% ke arah talang/drain)", showarrow=False, font=dict(size=11))
    dim_h(fig, min_x, max_x, min_y - 1.2, f"{panjang:.2f} m")
    dim_v(fig, max_x + 1.2, min_y, max_y, f"{lebar:.2f} m")
    panah_utara(fig, max_x + 2.3, max_y - 1.5)
    atur_2d(fig, "Tampak Atas (Denah Atap)", (min_x - 2, max_x + 3.5), (min_y - 2.6, max_y + 2.0), height=560)
    return fig


# ==========================================
# GAMBAR: POTONGAN A-A
# ==========================================
def gambar_potongan(x_cut):
    interval = interval_potong(x_cut)
    if not interval:
        return None
    y_lo = min(a for a, b in interval)
    y_hi = max(b for a, b in interval)
    H = tinggi_total
    tanah_d = kedalaman_pondasi + 0.5
    tp = tebal_pelat / 100
    fig = go.Figure()
    rect(fig, y_lo - 3, -tanah_d, y_hi + 3, 0, "#E6D5B8", "#8D6E63", 1, layer="below")

    for (ya, yb) in interval:
        rect(fig, ya, -0.15, yb, 0, "#7F8C8D", "#17202A", 1)  # lantai dasar
        for yw in (ya, yb - 0.15):
            cx = yw + 0.075
            rect(fig, cx - 0.3, -kedalaman_pondasi, cx + 0.3, 0, "#A6ACAF", "#566573", 1)  # pondasi
            rect(fig, yw, 0, yw + 0.15, H, "#E59866", "#17202A", 1.5)                     # dinding
            if tanah_lunak:
                fig.add_shape(type="line", x0=cx, y0=-kedalaman_pondasi, x1=cx, y1=-kedalaman_pondasi - 0.9,
                              line=dict(color="#17202A", width=3, dash="dot"))
        for f in range(1, jumlah_lantai + 1):
            if f == jumlah_lantai and jenis_atap != "Dak Beton (Datar)":
                for yw in (ya, yb - 0.15):
                    rect(fig, yw, H - 0.25, yw + 0.15, H, "#5D6D7E", "#17202A", 1)  # ring balok
            else:
                rect(fig, ya, f * tinggi_lantai - tp, yb, f * tinggi_lantai, "#5D6D7E", "#17202A", 1)  # pelat
        if jenis_atap == "Dak Beton (Datar)":
            rect(fig, ya, H, ya + 0.15, H + 0.5, "#BDC3C7", "#17202A", 1)
            rect(fig, yb - 0.15, H, yb, H + 0.5, "#BDC3C7", "#17202A", 1)

    if jenis_atap == "Dak Beton (Datar)":
        puncak = H + 0.5
    else:
        span = y_hi - y_lo
        tt = (span / 2) * math.tan(kemiringan_rad)
        poly(fig, [y_lo, y_hi, (y_lo + y_hi) / 2, y_lo], [H, H, H + tt, H], "rgba(231,76,60,0.35)", "#C0392B", 3)
        puncak = H + tt

    # Anotasi
    for f in range(jumlah_lantai):
        fig.add_annotation(x=(y_lo + y_hi) / 2, y=f * tinggi_lantai + tinggi_lantai / 2,
                           text=f"Lantai {f + 1}<br>h = {tinggi_lantai:.2f} m", showarrow=False, font=dict(size=11))
    fig.add_annotation(x=y_hi + 0.2, y=tinggi_lantai - tp / 2, text=f"← pelat t = {tebal_pelat} cm", showarrow=False, xanchor="left", font=dict(size=10))
    fig.add_annotation(x=y_hi + 0.2, y=-kedalaman_pondasi / 2, text=f"← pondasi (kedalaman {kedalaman_pondasi:.1f} m)", showarrow=False, xanchor="left", font=dict(size=10))
    if tanah_lunak:
        fig.add_annotation(x=y_hi + 0.2, y=-kedalaman_pondasi - 0.5, text="← tiang pancang (indikatif)", showarrow=False, xanchor="left", font=dict(size=10))
    for i in range(jumlah_lantai + 1):
        z = i * tinggi_lantai
        fig.add_annotation(x=y_lo - 0.3, y=z, text="±0.00" if i == 0 else f"+{z:.2f}", showarrow=False, xanchor="right", font=dict(size=10))
    dim_h(fig, y_lo, y_hi, -tanah_d - 0.6, f"{y_hi - y_lo:.2f} m")
    atur_2d(fig, f"Potongan A-A (memotong pada X = {x_cut:.2f} m)", (y_lo - 3.5, y_hi + 6.5), (-tanah_d - 1.6, puncak + 1.2), height=580)
    return fig


# ==========================================
# GAMBAR: 3D (WIREFRAME / SOLID)
# ==========================================
def mesh_baru():
    return {"x": [], "y": [], "z": [], "i": [], "j": [], "k": []}


def mesh_quad(m, p0, p1, p2, p3):
    b = len(m["x"])
    for p in (p0, p1, p2, p3):
        m["x"].append(p[0]); m["y"].append(p[1]); m["z"].append(p[2])
    m["i"] += [b, b]; m["j"] += [b + 1, b + 2]; m["k"] += [b + 2, b + 3]


def mesh_tri(m, p0, p1, p2):
    b = len(m["x"])
    for p in (p0, p1, p2):
        m["x"].append(p[0]); m["y"].append(p[1]); m["z"].append(p[2])
    m["i"].append(b); m["j"].append(b + 1); m["k"].append(b + 2)


def tambah_mesh(fig, m, warna, opacity, nama):
    if m["x"]:
        fig.add_trace(go.Mesh3d(x=m["x"], y=m["y"], z=m["z"], i=m["i"], j=m["j"], k=m["k"],
                                color=warna, opacity=opacity, flatshading=True, name=nama, hoverinfo="skip"))


def gambar_3d(mode):
    fig = go.Figure()
    z_atas = tinggi_total

    if mode in ("Wireframe", "Wireframe + Solid"):
        for i in range(jumlah_lantai + 1):
            z_level = [i * tinggi_lantai] * len(xs)
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=z_level, mode='lines',
                                       line=dict(color='#2E86C1' if i > 0 else '#28B463', width=5),
                                       name=f'Lantai {i}' if i > 0 else 'Sloof'))
        for i in range(len(xs) - 1):
            fig.add_trace(go.Scatter3d(x=[xs[i], xs[i]], y=[ys[i], ys[i]], z=[0, tinggi_total], mode='lines',
                                       line=dict(color='#17202A', width=6), showlegend=False))
        if jenis_atap != "Dak Beton (Datar)":
            fig.add_trace(go.Scatter3d(x=[rx_start, rx_end], y=[ridge_y, ridge_y], z=[z_atas + t_atap] * 2, mode='lines',
                                       line=dict(color='#CB4335', width=7), name=jenis_atap))
            cx_, cy_ = [min_x, max_x, max_x, min_x], [min_y, min_y, max_y, max_y]
            for i in range(4):
                tx = rx_start if cx_[i] == min_x else rx_end
                fig.add_trace(go.Scatter3d(x=[cx_[i], tx], y=[cy_[i], ridge_y], z=[z_atas, z_atas + t_atap], mode='lines',
                                           line=dict(color='#CB4335', width=4), showlegend=False))

    if mode in ("Solid", "Wireframe + Solid"):
        dinding, pelat, atap = mesh_baru(), mesh_baru(), mesh_baru()
        for i in range(len(xs) - 1):
            mesh_quad(dinding, (xs[i], ys[i], 0), (xs[i + 1], ys[i + 1], 0),
                      (xs[i + 1], ys[i + 1], tinggi_total), (xs[i], ys[i], tinggi_total))
        for f in range(jumlah_lantai + 1):
            z = f * tinggi_lantai
            for (x0, y0, x1, y1) in ruang_geo:
                mesh_quad(pelat, (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))
        if jenis_atap != "Dak Beton (Datar)":
            c0, c1, c2, c3 = (min_x, min_y, z_atas), (max_x, min_y, z_atas), (max_x, max_y, z_atas), (min_x, max_y, z_atas)
            r0, r1 = (rx_start, ridge_y, z_atas + t_atap), (rx_end, ridge_y, z_atas + t_atap)
            mesh_quad(atap, c0, c1, r1, r0)
            mesh_quad(atap, c2, c3, r0, r1)
            mesh_tri(atap, c0, c3, r0)
            mesh_tri(atap, c1, c2, r1)
        tambah_mesh(fig, dinding, "#F5CBA7", 0.55, "Dinding")
        tambah_mesh(fig, pelat, "#7F8C8D", 0.8, "Pelat Lantai")
        tambah_mesh(fig, atap, "#CB4335", 0.85, "Atap")

    # Kolom (titik)
    fig.add_trace(go.Scatter3d(x=[k[0] for k in kolom_list], y=[k[1] for k in kolom_list], z=[0] * len(kolom_list),
                               mode="markers", marker=dict(size=3, color="#C0392B"), name="Kolom (dasar)"))
    fig.update_layout(scene=dict(aspectmode='data'), margin=dict(l=0, r=0, b=0, t=0), height=560)
    return fig


# ==========================================
# GAMBAR: DENAH STRUKTUR & PONDASI
# ==========================================
def gambar_struktur():
    fig = go.Figure()
    sisi_vis = (sisi_footplat_cm / 100) if not tanah_lunak else 1.0
    for (x, y) in kolom_list:
        rect(fig, x - sisi_vis / 2, y - sisi_vis / 2, x + sisi_vis / 2, y + sisi_vis / 2,
             "rgba(127,140,141,0.35)", "#566573", 1, dash="dash", layer="below")
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#28B463", width=6), name="Sloof / Ring Balok", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[k[0] for k in kolom_list], y=[k[1] for k in kolom_list], mode="markers+text",
                             text=[f"K{i + 1}" for i in range(len(kolom_list))], textposition="top center", textfont=dict(size=9),
                             marker=dict(symbol="square", size=11, color="#C0392B"), name=f"Kolom {dim_kolom}x{dim_kolom} cm"))
    dim_h(fig, min_x, max_x, min_y - 1.5, f"{panjang:.2f} m")
    dim_v(fig, max_x + 1.5, min_y, max_y, f"{lebar:.2f} m")
    atur_2d(fig, "Denah Kolom, Sloof & Pondasi Telapak (indikatif)", (min_x - 2, max_x + 3.5), (min_y - 3, max_y + 2), height=620)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.02))
    return fig


# ==========================================
# EKSPOR DXF (DENAH PER LANTAI) - tanpa library tambahan
# ==========================================
def buat_dxf(idx_lantai):
    layers = {"DINDING": 7, "RUANG": 5, "KOLOM": 1, "JENDELA": 4, "PINTU": 30, "TEKS": 2, "DIMENSI": 3}
    out = ["0", "SECTION", "2", "TABLES",
           "0", "TABLE", "2", "LTYPE", "70", "1",
           "0", "LTYPE", "2", "CONTINUOUS", "70", "0", "3", "Solid line", "72", "65", "73", "0", "40", "0.0",
           "0", "ENDTAB",
           "0", "TABLE", "2", "LAYER", "70", str(len(layers))]
    for nm, col in layers.items():
        out += ["0", "LAYER", "2", nm, "70", "0", "62", str(col), "6", "CONTINUOUS"]
    out += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def garis(x0, y0, x1, y1, layer):
        out.extend(["0", "LINE", "8", layer, "10", f"{x0:.4f}", "20", f"{y0:.4f}", "30", "0",
                    "11", f"{x1:.4f}", "21", f"{y1:.4f}", "31", "0"])

    def teks(x, y, isi, tinggi, layer="TEKS"):
        out.extend(["0", "TEXT", "8", layer, "10", f"{x:.4f}", "20", f"{y:.4f}", "30", "0",
                    "40", f"{tinggi}", "1", isi])

    for r in daftar_ruang(idx_lantai):
        x0, y0, x1, y1 = r["x0"], r["y0"], r["x1"], r["y1"]
        for (a, b, c, d) in [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]:
            garis(a, b, c, d, "RUANG")
        teks(x0 + 0.15, (y0 + y1) / 2 + 0.15, r["nama"], 0.3)
        teks(x0 + 0.15, (y0 + y1) / 2 - 0.25, f"{r['luas']:.1f} m2", 0.25)

    for i in range(len(xs) - 1):
        xa, ya, xb, yb = xs[i], ys[i], xs[i + 1], ys[i + 1]
        garis(xa, ya, xb, yb, "DINDING")
        L = math.hypot(xb - xa, yb - ya)
        if L < 2.5:
            continue
        ux, uy = (xb - xa) / L, (yb - ya) / L
        pos = posisi_bukaan(L)
        depan = abs(ya - yb) < 1e-9 and abs(ya - min_y) < 1e-9
        idx_pintu = min(range(len(pos)), key=lambda q: abs(pos[q] - 0.5)) if (depan and idx_lantai == 0) else -1
        for k, f in enumerate(pos):
            cx, cy = xa + ux * L * f, ya + uy * L * f
            half = 0.5 if k == idx_pintu else 0.7
            garis(cx - ux * half, cy - uy * half, cx + ux * half, cy + uy * half, "PINTU" if k == idx_pintu else "JENDELA")

    s = dim_kolom / 200.0
    for (x, y) in kolom_list:
        for (a, b, c, d) in [(x - s, y - s, x + s, y - s), (x + s, y - s, x + s, y + s),
                             (x + s, y + s, x - s, y + s), (x - s, y + s, x - s, y - s)]:
            garis(a, b, c, d, "KOLOM")

    garis(min_x, min_y - 1.2, max_x, min_y - 1.2, "DIMENSI")
    teks((min_x + max_x) / 2 - 0.5, min_y - 1.7, f"{panjang:.2f} m", 0.3, "DIMENSI")
    garis(max_x + 1.2, min_y, max_x + 1.2, max_y, "DIMENSI")
    teks(max_x + 1.4, (min_y + max_y) / 2, f"{lebar:.2f} m", 0.3, "DIMENSI")
    teks(min_x, max_y + 0.8, f"DENAH LANTAI {idx_lantai + 1} (Elv. +{idx_lantai * tinggi_lantai:.2f} m)", 0.45)

    out += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(out)


# ==========================================
# USER INTERFACE (TABS)
# ==========================================
(tab_denah, tab_tampak, tab_3d, tab_struktur, tab_gempa, tab_tulangan,
 tab_kurva, tab_rab, tab_panduan) = st.tabs([
    "📐 Denah Per Lantai", "🏠 Tampak & Potongan", "👁️ Visualisasi 3D",
    "🏛️ Struktur & Pondasi", "🌋 Analisis Gempa", "🧮 Penulangan",
    "📅 Jadwal & Kurva S", "💰 Estimasi Biaya & Volume", "📚 Panduan Preliminary Design & Beban"])

# ---------- TAB DENAH ----------
with tab_denah:
    st.header("Denah Ruangan Setiap Lantai")
    st.caption("Denah dihasilkan otomatis (skematik) dari bentuk lahan & jumlah ruangan. Garis tosca = jendela, coklat = pintu utama, kotak merah = kolom, kotak abu = tangga.")
    sub = st.tabs([f"Lantai {i + 1}" for i in range(jumlah_lantai)])
    for i, t in enumerate(sub):
        with t:
            fig_d, ruangan = gambar_denah(i)
            st.plotly_chart(fig_d, use_container_width=True, key=f"denah_{i}")
            tombol_unduh(fig_d, f"denah_lantai_{i + 1}.html", f"dl_denah_{i}")
            st.download_button("📐 Unduh DXF (buka di AutoCAD/LibreCAD)", data=buat_dxf(i).encode("utf-8"),
                               file_name=f"denah_lantai_{i + 1}.dxf", mime="application/dxf", key=f"dl_dxf_{i}")
            df_r = pd.DataFrame({
                "Ruangan": [r["nama"] for r in ruangan],
                "Ukuran (m)": [f"{r['w']:.2f} x {r['h']:.2f}" for r in ruangan],
                "Luas (m²)": [round(r["luas"], 2) for r in ruangan]})
            df_r.index += 1
            tampil_tabel(df_r)
            st.caption(f"Luas lantai: {luas_lantai:.2f} m² | Jumlah ruangan: {len(ruangan)}")

# ---------- TAB TAMPAK ----------
with tab_tampak:
    st.header("Tampak & Potongan Bangunan")
    st.caption("Tampak diproyeksikan dari batas terluar (bounding box) bangunan. Pada bentuk L/U, lekukan denah tidak terlihat pada tampak.")
    sub = st.tabs(["Tampak Depan", "Tampak Belakang", "Tampak Kanan", "Tampak Kiri", "Tampak Atas", "Potongan A-A"])
    for t, arah in zip(sub[:4], ["depan", "belakang", "kanan", "kiri"]):
        with t:
            fig_t = gambar_tampak(arah)
            st.plotly_chart(fig_t, use_container_width=True, key=f"tampak_{arah}")
            tombol_unduh(fig_t, f"tampak_{arah}.html", f"dl_tampak_{arah}")
    with sub[4]:
        fig_a = gambar_tampak_atas()
        st.plotly_chart(fig_a, use_container_width=True, key="tampak_atas")
        tombol_unduh(fig_a, "tampak_atas.html", "dl_atas")
    with sub[5]:
        x_cut = st.slider("Posisi garis potong A-A (koordinat X, m)", float(min_x) + 0.1, float(max_x) - 0.1,
                          float(min_x + panjang * 0.45), 0.1)
        fig_p = gambar_potongan(x_cut)
        if fig_p is None:
            st.warning("Garis potong tidak memotong bangunan. Geser posisi X.")
        else:
            st.plotly_chart(fig_p, use_container_width=True, key="potongan")
            tombol_unduh(fig_p, "potongan_AA.html", "dl_potongan")

# ---------- TAB 3D ----------
with tab_3d:
    st.header("Model 3D Bangunan")
    mode_3d = st.radio("Mode tampilan:", ["Wireframe", "Solid", "Wireframe + Solid"], index=2, horizontal=True)
    st.plotly_chart(gambar_3d(mode_3d), use_container_width=True, key="fig3d")

# ---------- TAB STRUKTUR ----------
with tab_struktur:
    st.header("Denah Kolom, Sloof & Pondasi (Preliminary)")
    st.plotly_chart(gambar_struktur(), use_container_width=True, key="fig_struktur")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah Kolom", f"{jumlah_kolom_estimasi} titik")
    m2.metric("Beban Total (layan)", f"{P_total / 1000:,.1f} ton")
    m3.metric("Beban per Kolom (rata-rata)", f"{P_kolom / 1000:,.1f} ton")
    m4.metric("Tegangan Ijin Tanah (asumsi)", f"{sigma_tanah} kg/cm²")
    if not tanah_lunak:
        st.success(f"**Pondasi telapak (footplat) per kolom:** ± {sisi_footplat_cm} x {sisi_footplat_cm} cm (A = P/σ ijin). Kedalaman ± {kedalaman_pondasi:.1f} m.")
    else:
        st.success(f"**Tanah lunak → Tiang pancang:** ± {jumlah_tiang} tiang per kolom (asumsi Q ijin {Q_tiang / 1000:.0f} ton/tiang), dengan pile cap. Wajib uji sondir/CPT.")
    st.info(f"q layan = DL ({DL:.0f}) + LL ({LL}) = {q_layan:.0f} kg/m²  |  DL = berat pelat t={tebal_pelat} cm ({berat_pelat:.0f}) + SIDL ({SIDL}). Faktor +15% untuk berat balok & kolom.")

# ---------- TAB RAB ----------
with tab_rab:
    st.header("Rencana Anggaran Biaya (RAB) Kasar")
    st.info(f"**Luas Lahan Terpakai:** {luas_lantai:.2f} m² | **Total Estimasi Biaya:** Rp {total_biaya:,.0f} | **Harga Bangunan:** Rp {(total_biaya / luas_total_bangunan):,.0f} / m²")
    tampil_tabel(df_rab, kolom_rp=["Estimasi Harga (Rp)"])
    csv = df_rab.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Data Material & RAB (CSV)", data=csv, file_name='RAB_Material_Bangunan.csv', mime='text/csv')

# ---------- TAB PANDUAN ----------
with tab_panduan:
    st.header("Panduan Lengkap: Sipil & Eksekusi Lapangan")
    st.error("⚠️ **DISCLAIMER:** Output dimensi adalah Rule of Thumb. Wajib menggunakan software SAP2000/ETABS untuk DED dan analisis gempa.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("🛒 1. Daftar Belanja Material Utama")
        st.markdown(f"- **Material Dinding:** Siapkan minimal **{kebutuhan_bata:,} {satuan_bata}**.")
        st.markdown(f"- **Semen Perekat:** Butuh ± **{semen_sak:,} sak (50kg)** untuk dinding.")
        st.markdown(f"- **Material Lantai:** Beli **{kebutuhan_dus_lantai} Dus/Box** ({jenis_lantai}). *(Sudah dilebihkan 5% untuk potongan/waste)*.")
        st.markdown(f"- **Estimasi Luas Atap:** {luas_atap:.1f} m²")

    with c2:
        st.subheader("📏 2. Preliminary Design & Pembebanan")
        st.write(f"- Fungsi & Beban: **{fungsi_ruang}** | Kombinasi Ultimate (1.2D+1.6L): **{kombinasi_ultimate:.2f} kg/m²**")

        if kondisi_tanah == "Tanah Keras (Pegunungan)":
            rek_pondasi = "Pondasi Menerus Batu Kali (Kedalaman 60-80cm)"
        elif kondisi_tanah == "Tanah Sedang (Perumahan)":
            rek_pondasi = "Batu Kali + Cakar Ayam/Footplat (Min. 80x80cm) tiap kolom utama"
        else:
            rek_pondasi = "Tiang Pancang Mini (Minipile) / Bor Pile + Pile Cap (Wajib uji Sondir/CPT)"

        st.info(f"**Rekomendasi Pondasi:**\n{rek_pondasi}")

        st.success(f"**Dimensi Beton (Asumsi Jarak Kolom {jarak_kolom_asumsi}m):**\n"
                   f"- **Sloof (h=L/15):** {math.ceil(l_sloof / 5) * 5} x {math.ceil(t_sloof / 5) * 5} cm\n"
                   f"- **Balok Induk (h=L/12):** {math.ceil(l_balok_induk / 5) * 5} x {math.ceil(t_balok_induk / 5) * 5} cm\n"
                   f"- **Balok Anak (h=L/15):** {math.ceil(l_balok_anak / 5) * 5} x {math.ceil(t_balok_anak / 5) * 5} cm\n"
                   f"- **Kolom Utama (b=L_balok):** {dim_kolom} x {dim_kolom} cm (Est. {jumlah_kolom_estimasi} Titik Kolom)\n"
                   f"- **Tebal Pelat Lantai (t=L/35):** {tebal_pelat} cm")

    with c3:
        st.subheader("🏗️ 3. Rekomendasi Besi Tulangan")
        if jumlah_lantai == 1:
            st.success("**Bangunan 1 Lantai:**\n- Tulangan Sloof & Balok: **Ulir D10**\n- Tulangan Kolom Utama: **4D10** (Kolom Praktis 4Ø8)\n- Sengkang/Cincin: **Polos Ø8 jarak 15cm**")
        elif jumlah_lantai == 2:
            besi = "D16" if "Gudang" in fungsi_ruang else "D13"
            st.warning(f"**Bangunan 2 Lantai:**\n- Tulangan Balok Induk: **Ulir {besi}**\n- Tulangan Kolom Utama: **Min. 6D13**\n- Sengkang: **Polos Ø8 jarak 10cm (Daerah Tumpuan/Sendi) & 15cm (Lapangan)**")
        else:
            st.error(f"**{jumlah_lantai} Lantai (Struktur Tinggi):**\n- Kolom Utama: **Besi Ulir D16 / D19**\n- Sengkang: **Polos Ø10**\n- *Wajib menggunakan Detailing Gempa (SRPMK) sesuai SNI 2847-2019!*")


# ==========================================
# TAB ANALISIS GEMPA (STATIK EKIVALEN, SNI 1726:2019 - DISEDERHANAKAN)
# ==========================================
def interp_tabel(x, xt, yt):
    if x <= xt[0]:
        return yt[0]
    if x >= xt[-1]:
        return yt[-1]
    for q in range(len(xt) - 1):
        if xt[q] <= x <= xt[q + 1]:
            return yt[q] + (yt[q + 1] - yt[q]) * (x - xt[q]) / (xt[q + 1] - xt[q])


with tab_gempa:
    st.header("Analisis Gaya Gempa Statik Ekivalen (SNI 1726:2019 – Penyederhanaan)")
    st.warning("⚠️ Untuk pembelajaran/estimasi awal. Nilai tabel Fa/Fv di kode ini adalah pendekatan; cocokkan dengan tabel SNI 1726:2019 "
               "dan ambil Ss, S1 dari **Desain Spektra Indonesia (rsa.ciptakarya.pu.go.id)** sesuai koordinat lokasi. "
               "Nilai Ss/S1 default di bawah hanyalah contoh.")
    kelas_situs = {"Tanah Keras (Pegunungan)": "SC", "Tanah Sedang (Perumahan)": "SD", "Tanah Lunak (Rawa)": "SE"}[kondisi_tanah]
    g1, g2, g3, g4 = st.columns(4)
    Ss = g1.number_input("Ss (g)", min_value=0.0, max_value=3.0, value=0.90, step=0.05)
    S1 = g2.number_input("S1 (g)", min_value=0.0, max_value=2.0, value=0.40, step=0.05)
    sistem_gempa = g3.selectbox("Sistem Penahan Gempa", ["SRPMK (Beton Khusus) R=8", "SRPMM (Beton Menengah) R=5", "SRPMB (Beton Biasa) R=3"], index=1)
    Ie = g4.selectbox("Faktor Keutamaan Ie", [1.0, 1.25, 1.5], index=0)
    R_gempa = {"SRPMK": 8.0, "SRPMM": 5.0, "SRPMB": 3.0}[sistem_gempa.split(" ")[0]]

    FA_TAB = {"SC": [1.3, 1.3, 1.2, 1.2, 1.2], "SD": [1.6, 1.4, 1.2, 1.1, 1.0], "SE": [2.4, 1.7, 1.3, 1.1, 0.9]}
    FV_TAB = {"SC": [1.5, 1.5, 1.5, 1.5, 1.5], "SD": [2.4, 2.2, 2.0, 1.9, 1.8], "SE": [4.2, 3.3, 2.8, 2.4, 2.2]}
    Fa = interp_tabel(Ss, [0.25, 0.5, 0.75, 1.0, 1.25], FA_TAB[kelas_situs])
    Fv = interp_tabel(S1, [0.1, 0.2, 0.3, 0.4, 0.5], FV_TAB[kelas_situs])
    SMS, SM1 = Fa * Ss, Fv * S1
    SDS, SD1 = (2 / 3) * SMS, (2 / 3) * SM1

    T_bang = 0.0466 * (tinggi_total ** 0.9)  # Ta, rangka beton pemikul momen (Ct=0.0466, x=0.9)
    rasio = R_gempa / Ie
    Cs_hit = SDS / rasio
    Cs_maks = SD1 / (T_bang * rasio) if T_bang > 0 else Cs_hit
    Cs_min = max(0.044 * SDS * Ie, 0.01)
    Cs = max(min(Cs_hit, Cs_maks), Cs_min)

    w_lantai_kN = (DL + 0.25 * LL) * luas_lantai * 1.15 * 9.81 / 1000   # berat seismik per lantai (DL + 25% LL)
    W_tot = w_lantai_kN * jumlah_lantai
    V_dasar = Cs * W_tot
    k_dist = 1.0 if T_bang <= 0.5 else (2.0 if T_bang >= 2.5 else 1 + (T_bang - 0.5) / 2)
    pembagi = sum(w_lantai_kN * ((q + 1) * tinggi_lantai) ** k_dist for q in range(jumlah_lantai))
    F_lantai = [V_dasar * w_lantai_kN * ((q + 1) * tinggi_lantai) ** k_dist / pembagi for q in range(jumlah_lantai)]
    V_tingkat = [sum(F_lantai[q:]) for q in range(jumlah_lantai)]

    st.markdown(f"**Kelas situs:** {kelas_situs} (dari kondisi tanah) | **Fa** = {Fa:.2f} | **Fv** = {Fv:.2f}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SDS / SD1", f"{SDS:.3f} / {SD1:.3f} g")
    m2.metric("Periode T (Ta)", f"{T_bang:.3f} detik")
    m3.metric("Koefisien Cs", f"{Cs:.4f}")
    m4.metric("Geser Dasar V", f"{V_dasar:,.1f} kN")
    st.caption(f"Cs hitung = {Cs_hit:.4f} | Cs maks = {Cs_maks:.4f} | Cs min = {Cs_min:.4f} | W seismik total = {W_tot:,.1f} kN | k = {k_dist:.2f}")

    df_gempa = pd.DataFrame({
        "Lantai": [q + 1 for q in range(jumlah_lantai)],
        "Tinggi hi (m)": [(q + 1) * tinggi_lantai for q in range(jumlah_lantai)],
        "Berat wi (kN)": [round(w_lantai_kN, 1)] * jumlah_lantai,
        "Gaya Lateral Fi (kN)": [round(f, 1) for f in F_lantai],
        "Geser Tingkat Vi (kN)": [round(v, 1) for v in V_tingkat],
    }).set_index("Lantai")
    tampil_tabel(df_gempa)
    st.info(f"Perkiraan gaya geser rata-rata per kolom di dasar: **{V_dasar / jumlah_kolom_estimasi:,.1f} kN** ({jumlah_kolom_estimasi} kolom).")

    gc1, gc2 = st.columns(2)
    with gc1:
        fig_f = go.Figure(go.Bar(x=[f"Lt {q + 1}" for q in range(jumlah_lantai)], y=F_lantai, marker_color="#C0392B"))
        fig_f.update_layout(title="Distribusi Gaya Gempa Lateral per Lantai", yaxis_title="Fi (kN)", height=380, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_f, use_container_width=True, key="fig_gempa_f")
    with gc2:
        def Sa_spektrum(Tv):
            if SDS <= 0:
                return 0.0
            T0_ = 0.2 * SD1 / SDS
            Ts_ = SD1 / SDS
            if Tv < T0_:
                return SDS * (0.4 + 0.6 * Tv / T0_)
            if Tv <= Ts_:
                return SDS
            return SD1 / Tv

        Tg = [q * 0.05 for q in range(1, 81)]
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=Tg, y=[Sa_spektrum(v) for v in Tg], mode="lines", line=dict(color="#2E86C1", width=3), name="Spektrum desain"))
        fig_s.add_trace(go.Scatter(x=[T_bang], y=[Sa_spektrum(T_bang)], mode="markers", marker=dict(size=12, color="#C0392B"), name="T bangunan"))
        fig_s.update_layout(title="Spektrum Respons Desain", xaxis_title="T (detik)", yaxis_title="Sa (g)", height=380, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_s, use_container_width=True, key="fig_gempa_s")


# ==========================================
# TAB PENULANGAN (BALOK, PELAT, KOLOM) - SNI 2847 DISEDERHANAKAN
# ==========================================
def as_lentur(Mu_Nmm, b_, d_, fc_, fy_):
    """Luas tulangan tarik perlu (mm2) untuk penampang persegi tulangan tunggal; None bila penampang tidak cukup."""
    Rn = Mu_Nmm / (0.9 * b_ * d_ ** 2)
    term = 1 - 2 * Rn / (0.85 * fc_)
    if term < 0:
        return None
    rho = 0.85 * fc_ / fy_ * (1 - math.sqrt(term))
    return rho * b_ * d_


with tab_tulangan:
    st.header("Perhitungan Penulangan Awal: Balok, Pelat & Kolom")
    st.warning("⚠️ Metode disederhanakan (balok menerus M = wL²/10, pelat 2 arah terjepit penuh koefisien PBI'71, tulangan tunggal). "
               "Hasil untuk latihan/estimasi awal, bukan pengganti perhitungan SAP2000/ETABS.")
    p1, p2, p3 = st.columns(3)
    fc = p1.selectbox("Mutu beton f'c (MPa)", [20, 25, 30, 35], index=1)
    fy = p2.selectbox("Mutu baja ulir fy (MPa)", [420, 500], index=0)
    dia_balok = p3.selectbox("Diameter tulangan utama balok (mm)", [13, 16, 19, 22], index=0)
    fyt = 280  # sengkang polos

    # ---------- BALOK INDUK ----------
    st.subheader("1. Balok Induk")
    b_mm = math.ceil(l_balok_induk / 5) * 5 * 10
    h_mm = math.ceil(t_balok_induk / 5) * 5 * 10
    d_mm = h_mm - 60
    L_m = jarak_kolom_asumsi
    qu_pelat = kombinasi_ultimate * 9.81 / 1000            # kN/m2
    wu_balok = qu_pelat * L_m + 1.2 * 24 * (b_mm / 1000) * (h_mm / 1000)   # kN/m (lebar tributari = L)
    Mu_balok = wu_balok * L_m ** 2 / 10                    # kNm
    Vu_balok = wu_balok * L_m / 2                          # kN
    As_perlu = as_lentur(Mu_balok * 1e6, b_mm, d_mm, fc, fy)
    st.write(f"Penampang **{b_mm // 10} x {h_mm // 10} cm**, bentang {L_m:.1f} m, wu = {wu_balok:.1f} kN/m, "
             f"Mu = {Mu_balok:.1f} kNm, Vu = {Vu_balok:.1f} kN")
    if As_perlu is None:
        st.error("Penampang balok tidak cukup untuk momen ini (tanpa tulangan tekan). Perbesar dimensi balok / kurangi bentang.")
    else:
        As_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy) * b_mm * d_mm
        As_pakai = max(As_perlu, As_min)
        A_bar = math.pi / 4 * dia_balok ** 2
        n_tarik = max(2, math.ceil(As_pakai / A_bar))
        n_maks = max(1, int((b_mm - 2 * 48 + 25) // (dia_balok + 25)))
        n_tekan = max(2, math.ceil(n_tarik / 2))
        catatan_lapis = " (perlu **2 lapis** — jarak antar besi tidak cukup 1 lapis)" if n_tarik > n_maks else ""
        # geser
        Vu_N = Vu_balok * 1000
        Vc = 0.17 * math.sqrt(fc) * b_mm * d_mm
        Vs = Vu_N / 0.75 - Vc
        Av = 2 * math.pi / 4 * 8 ** 2
        if Vs > 0.66 * math.sqrt(fc) * b_mm * d_mm:
            st.error("Dimensi balok tidak cukup untuk geser (Vs melebihi batas). Perbesar penampang.")
        s_hit = d_mm / 2 if Vs <= 0 else Av * fyt * d_mm / Vs
        s_lap = int(min(s_hit, d_mm / 2, 300) // 10 * 10)
        s_tump = int(min(s_hit, d_mm / 4, 6 * dia_balok, 150) // 10 * 10)
        st.success(f"**Lentur:** As perlu = {As_perlu:.0f} mm² (As min = {As_min:.0f} mm²) → **{n_tarik}D{dia_balok}** tarik{catatan_lapis}, "
                   f"**{n_tekan}D{dia_balok}** tekan.\n\n"
                   f"**Geser:** Vc = {Vc / 1000:.1f} kN, Vs perlu = {max(Vs, 0) / 1000:.1f} kN → sengkang **Ø8-{s_tump} mm** (daerah tumpuan, 2h dari muka kolom) "
                   f"dan **Ø8-{s_lap} mm** (lapangan).")

    # ---------- PELAT ----------
    st.subheader("2. Pelat Lantai (strip 1 m)")
    t_mm = tebal_pelat * 10
    d_pelat = t_mm - 25
    qu_p = kombinasi_ultimate * 9.81 / 1000
    M_lap = 0.001 * qu_p * L_m ** 2 * 21
    M_tump = 0.001 * qu_p * L_m ** 2 * 52
    As_min_p = 0.0018 * 1000 * t_mm
    A_d10 = math.pi / 4 * 10 ** 2

    def tulangan_pelat(Mu_kNm):
        As_ = as_lentur(Mu_kNm * 1e6, 1000, d_pelat, fc, fy)
        if As_ is None:
            return None, None
        As_ = max(As_, As_min_p)
        s_ = int(min(1000 * A_d10 / As_, 3 * t_mm, 450) // 25 * 25)
        return As_, max(s_, 50)

    As_l, s_l = tulangan_pelat(M_lap)
    As_t, s_t = tulangan_pelat(M_tump)
    st.write(f"Tebal **{tebal_pelat} cm**, bentang {L_m:.1f} x {L_m:.1f} m, qu = {qu_p:.2f} kN/m², "
             f"M lapangan = {M_lap:.2f} kNm/m, M tumpuan = {M_tump:.2f} kNm/m")
    if As_l is None or As_t is None:
        st.error("Tebal pelat tidak cukup untuk momen ini. Tambah tebal pelat.")
    else:
        st.success(f"**Lapangan:** As = {As_l:.0f} mm²/m → **D10-{s_l} mm** (dua arah)\n\n"
                   f"**Tumpuan:** As = {As_t:.0f} mm²/m → **D10-{s_t} mm** (dua arah)")

    # ---------- KOLOM ----------
    st.subheader("3. Cek Kolom Lantai Dasar")
    Pu_N = 1.4 * P_kolom * 9.81            # pendekatan Pu ≈ 1.4 x beban layan
    rho_kol = 0.02
    Ag_perlu = Pu_N / (0.52 * (0.85 * fc * (1 - rho_kol) + fy * rho_kol))
    sisi_perlu = math.ceil(math.sqrt(Ag_perlu) / 50) * 5   # cm
    sisi_pakai = max(dim_kolom, sisi_perlu, 20)
    n_besi_kol = max(4, math.ceil(rho_kol * (sisi_pakai * 10) ** 2 / (math.pi / 4 * 16 ** 2) / 2) * 2)
    st.write(f"Pu ≈ 1.4 x P layan = {Pu_N / 1000:,.0f} kN (kolom rata-rata). Luas bruto perlu (ρ=2%) = {Ag_perlu / 100:,.0f} cm² → sisi min ≈ {sisi_perlu} cm.")
    st.success(f"**Kolom disarankan: {sisi_pakai} x {sisi_pakai} cm** dengan ± **{n_besi_kol}D16** (ρ≈2%) dan sengkang Ø8-100 mm di daerah sendi plastis. "
               f"Pengaruh momen/gempa belum termasuk — wajib dicek di software.")


# ==========================================
# TAB JADWAL & KURVA S
# ==========================================
with tab_kurva:
    st.header("Jadwal Pelaksanaan & Kurva S")
    st.caption("Bobot pekerjaan diambil dari RAB. Edit minggu mulai & durasi pada tabel. Progres tiap pekerjaan memakai distribusi sinus (lambat–cepat–lambat).")
    beton_start = 4
    dur_beton = 3 + 3 * jumlah_lantai
    dinding_start = beton_start + 3
    dur_dinding = 2 + 2 * jumlah_lantai
    atap_start = beton_start + dur_beton - 1
    lantai_start = dinding_start + dur_dinding - 1
    df_jadwal_awal = pd.DataFrame({
        "Pekerjaan": df_rab["Pekerjaan"].tolist(),
        "Mulai (minggu ke-)": [1, beton_start, dinding_start, lantai_start, atap_start],
        "Durasi (minggu)": [3, dur_beton, dur_dinding, 2 + jumlah_lantai, 3],
    })
    df_jadwal = df_jadwal_awal
    starts, durs = [], []
    kol_j = st.columns(len(df_jadwal_awal))
    for q in range(len(df_jadwal_awal)):
        with kol_j[q]:
            st.markdown(f"**{df_jadwal_awal['Pekerjaan'][q]}**")
            kunci = f"{q}_{jumlah_lantai}_{material_dinding}_{jenis_atap}"
            starts.append(int(st.number_input("Mulai (minggu ke-)", min_value=1, max_value=200, step=1,
                                              value=int(df_jadwal_awal["Mulai (minggu ke-)"][q]), key=f"mulai_{kunci}")))
            durs.append(int(st.number_input("Durasi (minggu)", min_value=1, max_value=200, step=1,
                                            value=int(df_jadwal_awal["Durasi (minggu)"][q]), key=f"durasi_{kunci}")))
    biaya_item = df_rab["Estimasi Harga (Rp)"].tolist()
    bobot = [b_ / total_biaya for b_ in biaya_item]
    total_minggu = max(s_ + d_ - 1 for s_, d_ in zip(starts, durs))

    def frac_selesai(w, s_, d_):
        u = min(max((w - s_ + 1) / d_, 0.0), 1.0)
        return 0.5 * (1 - math.cos(math.pi * u))

    kum = []
    for w in range(1, total_minggu + 1):
        kum.append(sum(bobot[q] * frac_selesai(w, starts[q], durs[q]) for q in range(len(bobot))) * 100)
    mingguan = [kum[0]] + [kum[q] - kum[q - 1] for q in range(1, len(kum))]
    minggu_lbl = list(range(1, total_minggu + 1))

    k1, k2, k3 = st.columns(3)
    k1.metric("Durasi Total", f"{total_minggu} minggu (± {total_minggu / 4.345:.1f} bulan)")
    k2.metric("Total Biaya", f"Rp {total_biaya:,.0f}")
    k3.metric("Rata-rata Biaya/Minggu", f"Rp {total_biaya / total_minggu:,.0f}")

    fig_k = go.Figure()
    fig_k.add_trace(go.Bar(x=minggu_lbl, y=mingguan, name="Bobot mingguan (%)", marker_color="#AED6F1"))
    fig_k.add_trace(go.Scatter(x=minggu_lbl, y=kum, mode="lines+markers", name="Kumulatif (%) – Kurva S", line=dict(color="#C0392B", width=3)))
    fig_k.update_layout(title="Kurva S Rencana", xaxis_title="Minggu ke-", yaxis_title="Bobot (%)", height=420,
                        margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_k, use_container_width=True, key="fig_kurva_s")

    fig_g = go.Figure()
    warna_g = ["#7F8C8D", "#2E86C1", "#E59866", "#28B463", "#CB4335"]
    for q, nm in enumerate(df_jadwal["Pekerjaan"].tolist()):
        fig_g.add_trace(go.Bar(y=[nm], x=[durs[q]], base=[starts[q] - 1], orientation="h", marker_color=warna_g[q % 5],
                               text=f"{bobot[q] * 100:.1f}%", textposition="inside", showlegend=False))
    fig_g.update_layout(title="Bagan Balok (Gantt Chart)", xaxis_title="Minggu", height=350,
                        yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig_g, use_container_width=True, key="fig_gantt")

    df_s = pd.DataFrame({"Minggu": minggu_lbl, "Bobot Mingguan (%)": [round(v, 2) for v in mingguan],
                         "Kumulatif (%)": [round(v, 2) for v in kum],
                         "Biaya Kumulatif (Rp)": [round(v / 100 * total_biaya) for v in kum]}).set_index("Minggu")
    tampil_tabel(df_s, kolom_rp=["Biaya Kumulatif (Rp)"])
    st.download_button("📥 Download Jadwal & Kurva S (CSV)", data=df_s.to_csv().encode("utf-8"),
                       file_name="Kurva_S.csv", mime="text/csv", key="dl_kurva")
