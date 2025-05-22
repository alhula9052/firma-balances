import streamlit as st
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import io
import os

# Tesseract path en entorno de nube
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

st.title("Firmador de Balances PDF 🖋️")

uploaded_pdf = st.file_uploader("Sube el archivo PDF del balance", type=["pdf"])
uploaded_signature = st.file_uploader("Sube la imagen de tu firma (fondo blanco)", type=["png", "jpg", "jpeg"])

x_offset = st.slider("Posición horizontal de la firma", min_value=0, max_value=500, value=220)
escala = st.slider("Escala de la firma", min_value=0.2, max_value=1.5, value=0.6)

if uploaded_pdf and uploaded_signature:
    if st.button("Firmar PDF"):
        with st.spinner("Procesando..."):

            # Convertir imagen a fondo transparente
            firma = Image.open(uploaded_signature).convert("RGBA")
            datas = firma.getdata()
            new_data = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            firma.putdata(new_data)

            firma = firma.resize((int(firma.width * escala), int(firma.height * escala)), Image.LANCZOS)
            firma_io = io.BytesIO()
            firma.save(firma_io, format="PNG")
            firma_io.seek(0)

            pdf_bytes = uploaded_pdf.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

                for j in range(len(ocr_data["text"]) - 1, -1, -1):
                    if "total" in ocr_data["text"][j].lower():
                        y = ocr_data["top"][j] + ocr_data["height"][j] + 40
                        x = x_offset

                        # Insertar imagen de firma en coordenadas
                        page.insert_image(
                            fitz.Rect(x, y, x + firma.width, y + firma.height),
                            stream=firma_io.getvalue(),
                            overlay=True
                        )
                        break

            pdf_output = io.BytesIO()
            doc.save(pdf_output)
            doc.close()

            st.success("✅ PDF firmado correctamente.")
            st.download_button("📥 Descargar PDF firmado", data=pdf_output.getvalue(), file_name="firmado.pdf")
