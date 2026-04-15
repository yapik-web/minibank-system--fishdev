import os
import json
import hashlib
import gradio as gr
from datetime import datetime, timedelta  # TAMBAHAN: import timedelta untuk penyesuaian jam
import matplotlib.pyplot as plt  # Untuk menggambar grafik
import qrcode  # TAMBAHAN: Untuk membuat QR code di terminal

DATA_FILE = "bank.json"

# LOAD & SAVE
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "riwayat": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# HASH PASSWORD
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# AUTH
def register(username, password):
    global data
    if username in data["users"]:
        return "❌ Username sudah ada!", gr.update(value=""), gr.update(value="")
    
    data["users"][username] = {
        "password": hash_password(password),
        "saldo": 0
    }
    save_data(data)
    return "✅ Registrasi berhasil!", gr.update(value=""), gr.update(value="")

def login(username, password):
    user = data["users"].get(username)
    if user and user["password"] == hash_password(password):
        return f"✅ Login berhasil!|{username}"
    return "❌ Login gagal!|"

def validasi(user):
    return user and user in data["users"]

# FITUR BANK
def cek_saldo(user):
    if not validasi(user):
        return "❌ Silakan login dulu!"
    return f" Saldo: {data['users'][user]['saldo']}"

def setor(user, jumlah):
    global data
    if not validasi(user):
        return "❌ Silakan login dulu!", gr.update(value="")
    try:
        jumlah = int(jumlah)
        if jumlah <= 0:
            return "❌ Harus > 0", gr.update(value="")
        
        # UBAH: Format menjadi Hari dan Menit disesuaikan ke WIB (UTC+7)
        tanggal_sekarang = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M") 
        data["users"][user]["saldo"] += jumlah
        data["riwayat"].append({"username": user, "aktivitas": f"Setor: {jumlah}", "tanggal": tanggal_sekarang})
        save_data(data)
        return "✅ Berhasil setor!", gr.update(value="")
    except:
        return "❌ Input tidak valid", gr.update(value="")

def tarik(user, jumlah):
    global data
    if not validasi(user):
        return "❌ Silakan login dulu!", gr.update(value="")
    try:
        jumlah = int(jumlah)
        if jumlah <= 0:
            return "❌ Harus > 0", gr.update(value="")
        
        if data["users"][user]["saldo"] < jumlah:
            return "❌ Saldo tidak cukup!", gr.update(value="")
        
        # UBAH: Format menjadi Hari dan Menit disesuaikan ke WIB (UTC+7)
        tanggal_sekarang = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
        data["users"][user]["saldo"] -= jumlah
        data["riwayat"].append({"username": user, "aktivitas": f"Tarik: {jumlah}", "tanggal": tanggal_sekarang})
        save_data(data)
        return "✅ Berhasil tarik!", gr.update(value="")
    except:
        return "❌ Input tidak valid", gr.update(value="")

def transfer(user, tujuan, jumlah):
    global data
    if not validasi(user):
        return "❌ Silakan login dulu!", gr.update(value=""), gr.update(value="")
    
    if tujuan not in data["users"]:
        return "❌ User tidak ditemukan!", gr.update(value=""), gr.update(value="")
    
    try:
        jumlah = int(jumlah)
        if jumlah <= 0:
            return "❌ Harus > 0", gr.update(value=""), gr.update(value="")
        
        if data["users"][user]["saldo"] < jumlah:
            return "❌ Saldo tidak cukup!", gr.update(value=""), gr.update(value="")
        
        # UBAH: Format menjadi Hari dan Menit disesuaikan ke WIB (UTC+7)
        tanggal_sekarang = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
        data["users"][user]["saldo"] -= jumlah
        data["users"][tujuan]["saldo"] += jumlah
        
        data["riwayat"].append({"username": user, "aktivitas": f"Transfer ke {tujuan}: {jumlah}", "tanggal": tanggal_sekarang})
        data["riwayat"].append({"username": tujuan, "aktivitas": f"Diterima dari {user}: {jumlah}", "tanggal": tanggal_sekarang})
        
        save_data(data)
        return "✅ Transfer berhasil!", gr.update(value=""), gr.update(value="")
    except:
        return "❌ Input tidak valid", gr.update(value=""), gr.update(value="")

