"""
CHIFIA - Chili Intelligent Farming with AI
Flask Backend (YOLOv26 Compatible)
"""

import os
import io
import base64
import random
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont


app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ──────────────────────────────────────────────
# DISEASE CLASS CONFIG
# ──────────────────────────────────────────────
DISEASE_CLASSES = {
    0: {"name": "bercak_daun",   "label": "Bercak Daun",   "color": (234,179,8),   "hex": "#EAB308", "severity": "Ringan",  "icon": "🟡",
        "cause": "Disebabkan oleh jamur Cercospora capsici yang berkembang di kondisi lembab dan suhu hangat. Spora menyebar melalui angin dan percikan air hujan."},
    1: {"name": "daun_keriting", "label": "Daun Keriting",  "color": (249,115,22),  "hex": "#F97316", "severity": "Sedang",  "icon": "🟠",
        "cause": "Disebabkan oleh infeksi virus (Pepper Yellow Leaf Curl Virus) yang ditularkan oleh kutu daun (Aphid) dan thrips sebagai serangga vektor."},
    2: {"name": "healthy",       "label": "Daun Sehat",     "color": (34,197,94),   "hex": "#22C55E", "severity": "Sehat",   "icon": "✅",
        "cause": "Tanaman dalam kondisi sehat dan tidak menunjukkan gejala penyakit."},
    3: {"name": "kutu_kebul",    "label": "Kutu Kebul",     "color": (167,139,250), "hex": "#A78BFA", "severity": "Sedang",  "icon": "🟣",
        "cause": "Serangan hama Bemisia tabaci (kutu kebul/whitefly) yang menghisap cairan daun dan mengeluarkan embun madu, memicu pertumbuhan jamur jelaga."},
    4: {"name": "virus_kuning",  "label": "Virus Kuning",   "color": (239,68,68),   "hex": "#EF4444", "severity": "Berat",   "icon": "🔴",
        "cause": "Disebabkan oleh Begomovirus (Pepper Yellow Leaf Curl Virus) yang ditularkan secara persisten oleh kutu kebul (Bemisia tabaci). Tidak ada obat untuk tanaman yang sudah terinfeksi."},
}
TREATMENT = {
    "healthy":       "Tidak diperlukan tindakan. Lanjutkan perawatan rutin dan pantau tanaman secara berkala.",
    "bercak_daun":   "Semprotkan fungisida berbahan aktif mankozeb atau klorotalonil setiap 7 hari. Buang dan musnahkan daun yang terinfeksi. Hindari penyiraman dari atas dan perbaiki drainase lahan.",
    "daun_keriting": "Kendalikan kutu daun dengan insektisida sistemik (imidakloprid atau abamektin). Cabut dan musnahkan tanaman yang terinfeksi berat. Gunakan mulsa reflektif untuk mengusir kutu.",
    "kutu_kebul":    "Semprotkan insektisida imidakloprid, thiamethoxam, atau spirotetramat. Pasang perangkap lengket kuning. Bersihkan gulma di sekitar tanaman dan atur jarak tanam agar tidak rapat.",
    "virus_kuning":  "Cabut dan musnahkan tanaman yang bergejala segera untuk mencegah penyebaran. Kendalikan kutu kebul sebagai vektor utama. Tidak ada pengobatan untuk tanaman yang sudah terinfeksi virus.",
}



# ──────────────────────────────────────────────
# LOAD MODEL (YOLOv26 or Demo)
# ──────────────────────────────────────────────
MODEL = None
MODEL_MODE = "demo"

def try_load_yolo():
    global MODEL, MODEL_MODE
    model_onnx = os.path.join("model", "best.onnx")
    model_pt = os.path.join("model", "best.pt")
    model_path = model_onnx if os.path.exists(model_onnx) else (model_pt if os.path.exists(model_pt) else None)
    if model_path:
        try:
            from ultralytics import YOLO
            MODEL = YOLO(model_path, task='detect')
            MODEL_MODE = "yolo"
            print(f"[CHIFIA] OK YOLO model loaded: {model_path}")
        except Exception as e:
            print(f"[CHIFIA] WARN YOLO load failed: {e} -> using demo mode")
    else:
        print("[CHIFIA] DEMO mode (no model found)")

