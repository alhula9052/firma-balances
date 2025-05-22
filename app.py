import streamlit as st
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import io
import os

# Configuración para entorno en la nube
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

st.title("Firmador de Balances PDF 🖋️")

uploaded_pdf = st.file_uploader("Sube el archivo PDF del balance", type=["pdf"])
uploaded_signature = st.file_uploader("Sube la imagen de tu firma (fondo blanco)", type=["png", "jpg", "jpeg"])

x_offset = st.slider("Posición horizontal de la firma", min_value=0, max_value=500, value=220)
escala = st.slider("Escala de la firma", min_value=0.2, max_value=1.5, value=0.6)

if uploaded_pdf and uploaded_signature:
    if st.button("Firmar PDF"):
        with st.spinner("Procesando..."):
            firma_original = Image.open(uploaded_signature).convert("RGBA")

            # Quitar fondo blanco
            datas = firma_original.getdata()
            new_data = []
            for item in datas:
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            firma_original.putdata(new_data)

            firma = firma_original.resize(
                (int(firma_original.width * escala), int(firma_original.height * escala)), Image.LANCZOS
            )
            firma_w, firma_h = firma.size

            pdf_bytes = uploaded_pdf.read()
            pages = convert_from_bytes(pdf_bytes)
            firmadas = []

            for page in pages:
                page = page.convert("RGBA")
                ocr_data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
                page_rgb = page.copy()

                for j in range(len(ocr_data["text"]) - 1, -1, -1):
                    if "total" in ocr_data["text"][j].lower():
                        y = ocr_data["top"][j] + ocr_data["height"][j] + 40
                        x = x_offset
                        page.alpha_composite(firma, (x, min(y, page.height - firma_h - 10)))
                        page_rgb = page.convert("RGB")
                        break

                firmadas.append(page_rgb)

            temp_output = io.BytesIO()
            firmadas[0].save(temp_output, save_all=True, append_images=firmadas[1:], format="PDF", resolution=100.0)
            st.success("✅ PDF firmado correctamente.")
            st.download_button("📥 Descargar PDF firmado", data=temp_output.getvalue(), file_name="firmado.pdf")
