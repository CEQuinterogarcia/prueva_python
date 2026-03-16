from flask import Flask, render_template, request, Response
from flaskext.mysql import MySQL
from datetime import datetime
from fpdf import FPDF   # libreria para exportar PDF
from PIL import Image
import os       
import io

app = Flask(__name__)

# Configuración de la base de datos
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '123456789'
app.config['MYSQL_DATABASE_DB'] = 'bd_trabajos'
mysql.init_app(app)

@app.route('/')
def index():
    
    return render_template('trabajos/index.html')

# se muestra el contenido de BD en la tabla
@app.route('/mostrar')
def mostrar():
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        sql = "SELECT * FROM trabajos;"
        cursor.execute(sql)
        trabajos = cursor.fetchall()
        #print(trabajos)

        conn.commit()
    except Exception as e:
        print("Error al mostrar:", e)
    finally:
        cursor.close()
        conn.close()

    return render_template('trabajos/mostrar.html', trabajos=trabajos)

# envia a la pagina crear
@app.route('/crear')
def crear():
    return render_template('trabajos/crear.html')

# se guarda el registro en la tabla
@app.route('/guardar', methods=['POST'])
def guardar():

    _tittrabajo = request.form['txtT_trabajo']
    _tiptrabajo = request.form['selTi_trabajo']
    _autor = request.form['txtAutor']
    _universidad = request.form['txtUniversidad']
    _pclave = request.form['txtP_clave']
    _resumen = request.form['txtResumen']
    _curso = request.form['selCurso']
    _imagen = request.files['filImagen']
    _pdf = request.files['filPdf']
    _ciudad = request.form['txtCiudad']
    _especialidad = request.form['selEspecialidad']
       

    now = datetime.now()
    tiempo = now.strftime("%Y%m%H%M%S")   

     # Leer contenido binario de la imagen
    imagen_blob = _imagen.read() if _imagen and _imagen.filename != '' else None
  
    # Guardar PDF en carpeta "pdf"
    import os
    PDF_FOLDER = 'static/pdf'
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)

 # creamos un nombre incluyendo fecha para PDF
    pdf_filename = None
    if _pdf and _pdf.filename != '':
        tiemaspdf= tiempo+_pdf.filename
        pdf_filename = os.path.join(PDF_FOLDER, tiemaspdf)
        _pdf.save(pdf_filename)

    # Guardamos solo el nombre del archivo en la BD
        pdf_filename = tiemaspdf   
    

    conn = mysql.connect()
    cursor = conn.cursor()
    
    
    try:
        sql = """INSERT INTO trabajos 
                 (titulo_trabajo, tipo_trabajo, autor, universidad, palabras_claves, resumen, curso, imagen, car_pdf, ciudad, especialidad) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        valores = (_tittrabajo, _tiptrabajo, _autor, _universidad, _pclave, _resumen, _curso, imagen_blob, pdf_filename, _ciudad, _especialidad)
        cursor.execute(sql, valores)
        conn.commit()
    except Exception as e:
        print("Error al Guardar:", e)
    finally:
        cursor.close()
        conn.close()
    return render_template('trabajos/index.html')

# mostrar imagen desde el archivo BD

@app.route('/imagen/<int:id>')
def mostrar_imagen(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT imagen FROM trabajos WHERE id_trabajos=%s", (id,))
        row = cursor.fetchone()
    except Exception as e:
        print("Error al mostrar imagen:", e)
        row = None
    finally:
        cursor.close()
        conn.close()

    if row and row[0]:
        return Response(row[0], mimetype='image/jpeg')  
    return "Imagen no encontrada"

# para exportar el PDF

@app.route('/exportar/<int:id_trabajos>')
def exportar_pdf(id_trabajos):
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """SELECT titulo_trabajo, tipo_trabajo, autor, curso, especialidad, ciudad, resumen, imagen 
                          FROM trabajos WHERE id_trabajos=%s"""
        cursor.execute(sql, (id_trabajos,))
        trabajo = cursor.fetchone()

        if not trabajo:
            return "Trabajo no encontrado"

        titulo, tipo, autor, curso, especialidad, ciudad, resumen, imagen_blob = trabajo

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt=f"Título: {titulo}", ln=True)
        pdf.cell(200, 10, txt=f"Tipo: {tipo}", ln=True)
        pdf.cell(200, 10, txt=f"Autor: {autor}", ln=True)
        pdf.cell(200, 10, txt=f"Curso: {curso}", ln=True)
        pdf.cell(200, 10, txt=f"Especialidad: {especialidad}", ln=True)
        pdf.cell(200, 10, txt=f"Ciudad: {ciudad}", ln=True)
        pdf.multi_cell(0, 10, txt=f"Resumen: {resumen}")

        # Insertar imagen si existe
        if imagen_blob:
            try:
                # Abrir imagen desde bytes con PIL
                img = Image.open(io.BytesIO(imagen_blob))
                img_format = img.format.lower()  # 'jpeg', 'png'
                img_path = f"temp_img.{img_format}"
                img.save(img_path)

                pdf.image(img_path, x=10, y=None, w=50)
                os.remove(img_path)
            except Exception as e:
                print("Error al procesar imagen con PIL:", e)


        nombre_pdf = f"trabajo_{id_trabajos}.pdf"
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        return Response(pdf_bytes, mimetype='application/pdf',
                        headers={"Content-Disposition": f"attachment;filename={nombre_pdf}"})

    except Exception as e:
        print("Error al generar PDF:", e)
        return "Error al generar PDF"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)