# FUNGSI GABUNGAN RIWAYAT & GRAFIK (DIUBAH KE GAYA TRADING)
def riwayat_dan_grafik(user):
    if not validasi(user):
        return "❌ Silakan login dulu!", None
    
    # 1. Teks Riwayat
    logs = []
    transaksi_per_waktu = {}
    
    for r in data["riwayat"]:
        if r["username"] == user:
            # Fallback jika data riwayat lama menggunakan format lama (disesuaikan ke WIB juga)
            tgl = r.get("tanggal", (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M"))
            logs.append(f"[{tgl}] {r['aktivitas']}")
            
            # Ekstrak waktu per JAM (YYYY-MM-DD HH:00) untuk grafik
            # Memotong menit agar terkumpul dalam jam yang sama
            tgl_jam = tgl[:13] + ":00" if len(tgl) >= 13 else tgl
            
            # Hitung jumlah transaksi untuk grafik
            transaksi_per_waktu[tgl_jam] = transaksi_per_waktu.get(tgl_jam, 0) + 1
            
    teks_riwayat = "\n".join(logs) if logs else "Belum ada transaksi"
    
    # 2. Gambar Grafik ala Trading
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Set background grafik gelap (mirip platform trading)
    fig.patch.set_facecolor('#111111')
    ax.set_facecolor('#111111')
    
    if not transaksi_per_waktu:
        ax.text(0.5, 0.5, "NO DATA AVAILABLE", ha='center', va='center', color="gray", fontweight="bold")
        ax.axis("off")
    else:
        waktus = list(transaksi_per_waktu.keys())
        jumlahs = list(transaksi_per_waktu.values())
        
        # Urutkan berdasarkan waktu
        waktus, jumlahs = zip(*sorted(zip(waktus, jumlahs)))
        
        # Plot garis gaya trading (Line with filled area)
        ax.plot(waktus, jumlahs, color='#00ff88', linewidth=2, marker='o', markersize=4)
        ax.fill_between(waktus, jumlahs, color='#00ff88', alpha=0.15)
        
        ax.set_title("TRANSACTION VOLUME (H1)", color="#ffffff", fontweight="bold", pad=15)
        ax.set_ylabel("Volume", fontweight="bold", color="#a0a0b0")
        
        # Grid ala trading view
        ax.grid(color='#333344', linestyle='--', linewidth=0.5)
        
        # Ubah warna teks sumbu (ticks)
        ax.tick_params(axis='x', colors='#a0a0b0', rotation=30, labelsize=8)
        ax.tick_params(axis='y', colors='#a0a0b0', labelsize=8)
        
        # Bersihkan border/spine
        for spine in ax.spines.values():
            spine.set_edgecolor('#333344')
            
    plt.tight_layout()
    return teks_riwayat, fig

# LOGIN HANDLER
def handle_login(username, password):
    res = login(username, password)
    msg, user = res.split("|")
    
    if user:
        return (
            msg,
            user,
            gr.update(visible=True),       
            gr.update(visible=True),   
            gr.update(visible=False),  
            gr.update(visible=False),  
            gr.update(selected="dashboard"),   
            gr.update(value=""),
            gr.update(value="")
        )
    else:
        return (
            msg,
            "",
            gr.update(visible=False), 
            gr.update(visible=False), 
            gr.update(visible=True),  
            gr.update(visible=True),  
            gr.update(selected="login"),      
            gr.update(value=""),
            gr.update(value="")
        )

# TOGGLE PASSWORD
def toggle_password(show):
    return gr.update(type="text" if show else "password")

# LOGOUT
def logout():
    return (
        "",
        gr.update(visible=False), 
        gr.update(visible=False), 
        gr.update(visible=True),  
        gr.update(visible=True),  
        gr.update(selected="login"),          
        " Berhasil logout!"
    )

# CSS (TIDAK DIUBAH)
css = """
body {
    background: linear-gradient(135deg, #1e3c72, #2a5298);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.main-title h1 {
    text-align: center;
    color: white;
    font-size: 2.5em;
    margin-bottom: 20px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
}

button {
    background: linear-gradient(45deg, #00c6ff, #0072ff) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all 0.3s ease-in-out !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    font-weight: bold !important;
}

button:hover {
    transform: translateY(-2px);
    background: linear-gradient(45deg, #0072ff, #00c6ff) !important;
}

textarea, input {
    border-radius: 8px !important;
    background-color: rgba(255, 255, 255, 0.9) !important;
    color: #333 !important;
}

.gradio-container label > span {
    background: #0072ff !important;
    color: white !important;
    border-radius: 5px !important;
}
"""

# UI (TIDAK DIUBAH)
with gr.Blocks(css=css, theme=gr.themes.Soft()) as app:
    gr.Markdown("#  Mini Bank System", elem_classes="main-title")

    user_state = gr.State("")

    with gr.Tabs() as tabs_container:
        
        # LOGIN TAB
        with gr.Tab("Login", id="login") as login_tab:
            with gr.Row():
                with gr.Column(scale=1): pass
                with gr.Column(scale=2):
                    gr.Markdown("###  Hi Welcome Back!")
                    username = gr.Textbox(label="Username", placeholder="Masukkan username...")
                    password = gr.Textbox(label="Password", type="password", placeholder="Masukkan password...")
                    show_pass = gr.Checkbox(label="👁 Show Password")
                    login_btn = gr.Button(" Login", variant="primary")
                    login_out = gr.Textbox(label="Status", interactive=False)
                with gr.Column(scale=1): pass

        # REGISTER TAB
        with gr.Tab("Register", id="register") as register_tab:
            with gr.Row():
                with gr.Column(scale=1): pass
                with gr.Column(scale=2):
                    gr.Markdown("###  Buat Akun Baru")
                    reg_user = gr.Textbox(label="Username", placeholder="Pilih username...")
                    reg_pass = gr.Textbox(label="Password", type="password", placeholder="Buat password...")
                    show_pass_reg = gr.Checkbox(label="👁 Show Password")
                    reg_btn = gr.Button("Daftar Sekarang", variant="primary")
                    reg_out = gr.Textbox(label="Status", interactive=False)
                with gr.Column(scale=1): pass

        # DASHBOARD TAB
        with gr.Tab("Dashboard", visible=False, id="dashboard") as dashboard_tab:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("###  Informasi Rekening")
                    saldo_out = gr.Textbox(label="Saldo Saat Ini", interactive=False, value="💰 Saldo: 0")
                    cek_btn = gr.Button(" Cek Saldo", variant="primary")
                with gr.Column(scale=1):
                    gr.Markdown("###  Transaksi Cepat")
                    setor_in = gr.Textbox(label="Jumlah Setor", placeholder="Rp...")
                    setor_btn = gr.Button(" Setor")
                    tarik_in = gr.Textbox(label="Jumlah Tarik", placeholder="Rp...")
                    tarik_btn = gr.Button(" Tarik")
                    aksi_out = gr.Textbox(label="Status Transaksi", interactive=False)
            
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column(scale=1):
                    riwayat_out = gr.TextArea(label="Daftar Aktivitas", interactive=False, lines=11)
                with gr.Column(scale=1):
                    grafik_out = gr.Plot(label="Analisis Transaksi")
                    
            with gr.Row():
                riwayat_btn = gr.Button(" Lihat Riwayat & Grafik", variant="secondary")
                logout_btn = gr.Button(" Logout", variant="stop")
            logout_out = gr.Textbox(label="Status Logout", interactive=False)

        # TRANSFER TAB
        with gr.Tab("Transfer", visible=False, id="transfer") as transfer_tab:
            with gr.Row():
                with gr.Column(scale=1): pass
                with gr.Column(scale=2):
                    gr.Markdown("###  Kirim Dana")
                    tujuan = gr.Textbox(label="Username Tujuan", placeholder="Masukkan username tujuan...")
                    jumlah_tf = gr.Textbox(label="Nominal Transfer", placeholder="Rp...")
                    tf_btn = gr.Button(" Kirim Dana", variant="primary")
                    tf_out = gr.Textbox(label="Status Transfer", interactive=False)
                with gr.Column(scale=1): pass

    # EVENT LISTENERS
    login_btn.click(
        handle_login,
        [username, password],
        [login_out, user_state, dashboard_tab, transfer_tab, login_tab, register_tab, tabs_container, username, password]
    )

    reg_btn.click(register, [reg_user, reg_pass], [reg_out, reg_user, reg_pass])
    show_pass.change(toggle_password, show_pass, password)
    show_pass_reg.change(toggle_password, show_pass_reg, reg_pass)
    cek_btn.click(cek_saldo, user_state, saldo_out)
    setor_btn.click(setor, [user_state, setor_in], [aksi_out, setor_in])
    tarik_btn.click(tarik, [user_state, tarik_in], [aksi_out, tarik_in])
    tf_btn.click(transfer, [user_state, tujuan, jumlah_tf], [tf_out, tujuan, jumlah_tf])
    
    riwayat_btn.click(riwayat_dan_grafik, user_state, [riwayat_out, grafik_out])
    
    logout_btn.click(
        logout,
        [],
        [user_state, dashboard_tab, transfer_tab, login_tab, register_tab, tabs_container, logout_out]
    )

# MODIFIKASI BAGIAN DEPLOYMENT AGAR MENGHASILKAN QR CODE DI TERMINAL


if __name__ == "__main__":
    import time
    
    # Jalankan app tanpa melakukan blocking (prevent_thread_lock=True) 
    # dan aktifkan share=True agar mendapatkan Public URL
    app.launch(share=True, prevent_thread_lock=True)
    
    # Ambil URL Share Publik
    public_url = app.share_url
    
    if public_url:
        print("\n" + "="*50)
        print(" AKSES DARI HP / DEVICE LAIN ")
        print("="*50)
        print(f"Buka URL ini: {public_url}")
        print("Atau scan QR Code di bawah ini:\n")
        
        # Buat objek QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(public_url)
        qr.make(fit=True)
        
        # Print QR Code langsung ke terminal (invert=True cocok untuk terminal background gelap)
        # Jika terminal kamu warna terang (putih), ganti invert=False
        qr.print_ascii(invert=True)
        print("="*50 + "\n")
    
    # Buat loop agar terminal tidak langsung menutup karena thread tidak di-lock
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer dimatikan.")