try_load_yolo()

# ──────────────────────────────────────────────
# IMAGE UTILITIES
# ──────────────────────────────────────────────
def read_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) > 1280:
        ratio = 1280 / max(w, h)
        img = img.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
    return img


def pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def draw_boxes(img: Image.Image, detections: list) -> Image.Image:
    out = img.copy()
    draw = ImageDraw.Draw(out, "RGBA")
    try:
        font_big = ImageFont.truetype("arial.ttf", 15)
    except:
        font_big = ImageFont.load_default()

    W, H = img.size
    for d in detections:
        cls = DISEASE_CLASSES.get(d["class_id"], DISEASE_CLASSES[0])
        rgb = cls["color"]
        x1,y1,x2,y2 = d["bbox"]["x1"],d["bbox"]["y1"],d["bbox"]["x2"],d["bbox"]["y2"]
        th = max(2, int(min(W,H)*0.004))
        # fill
        draw.rectangle([x1,y1,x2,y2], fill=(*rgb,35))
        # border
        for t in range(th):
            draw.rectangle([x1+t,y1+t,x2-t,y2-t], outline=(*rgb,255))
        # corner marks
        cl = max(14, int(min(W,H)*0.03))
        ct = th+1
        for (ax,ay,bx,by) in [(x1,y1,x1+cl,y1+ct),(x1,y1,x1+ct,y1+cl),
                               (x2-cl,y1,x2,y1+ct),(x2-ct,y1,x2,y1+cl),
                               (x1,y2-ct,x1+cl,y2),(x1,y2-cl,x1+ct,y2),
                               (x2-cl,y2-ct,x2,y2),(x2-ct,y2-cl,x2,y2)]:
            draw.rectangle([ax,ay,bx,by], fill=(*rgb,255))
        # label
        txt = f" {cls['label']}  {d['confidence']:.0%} "
        try:
            bb = draw.textbbox((0,0), txt, font=font_big)
            tw,th2 = bb[2]-bb[0], bb[3]-bb[1]
        except:
            tw,th2 = 120,16
        pad=4
        ly1 = y1 - th2 - pad*2
        ly2 = y1
        if ly1 < 0: ly1,ly2 = y1, y1+th2+pad*2
        draw.rectangle([x1,ly1,x1+tw+pad*2,ly2], fill=(*rgb,220))
        draw.text((x1+pad, ly1+pad), txt, fill=(255,255,255,255), font=font_big)
    return out

# ──────────────────────────────────────────────
# DEMO DETECTOR
# ──────────────────────────────────────────────
def demo_detect(img: Image.Image) -> list:
    W, H = img.size
    scenario = random.choices(
        ["healthy","single","multi"], weights=[0.2,0.55,0.25])[0]
    if scenario == "healthy":
        picks = [2]
    elif scenario == "single":
        picks = [random.choice([1,2,3,4])]
        if random.random()>0.5: picks.append(0)
    else:
        picks = random.sample([1,2,3,4], 2)
        if random.random()>0.6: picks.append(0)

    zones = [(0.05,0.05,0.45,0.45),(0.55,0.05,0.95,0.45),
             (0.05,0.55,0.45,0.95),(0.55,0.55,0.95,0.95),(0.25,0.25,0.75,0.75)]
    random.shuffle(zones)
    detections = []
    for i, cid in enumerate(picks[:len(zones)]):
        zx1,zy1,zx2,zy2 = zones[i]
        bw = random.uniform(0.22,0.42)*(zx2-zx1)
        bh = random.uniform(0.22,0.42)*(zy2-zy1)
        cx = random.uniform(zx1+bw/2, zx2-bw/2)
        cy = random.uniform(zy1+bh/2, zy2-bh/2)
        x1=max(0.04,cx-bw/2); y1=max(0.04,cy-bh/2)
        x2=min(0.96,cx+bw/2); y2=min(0.96,cy+bh/2)
        conf = random.uniform(0.82,0.99) if cid==0 else random.uniform(0.65,0.97)
        cls = DISEASE_CLASSES[cid]
        detections.append({
            "detection_id": i+1,
            "class_id": cid,
            "class_name": cls["name"],
            "label": cls["label"],
            "confidence": round(conf,4),
            "confidence_pct": f"{conf:.1%}",
            "severity": cls["severity"],
            "color": cls["hex"],
            "icon": cls["icon"],
            "treatment": TREATMENT[cls["name"]],
            "bbox": {"x1":int(x1*W),"y1":int(y1*H),"x2":int(x2*W),"y2":int(y2*H)},
        })
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    return detections

