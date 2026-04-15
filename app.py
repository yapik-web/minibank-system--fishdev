from flask import Flask, request, jsonify, render_template
import io
import base64
import matplotlib
matplotlib.use('Agg') # Mencegah error matplotlib di server backend
import matplotlib.pyplot as plt

# KITA IMPORT KODE ASLI KAMU TANPA MENGUBAHNYA
import bank_app 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    # bank_app.register mengembalikan (pesan, gr.update, gr.update)
    # Kita ambil index [0] yaitu pesannya saja
    res = bank_app.register(data['username'], data['password'])
    return jsonify({"message": res[0]})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    res = bank_app.login(data['username'], data['password'])
    msg, user = res.split("|")
    return jsonify({"message": msg, "user": user})

@app.route('/api/saldo', methods=['POST'])
def api_saldo():
    data = request.json
    res = bank_app.cek_saldo(data['user'])
    return jsonify({"message": res})

@app.route('/api/setor', methods=['POST'])
def api_setor():
    data = request.json
    res = bank_app.setor(data['user'], data['jumlah'])
    return jsonify({"message": res[0]})

@app.route('/api/tarik', methods=['POST'])
def api_tarik():
    data = request.json
    res = bank_app.tarik(data['user'], data['jumlah'])
    return jsonify({"message": res[0]})

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    data = request.json
    res = bank_app.transfer(data['user'], data['tujuan'], data['jumlah'])
    return jsonify({"message": res[0]})

@app.route('/api/riwayat', methods=['POST'])
def api_riwayat():
    data = request.json
    teks, fig = bank_app.riwayat_dan_grafik(data['user'])
    
    if fig is None:
        return jsonify({"message": teks, "image": None})
    
    # Konversi figure Matplotlib ke format gambar Base64 untuk ditampilkan di HTML
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', facecolor='#111111')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    
    return jsonify({"message": teks, "image": img_base64})

import os

if __name__ == '__main__':
    # Ambil port dari environment variable yang disediakan Render
    port = int(os.environ.get("PORT", 5000))
    # Jalankan app dengan host 0.0.0.0 agar bisa diakses publik
    app.run(host='0.0.0.0', port=port)