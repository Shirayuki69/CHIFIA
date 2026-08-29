import os

files = [
    r"C:\xampp\htdocs\CHIFIA\templates\index.html",
    r"C:\xampp\htdocs\CHIFIA\templates\deteksi.html",
    r"C:\xampp\htdocs\CHIFIA\templates\about.html"
]

for f in files:
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Replace specific AI phrases to avoid replacing letters inside words
        replacements = {
            "Artificial Intelligence": "YOLOv26",
            "AI Disease Scanner": "YOLOv26 Disease Scanner",
            "Deteksi Penyakit AI": "Deteksi Penyakit YOLOv26",
            "Analisis AI": "Analisis YOLOv26",
            "Hasil AI": "Hasil YOLOv26",
            "Prediksi AI": "Prediksi YOLOv26",
            "Model AI": "Model YOLOv26",
            "berbasis AI": "berbasis YOLOv26",
            "teknologi AI": "teknologi YOLOv26",
            "AI Detection": "YOLOv26 Detection",
            "AI Disease Detector": "YOLOv26 Disease Detector",
            "deteksi penyakit AI": "deteksi penyakit YOLOv26"
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)

print("Replacement complete.")