def _iou(a, b):
    """Compute IoU between two boxes [x1,y1,x2,y2]."""
    ix1 = max(a[0], b[0]); iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2]); iy2 = min(a[3], b[3])
    inter = max(0, ix2-ix1) * max(0, iy2-iy1)
    if inter == 0: return 0.0
    area_a = (a[2]-a[0]) * (a[3]-a[1])
    area_b = (b[2]-b[0]) * (b[3]-b[1])
    return inter / (area_a + area_b - inter)

def yolo_detect(img: Image.Image) -> list:
    # Let YOLO handle the resizing natively. Use imgsz=640 (standard) to prevent macro shots from becoming too large for the model's receptive field.
    results = MODEL.predict(source=img, conf=0.20, iou=0.45, imgsz=640, agnostic_nms=True, verbose=False)

    raw = []
    for box in results[0].boxes:
        cid  = int(box.cls[0])
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].cpu().numpy().tolist()
        raw.append({"cid": cid, "conf": conf, "xyxy": xyxy})

    # Manual NMS: remove boxes that overlap > 40% with a higher-confidence box
    raw.sort(key=lambda x: x["conf"], reverse=True)
    kept = []
    for r in raw:
        duplicate = False
        for k in kept:
            if _iou(r["xyxy"], k["xyxy"]) > 0.40:
                duplicate = True
                break
        if not duplicate:
            kept.append(r)

    detections = []
    for i, r in enumerate(kept):
        cid  = r["cid"]
        conf = r["conf"]
        xyxy = r["xyxy"]
        cls  = DISEASE_CLASSES.get(cid, {"name":"unknown","label":"Unknown","hex":"#888","severity":"?","icon":"⚪"})
        detections.append({
            "detection_id": i+1,
            "class_id": cid,
            "class_name": cls.get("name","unknown"),
            "label": cls.get("label","Unknown"),
            "confidence": round(conf,4),
            "confidence_pct": f"{conf:.1%}",
            "severity": cls.get("severity","?"),
            "color": cls.get("hex","#888"),
            "icon": cls.get("icon","⚪"),
            "cause": cls.get("cause", "Penyebab belum diketahui."),
            "treatment": TREATMENT.get(cls.get("name",""), "Konsultasikan dengan ahli pertanian."),
            "bbox": {"x1":int(xyxy[0]),"y1":int(xyxy[1]),"x2":int(xyxy[2]),"y2":int(xyxy[3])},
        })
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    return detections


def build_summary(detections):
    disease = [d for d in detections if d["class_name"] != "healthy"]
    
    # Jika tidak ada deteksi sama sekali, asumsikan tidak ada penyakit (kemungkinan besar daun sehat yang tidak di-tag oleh model)
    if not detections:
        return {"status":"sehat","urgency":"low","message":"✅ Tidak ada penyakit terdeteksi.","recommendation":"Tanaman terlihat sehat atau objek terlalu jauh. Pertahankan perawatan rutin.","disease_count":0,"diseases_found":[]}
        
    if not disease:
        return {"status":"sehat","urgency":"low","message":"✅ Tanaman SEHAT. Tidak ada penyakit terdeteksi.","recommendation":"Lanjutkan perawatan rutin dan pantau berkala.","disease_count":0,"diseases_found":[]}
    names = [d["label"] for d in disease]
    has_critical = any(d["class_name"]=="virus_kuning" for d in disease)
    if has_critical:
        return {"status":"kritis","urgency":"critical","message":f"🔴 KRITIS! Terdeteksi {len(names)} masalah: {', '.join(names)}.","recommendation":"Segera tindak lanjut! Virus kuning dapat menyebar ke seluruh kebun melalui kutu kebul.","disease_count":len(disease),"diseases_found":names}
    if len(disease)>=2:
        return {"status":"berat","urgency":"high","message":f"🟠 Terdeteksi {len(names)} penyakit: {', '.join(names)}.","recommendation":"Segera konsultasikan dengan penyuluh pertanian.","disease_count":len(disease),"diseases_found":names}
    return {"status":"ringan","urgency":"medium","message":f"🟡 Terdeteksi: {', '.join(names)}.","recommendation":"Lakukan pengobatan sesuai rekomendasi untuk mencegah penyebaran.","disease_count":len(disease),"diseases_found":names}


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deteksi')
def deteksi():
    return render_template('deteksi.html', model_mode=MODEL_MODE)

