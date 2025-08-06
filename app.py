from flask import Flask, render_template, request, send_file
from generar_pdf import generar_pdf
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf_route():
    datos = request.json
    pdf_bytes = generar_pdf(datos)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='prepago_cybernova.pdf'
    )

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