@app.route('/about')
def about():
    return render_template('about.html')

# --- DATA ARTIKEL ---
ARTICLES = {
    "1": {
        "title": "Mengenal 5 Penyakit Utama Tanaman Cabai & Cara Penanganannya",
        "category": "Penyakit Cabai",
        "date": "24 Agu 2026",
        "image": "/static/img/article_anthracnose.png",
        "source": "https://id.wikipedia.org/wiki/Cabai#Hama_dan_penyakit",
        "summary": "Panduan lengkap mengenali gejala Bercak Daun, Daun Keriting, Kutu Kebul, Virus Kuning, dan Bercak Daun beserta rekomendasi penanganannya.",
        "content": """
        <p>Tanaman cabai (<em>Capsicum annuum L.</em>) sangat rentan terhadap berbagai serangan hama dan patogen penyakit. Mengenali gejala sejak dini adalah kunci utama untuk mencegah kegagalan panen. Berikut adalah 5 penyakit utama yang terdeteksi oleh sistem CHIFIA:</p>

        <h3>1. Bercak Daun (Cercospora capsici)</h3>
        <p>Disebabkan oleh jamur <em>Cercospora capsici</em>. Gejala ditandai dengan munculnya bercak-bercak bulat berwarna coklat tua dengan bagian tengah berwarna abu-abu pada permukaan daun. Pada tingkat parah, daun menguning dan gugur secara prematur.</p>

        <h3>2. Daun Keriting (Pepper Yellow Leaf Curl Virus)</h3>
        <p>Disebabkan oleh infeksi virus yang membuat helai daun mengecil, menggulung ke atas (keriting), dan tekstur daun kaku. Ditularkan oleh serangga vektor seperti thrips dan kutu daun (aphid).</p>

        <h3>3. Kutu Kebul (Bemisia tabaci)</h3>
        <p>Serangan hama serangga kecil berwarna putih yang menghisap cairan sel daun. Kutu kebul mengeluarkan embun madu yang memicu pertumbuhan jamur jelaga hitam dan merupakan pembawa utama (vektor) Begomovirus.</p>

        <h3>4. Virus Kuning (Begomovirus)</h3>
        <p>Infeksi virus paling berbahaya yang ditularkan oleh kutu kebul. Daun mengalami chlorosis (menguning total), tulang daun memucat, dan pertumbuhan tanaman terhenti (kerdik) tanpa menghasilkan buah.</p>

        <h3>5. Bercak Daun / Patek (Colletotrichum spp.)</h3>
        <p>Infeksi jamur pada buah dan daun cabai yang menyebabkan bercak lesi melingkar nekrotik melekuk ke dalam berwarna coklat kehitaman. Sangat cepat menyebar saat musim hujan dengan kelembaban tinggi.</p>

        <h3>Langkah Pencegahan Umum</h3>
        <ul>
            <li>Lakukan sanitasi lahan dan pemusnahan tanaman terinfeksi segera.</li>
            <li>Gunakan mulsa plastik hitam perak (MPHP) dan atur jarak tanam ideal.</li>
            <li>Manfaatkan aplikasi <strong>CHIFIA</strong> untuk deteksi dini secara otomatis melalui foto daun.</li>
        </ul>
        """
    },
    "2": {
        "title": "Aplikasi CHIFIA: Solusi Cerdas Deteksi Penyakit Cabai Berbasis AI",
        "category": "Aplikasi CHIFIA",
        "date": "20 Agu 2026",
        "image": "/static/img/hero_illustration.png",
        "source": "https://id.wikipedia.org/wiki/Kutu_kebul",
        "summary": "Bagaimana aplikasi web CHIFIA membantu petani mendeteksi penyakit cabai secara instan hanya dengan mengambil foto dari kamera smartphone.",
        "content": """
        <p><strong>CHIFIA</strong> (<em>Chili Intelligent Farming with AI</em>) adalah aplikasi kecerdasan buatan terpadu yang dirancang khusus untuk memodernisasi sektor pertanian cabai di Indonesia. Aplikasi ini memungkinkan petani, penyuluh, dan hobiis tanaman untuk melakukan diagnosis penyakit tanaman cabai secara cepat dan presisi.</p>

        <h3>Fitur Utama Aplikasi CHIFIA</h3>
        <ul>
            <li><strong>Ambil Foto Kamera Langsung:</strong> Petani dapat mengambil gambar daun cabai yang sakit secara langsung dari kamera smartphone di area kebun.</li>
            <li><strong>Unggah Gambar dari Galeri:</strong> Mendukung pengunggahan foto berformat JPG/PNG hingga ukuran 16MB.</li>
            <li><strong>Deteksi Multi-Klasifikasi Real-Time:</strong> Sistem AI menganalisis gambar dalam hitungan detik dan menampilkan kotak penanda (bounding box) pada area daun yang terinfeksi.</li>
            <li><strong>Indikator Tingkat Keparahan & Keyakinan:</strong> Menyajikan persentase tingkat keyakinan AI (confidence score) beserta status tingkat keparahan (Ringan, Sedang, Berat, atau Sehat).</li>
            <li><strong>Rekomendasi Penanganan Presisi:</strong> Memberikan panduan langkah pengobatan yang tepat sesuai dengan jenis penyakit yang terdeteksi (seperti penggunaan fungisida, sanitasi lahan, atau pemusnahan tanaman).</li>
        </ul>

        <h3>Cara Menggunakan Aplikasi</h3>
        <ol>
            <li>Buka menu <strong>Mulai Deteksi</strong> pada navigasi utama CHIFIA.</li>
            <li>Pilih mode pengambilan foto kamera atau unggah file dari galeri perangkat.</li>
            <li>Klik tombol <strong>Analisis Gambar</strong> dan tunggu sistem AI memproses.</li>
            <li>Lihat hasil prediksi visual beserta petunjuk penanganan di layar Anda.</li>
        </ol>
        """
    },
    "3": {
        "title": "Peran Model Deep Learning YOLOv26 dalam Deteksi Objek Real-Time",
        "category": "Model AI YOLOv26",
        "date": "15 Agu 2026",
        "image": "/static/img/article_ai.png",
        "source": "https://github.com/ultralytics/ultralytics",
        "summary": "Memahami arsitektur jaringan saraf YOLOv26 (You Only Look Once) dan keunggulannya dalam mengenali lesi penyakit tanaman secara instan.",
        "content": """
        <p>Dalam pengembangan aplikasi CHIFIA, arsitektur model kecerdasan buatan yang digunakan adalah <strong>YOLOv26 (You Only Look Once)</strong>. Berbeda dari arsitektur klasifikasi gambar tradisional, YOLOv26 adalah model <em>single-stage object detector</em> yang sangat efisien dan akurat.</p>

        <h3>Keunggulan Arsitektur Model YOLOv26</h3>
        <p>Model YOLOv26 membagi gambar input menjadi grid dan secara bersamaan memprediksi bounding box (lokasi lesi) serta probabilitas kelas (jenis penyakit) dalam satu lintasan komputasi (single pass). Keunggulannya meliputi:</p>
        <ul>
            <li><strong>Kecepatan Inferensi Sangat Tinggi:</strong> Mampu memproses gambar hanya dalam &lt; 30 milidetik per frame, memungkinkan deteksi real-time.</li>
            <li><strong>Deteksi Lokasi Presisi:</strong> Tidak hanya menebak jenis penyakit, tetapi menunjukkan lokasi persis daun yang sakit di dalam foto.</li>
            <li><strong>Multi-Object Detection:</strong> Mampu mengenali beberapa daun atau beberapa gejala penyakit sekaligus dalam satu foto.</li>
            <li><strong>Model Ringan (Edge-Friendly):</strong> Ukuran bobot model (file <code>best.pt</code>) yang teroptimasi memungkinkan eksekusi di server web maupun perangkat edge tanpa latency tinggi.</li>
        </ul>

        <h3>Implementasi pada CHIFIA</h3>
        <p>Model YOLOv26 pada CHIFIA telah dilatih menggunakan ribuan citra daun cabai yang terlabeli secara presisi. Melalui arsitektur Convolutional Neural Network (CNN) dengan feature pyramid networks (FPN), model mampu membedakan tekstur lesi yang sangat mirip di lapangan.</p>
        """
    },
    "4": {
        "title": "Cara Mengoptimalkan Akurasi Model AI Deteksi Penyakit Cabai",
        "category": "Optimasi AI",
        "date": "10 Agu 2026",
        "image": "/static/img/article_optimize.png",
        "source": "https://docs.ultralytics.com",
        "summary": "Teknik data augmentation, fine-tuning dataset lokal, dan penyesuaian threshold confidence untuk meningkatkan presisi AI hingga di atas 95%.",
        "content": """
        <p>Mencapai akurasi deteksi di atas 95% pada kondisi lapangan nyata memerlukan strategi optimasi model AI yang tepat. Berikut adalah teknik-teknik utama yang diterapkan pada pengembangan model CHIFIA:</p>

        <h3>1. Data Augmentation Beragam</h3>
        <p>Untuk melatih model agar tahan terhadap variasi pencahayaan dan sudut kamera di kebun, dataset diperkaya dengan augmentasi:</p>
        <ul>
            <li>Rotasi acak (0-360°) dan Horizontal/Vertical Flip.</li>
            <li>HSV Jittering (penyesuaian Hue, Saturation, dan Value pencahayaan).</li>
            <li>Mosaic Augmentation (menggabungkan 4 gambar berbeda menjadi satu).</li>
        </ul>

        <h3>2. Fine-Tuning pada Dataset Varietas Lokal</h3>
        <p>Model dasar (pre-trained weights) di-fine tune menggunakan dataset khusus tanaman cabai lokal Indonesia (seperti cabai rawit, cabai merah keriting, dan cabai besar) pada berbagai kondisi cuaca.</p>

        <h3>3. Penyesuaian Anchor Boxes & Non-Maximum Suppression (NMS)</h3>
        <p>Menyesuaikan skala anchor boxes dengan ukuran lesi bintik daun yang kecil, serta mengoptimalkan threshold IoU (Intersection over Union) dan confidence score untuk menekan angka false positive.</p>

        <p>Hasil dari pipeline optimasi ini menghasilkan model berakurasi 95%+ yang handal mengenali penyakit tanaman cabai secara konsisten.</p>
        """
    }
}

@app.route('/artikel/<id>')
def baca_artikel(id):
    if id in ARTICLES:
        return render_template('artikel.html', artikel=ARTICLES[id])
    return "Artikel tidak ditemukan", 404

@app.route('/detect', methods=['POST'])
def detect():
    try:
        image_bytes = None
        if 'file' in request.files and request.files['file'].filename:
            image_bytes = request.files['file'].read()
        elif request.is_json:
            data = request.get_json()
            if data and 'image' in data:
                b64 = data['image']
                if ',' in b64: b64 = b64.split(',')[1]
                image_bytes = base64.b64decode(b64)
        if not image_bytes:
            return jsonify({"error": "No image provided"}), 400

        img = read_image(image_bytes)
        detections = yolo_detect(img) if MODEL_MODE == "yolo" else demo_detect(img)
        annotated = draw_boxes(img, detections)
        summary = build_summary(detections)

        return jsonify({
            "success": True,
            "detections": detections,
            "annotated_image": pil_to_b64(annotated),
            "summary": summary,
            "mode": MODEL_MODE,
            "total": len(detections),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/model-status')
def model_status():
    return jsonify({"mode": MODEL_MODE, "classes": list(DISEASE_CLASSES.values())})

if __name__ == '__main__':
    print("\n=== CHIFIA - Chili Intelligent Farming with AI ===")
    print(f"   Mode    : {MODEL_MODE.upper()}")
    print("   URL     : http://localhost:5000")
    print("=================================================\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
