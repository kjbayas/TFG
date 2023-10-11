import os
import json
import random
import string
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, jsonify
from flask_babel import Babel #traduccion FALTA 
from flaskext.mysql import MySQL
from flask_mail import Mail, Message
from config import Config 
from flask_login import login_required
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.config.from_object(Config)  #Set up the application with the Config configuration.
app.secret_key = '2023K4rol'

# Initialize extensions, MySQL, Mail
mysql = MySQL()
mysql.init_app(app)
mail = Mail(app)
babel = Babel(app)

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/css/<archivocss>') # We add styles in a general way 
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'),archivocss)

@app.route('/img/<imagen>') # Store images  
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)
 
@app.route('/libros') # Make a call to the book website
def libros():
    conexion=mysql.connect()  
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros`")
    libros=cursor.fetchall()
    conexion.commit()
    return render_template('sitio/libros.html', libros=libros)


@app.route('/nosotros')
def nosotros():

    id_rol = 0  # id_rol we set the role id to 0 to allow only viewering
    tiene_permiso = False  # Other rol don't have permission to edit 
    conexion = mysql.connect()  
    cursor = conexion.cursor()
    cursor.execute("SELECT id, title, place, str_to_date(start_event, '%Y-%m-%d %H:%i:%s'), str_to_date(end_event, '%Y-%m-%d %H:%i:%s') FROM events")
    calendar = cursor.fetchall()
    conexion.close()

    return render_template('sitio/nosotros.html', calendar=calendar, tiene_permiso=tiene_permiso)

@app.route("/insert", methods=["POST", "GET"]) # Insert events in the calendar
def insert():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    msg = ''
    
    if request.method == 'POST':
        title = request.form['title']
        place = request.form['place']
        start = request.form['start']
        end = request.form['end']
        print(title)
        print(start)
        print(end)
        cursor.execute("INSERT INTO events (title, place, start_event, end_event) VALUES (%s, %s, %s, %s)", [title, place, start, end])
        conexion.commit()
        conexion.close()
        msg = 'success' 

    return jsonify(msg)

@app.route("/update", methods=["POST", "GET"])
def update():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    msg = ''
    
    if request.method == 'POST':
        title = request.form['title']
        place = request.form['place']
        start = request.form['start']
        end = request.form['end']
        id = request.form['id']
        cursor.execute("UPDATE events SET title=%s, place=%s, start_event=%s, end_event=%s WHERE id=%s", [title, place, start, end, id])
        conexion.commit()
        conexion.close()
        msg = 'success'
    
    return jsonify(msg)


@app.route("/ajax_delete", methods=["POST", "GET"])
def ajax_delete():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    msg = ''
    
    if request.method == 'POST':
        getid = request.form['id']
        print(getid)
        cursor.execute("DELETE FROM events WHERE id={0}".format(getid))
        conexion.commit()
        conexion.close()
        msg = 'success'
    
    return jsonify(msg)


@app.route('/admin/')
def admin_index():
    if not 'login' in session:
        return redirect('/admin/login')
    return render_template('admin/index.html')

@app.route('/admin/nosotros')
def admin_nosotros():
    
    if 'login' not in session: # Check if the session has been started
        return redirect('/admin/login')  
    
    id_rol = session['id_rol'] # Retrieve the role value of the current user

    if id_rol == 1:  # User with role =1 is an admin 
        tiene_permiso = True  
    else:
        tiene_permiso = False  

    conexion = mysql.connect() 
    cursor = conexion.cursor()
    cursor.execute("SELECT id, title, place, str_to_date(start_event, '%Y-%m-%d %H:%i:%s'), str_to_date(end_event, '%Y-%m-%d %H:%i:%s') FROM events")
    calendar = cursor.fetchall()
    conexion.close()

    return render_template('admin/nosotros.html', calendar=calendar, tiene_permiso=tiene_permiso)

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/libros')
def admin_libros():
    if not 'login' in session:
        return redirect('/admin/login')

    conexion = mysql.connect()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM `libros`") # We obtain the data of libros
    libros = cursor.fetchall()

    cursor.execute("SELECT id, nombre, apellido FROM autores") # We obtain the data of autores
    autores_data = cursor.fetchall()

    for libro in libros: # Check the relationship between libros and autores
        libro_id = libro[0]
        autor_id_libro = libro[6]
        autor_encontrado = False
        
        for autor_data in autores_data: # Iterate over the tuples in  autores_data to find the autor
            autor_id_data = autor_data[0]
            if autor_id_libro == autor_id_data:
                autor_encontrado = True
                break
        
        if not autor_encontrado: # Check if the author was found for the current book
            mensaje_error = f"Author not found for book ID: {libro_id}"
            return render_template('admin/libros.html', libros=libros, autores=autores_data, mensaje_error=mensaje_error)
        
    conexion.close()
    
    return render_template('admin/libros.html', libros=libros, autores=autores_data) # If all authors are correctly related, render the template


@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form['txtUsuario']
    password = request.form['txtPassword']

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM login WHERE username = %s AND password = %s", (username, password))
    login = cursor.fetchone()
    conexion.close()

    if login is not None:
        if login[5] == 0:  # Verificar si el registro ha sido admitido (registro_pendiente = 0)
            session['login'] = True
            session['username'] = login[1]
            session['id_rol'] = login[4]
            session['id'] = login[0]

            if session['id_rol'] == 0:
                return redirect('/admin')
            elif session['id_rol'] == 1:
                return redirect('/admin')
            else:
                return render_template('admin/login.html', mensaje='Access Denied: User not created.')
        else:
            return render_template('admin/login.html', mensaje='Waiting for confirmation.')
    else:
        return render_template('admin/login.html', mensaje='Access Denied, please verify your credentials.')


@app.route('/admin/registro', methods=['GET', 'POST'])
def admin_registro():
    if request.method == 'POST':
        # Formulario de registro
        username = request.form['txtUsuario']
        password = request.form['txtPassword']
        email = request.form['txtEmail']
        # Verificar si el nombre de usuario ya existe en la Base de Datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        query = "SELECT id FROM login WHERE username = %s"
        cursor.execute(query, (username,))
        existing_user = cursor.fetchone()

        if existing_user: # Usuario ya existe en la base de datos, salta error y cierra la conexion 
            conexion.close()
            return render_template('admin/registro.html', error='USERNAME not valid')

        # Guardar los datos en la base de datos
        query = "INSERT INTO login (username, password, email, registro_pendiente) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (username, password, email, 1))
        conexion.commit()
        conexion.close()

        return redirect('/admin/login')  # Registro OK Redirigir al inicio de sesión

    return render_template('admin/registro.html')


# Token para restablecer la contraseña
def generate_reset_token():
    token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
    return token

# Modifica la función de envío de correo para aceptar argumentos
def enviar_correo(destinatario, asunto, contenido):
    msg = Message(asunto, sender='karoltfg2023@gmail.com', recipients=[destinatario])
    msg.body = contenido

    # Intentar enviar el correo
    try:
        mail.send(msg)
        return True, None  # Correo enviado correctamente
    except Exception as e:
        # Manejar cualquier tipo de error que pueda ocurrir al enviarse el correo
        return False, str(e)  

# olvide_contrasena, llama a enviar_correo 
@app.route('/admin/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        token = generate_reset_token()  # Genera un token para restablecer la contraseña

        # Guardar el token en la base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO reset_tokens (email, token) VALUES (%s, %s)", (email, token))
        conexion.commit()
        conexion.close()

        # Intentar enviar el correo electrónico
        exito, error = enviar_correo(email, 'Password Reset ', f'Click on the link to reset your password: {url_for("restablecer_contrasena", token=token, _external=True)}')

        if exito:
            mensaje = "An email with instructions to reset your password has been sent."
            return render_template('admin/login.html', mensaje=mensaje)
        else:
            mensaje = f"An error occurred while sending the email. Please try again later. Error: {error}"
            return render_template('admin/olvide_contrasena.html', mensaje=mensaje)

    return render_template('admin/olvide_contrasena.html')


# Restablecer la contraseña
@app.route('/admin/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        
        # Verificar el token en la base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT email FROM reset_tokens WHERE token = %s", (token,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Actualizar la contraseña en la base de datos
            cursor.execute("UPDATE login SET password = %s WHERE email = %s", (nueva_contrasena, resultado[0]))
            conexion.commit()
            # Eliminar el token de la base de datos después de usarlo
            cursor.execute("DELETE FROM reset_tokens WHERE token = %s", (token,))
            conexion.commit()
            conexion.close()
            
            mensaje = "Password reset successful. You can now log in with your new password."
            return render_template('admin/login.html', mensaje=mensaje)
        else:
            mensaje = "The token is not valid. Please request another password reset."
            return render_template('admin/login.html', mensaje=mensaje)

    return render_template('admin/restablecer_contrasena.html', token=token)


@app.route('/admin/permisos', methods=['GET', 'POST'])
def admin_permisos():
    if request.method == 'POST':
        username = request.form['txtUsuario']
        password = request.form['txtPassword']
        email = request.form['txtEmail']
        id_rol = request.form['txtIdRol']  # Obtener el valor del campo txtIdRol
        registro_pendiente = request.form['registro_pendiente']

        # Guardar los datos en la base de datos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        query = "INSERT INTO login (username, password, email, id_rol, registro_pendiente) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (username, password, email, id_rol, registro_pendiente))
        conexion.commit()
        conexion.close()

    # Verificar el acceso basado en el username
    if 'username' in session and session['username'] == 'karolbayas':
        # Obtener todos los datos de la tabla de permisos
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM login")
        permisos = cursor.fetchall()
        conexion.close()

        return render_template('admin/permisos.html', permisos=permisos)

    # Redirigir a la página anterior si no se cumple el requisito
    return redirect(request.referrer or '/')

@app.route('/admin/permisos/editar', methods=['POST'])
def admin_permisos_editar():
    if not 'login' in session:
        return redirect('/admin/login')

    username = request.form['username']
    password = request.form['password']
    id_rol = request.form['id_rol']
    registro_pendiente = request.form['registro_pendiente']

    # Actualizar los campos en la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()
    query = "UPDATE login SET password = %s, id_rol = %s, registro_pendiente = %s WHERE username = %s"
    cursor.execute(query, (password, id_rol, registro_pendiente, username))
    conexion.commit()
    conexion.close()

    return redirect('/admin/permisos')



@app.route('/admin/permisos/eliminar/<int:id_permiso>', methods=['GET'])
def admin_permisos_eliminar(id_permiso):
    if not 'login' in session:
        return redirect('/admin/login')

    # Eliminar el permiso de la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()
    query = "DELETE FROM login WHERE id = %s"
    cursor.execute(query, (id_permiso,))
    conexion.commit()
    conexion.close()

    return redirect('/admin/permisos')

@app.route('/admin/permisos/aceptar/<int:id_permiso>', methods=['POST'])
def admin_permisos_aceptar(id_permiso):
    if not 'login' in session:
        return redirect('/admin/login')

    # Actualizar el valor de registro_pendiente a 0 en la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()
    query = "UPDATE login SET registro_pendiente = 0 WHERE id = %s"
    cursor.execute(query, (id_permiso,))
    conexion.commit()
    conexion.close()

    return redirect('/admin/permisos')

def guardar_archivo(archivo, carpeta_destino):
    if archivo.filename == '':
        return None  # Si no se seleccionó ningún archivo, devolver None
    
    # Verificar si el archivo es permitido (puedes definir tus propias extensiones permitidas)
    extension_permitida = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4']
    if '.' not in archivo.filename or archivo.filename.rsplit('.', 1)[1].lower() not in extension_permitida:
        return None  # Si la extensión del archivo no es válida, devolver None
    
    # Guardar el archivo en la carpeta de destino
    nombre_archivo = secure_filename(archivo.filename)
    ruta_guardado = os.path.join(carpeta_destino, nombre_archivo)
    print("Intentando guardar archivo en:", ruta_guardado)
    archivo.save(ruta_guardado)
    
    return nombre_archivo  # Devolver el nombre del archivo guardado


@app.route('/admin/libros/guardar', methods=['POST'])
def admin_libros_guardar():

    if not 'login' in session:
        return redirect('/admin/login')

    _nombre = request.form['txtNombre'].upper()
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']
    _year = request.form['txtYear']
    _area_seleccionada = request.form['txtArea']
    _autor_nombre = request.form['txtAutorNombre'].upper()
    _autor_apellido = request.form['txtAutorApellido'].upper()
    _descripcion = request.form['txtDescripcion']
    _video = request.files['txtVideo']
    _pdf = request.files['txtPDF']
    _imagen_secundaria = request.files['txtImagenSecundaria']

    _archivo = guardar_archivo(request.files['txtImagen'], 'templates/sitio/img/')
    _video = guardar_archivo(request.files['txtVideo'], 'static/archivos/videos/')
    _pdf = guardar_archivo(request.files['txtPDF'], 'static/archivos/pdf/')
    _imagen_secundaria = guardar_archivo(request.files['txtImagenSecundaria'], 'static/archivos/imagenes/')

    # Verificar si algún campo está vacío
    if not _nombre or not _url or not _archivo or not _autor_nombre or not _autor_apellido:
        mensaje_error = 'Please fill in all the fields.'
        return redirect(url_for('admin_libros', mensaje_error=mensaje_error))

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM autores WHERE nombre = %s AND apellido = %s", (_autor_nombre, _autor_apellido))
    autor_existente = cursor.fetchone()
    
    if autor_existente:
        _autor_id = autor_existente[0]  # Utilizar el ID del autor existente
    else:
        # Si el autor no existe, insertarlo en la base de datos de autores
        cursor.execute("INSERT INTO autores (nombre, apellido) VALUES (%s, %s)", (_autor_nombre, _autor_apellido))
        conexion.commit()
        _autor_id = cursor.lastrowid  # Obtener el ID del nuevo autor

    # Obtener el ID del área seleccionada
    cursor.execute("SELECT id FROM areas WHERE nombre = %s", (_area_seleccionada,))
    resultado_area = cursor.fetchone()
    
    if resultado_area:
        _area_id = resultado_area[0]  # Obtener el ID del área
    else:
        # Manejar el caso en el que no se encontró la categoría de ÁREA seleccionada
        conexion.close()
        return redirect(url_for('admin_libros', mensaje_error='Invalid area selected.'))

    # Continuar con la inserción del libro en la base de datos de libros, incluyendo el _autor_id y _area_id en la consulta SQL.
    sql = "INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`, `year`, `area_id`, `autor_id`, `descripcion`, `video`, `pdf`, `imagen_secundaria`) VALUES (NULL, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s);"
    datos = (_nombre, _archivo, _url, _year, _area_id, _autor_id,_descripcion, _video, _pdf, _imagen_secundaria)
    
    cursor.execute(sql, datos)
    conexion.commit()
    conexion.close()
    return redirect('/admin/libros')

@app.route('/sitio/libros', methods=['GET'])
def sitio_libros():
    year = request.args.get('year')
    area = request.args.get('area')
    author = request.args.get('author')

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, apellido FROM autores")
    autores = cursor.fetchall()  # Extraer los resultados antes de cerrar la conexión
    sql = "SELECT * FROM libros WHERE 1=1"     # Construye la consulta SQL que se basa en los parámetros
    conditions = [] # crea condiciones de filtrado
    params = []

    if author:
        author_id = author
        conditions.append("autor_id = %s")
        params.append(author_id)
    if year:
        conditions.append("year = %s")
        params.append(year)
    if area:
        conditions.append("area_id = (SELECT id FROM areas WHERE nombre = %s)")
        params.append(area)


    if conditions:
        sql += " AND " + " AND ".join(conditions)

    cursor.execute(sql, params)
    libros = cursor.fetchall()
    conexion.close()

    return render_template('sitio/libros.html', libros=libros, autores=autores)

@app.route('/admin/libros/<int:libro_id>/editar', methods=['GET'])
def editar_libro(libro_id):
    if not 'login' in session:
        return redirect('/admin/login')

    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Obtener los datos actuales del libro para prellenar el formulario de edición
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro = cursor.fetchone()

        # Obtener datos de áreas desde la base de datos
    cursor.execute("SELECT * FROM areas")
    areas_data = cursor.fetchall()


    # Si el libro no existe, mostrar un mensaje de error
    if not libro:
        conexion.close()
        return render_template('error.html', error_message='Libro no encontrado')

    # Obtener datos adicionales necesarios para el formulario (como lista de áreas, etc.)
    # Esto es necesario para llenar los campos de selección en el formulario de edición

    cursor.close()
    conexion.close()

    return render_template('admin/editar_libro.html', libro=libro, areas_data=areas_data)  # Pasa áreas u otros datos necesarios al formulario


@app.route('/admin/libros/<int:libro_id>/guardar', methods=['POST'])
def guardar_cambios_libro(libro_id):
    if not 'login' in session:
        return redirect('/admin/login')
    
    # Obtener los datos existentes del libro para comparar con los datos del formulario
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro_existente = cursor.fetchone()

    _nombre = request.form['txtNombre'].upper()
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen'] if 'txtImagen' in request.files else None
    _year = request.form['txtYear']
    _area_seleccionada = request.form['txtArea']
    _autor_nombre = request.form['txtAutorNombre'].upper()
    _autor_apellido = request.form['txtAutorApellido'].upper()
    _descripcion = request.form['txtDescripcion']
    _video = request.files['txtVideo'] if 'txtVideo' in request.files else None
    _pdf = request.files['txtPDF'] if 'txtPDF' in request.files else None
    _imagen_secundaria = request.files['txtImagenSecundaria'] if 'txtImagenSecundaria' in request.files else None

    # Validaciones y procesamiento de archivos, similar a admin_libros_guardar

    # Conectar a la base de datos
    conexion = mysql.connect()
    cursor = conexion.cursor()

    # Construir la consulta SQL
    sql = "UPDATE libros SET nombre=%s, url=%s, year=%s, descripcion=%s"
    datos = (_nombre, _url, _year, _descripcion)

    # Comprobar si los campos del formulario tienen valores no vacíos y actualizarlos si es necesario
    if _archivo:
        archivo_path = guardar_archivo(_archivo, 'templates/sitio/img/')
        sql += ", imagen=%s"
        datos += (archivo_path,)
    if _area_seleccionada:
        # Obtener el ID del área seleccionada
        cursor.execute("SELECT id FROM areas WHERE nombre = %s", (_area_seleccionada,))
        resultado_area = cursor.fetchone()
        if resultado_area:
            _area_id = resultado_area[0]  # Obtener el ID del área
            sql += ", area_id=%s"
            datos += (_area_id,)
        else:
            # Manejar el caso en el que no se encontró la categoría de ÁREA seleccionada
            conexion.close()
            return redirect('/admin/libros', mensaje_error='Invalid area selected.')
    if _video:
        video_path = guardar_archivo(_video, 'static/archivos/videos/')
        sql += ", video=%s"
        datos += (video_path,)

    if _pdf:
        pdf_path = guardar_archivo(_pdf, 'static/archivos/pdf/')
        sql += ", pdf=%s"
        datos += (pdf_path,)

    if _imagen_secundaria:
        imagen_secundaria_path = guardar_archivo(_imagen_secundaria, 'static/archivos/imagenes/')
        sql += ", imagen_secundaria=%s"
        datos += (imagen_secundaria_path,)
    # Obtener el ID del autor si ya existe en la base de datos
    cursor.execute("SELECT id FROM autores WHERE nombre = %s AND apellido = %s", (_autor_nombre, _autor_apellido))
    resultado_autor = cursor.fetchone()
    if resultado_autor:
        _autor_id = resultado_autor[0]  # Obtener el ID del autor
    else:
        # Si el autor no se encuentra en la base de datos, añadirlo
        cursor.execute("INSERT INTO autores (nombre, apellido) VALUES (%s, %s)", (_autor_nombre, _autor_apellido))
        conexion.commit()
        # Obtener el ID del autor recién añadido
        _autor_id = cursor.lastrowid

    # Ejecutar la consulta SQL con los datos actualizados
    sql += ", autor_id=%s WHERE id=%s"
    datos += (_autor_id, libro_id)
    cursor.execute(sql, datos)
    conexion.commit()
    conexion.close()

    return redirect('/admin/libros')





@app.route('/admin/libros/borrar', methods=['POST'])
def admin_libros_borrar():

    if not 'login' in session:
        return redirect('/admin/login')
    
    _id=request.form['txtID']
    print(_id)
    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros` WHERE id =%s",(_id))
    libro=cursor.fetchall()
    conexion.commit()
    print(libro)
    cursor.execute("DELETE FROM comentarios WHERE libro_id = %s", (_id,))
    conexion.commit()
    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("DELETE FROM libros WHERE id =%s",(_id))
    conexion.commit()
    
    return redirect('/admin/libros')

@app.route('/sitio/admin/libros/<int:libro_id>', methods=['GET'])
@app.route('/admin/libros/<int:libro_id>', methods=['GET'])
@app.route('/sitio/admin/libros.html/<int:libro_id>', methods=['GET', 'POST'])
def ver_libro(libro_id):
    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM libros WHERE id = %s", (libro_id,))
    libro = cursor.fetchone()
    cursor.execute("SELECT id, nombre, apellido FROM autores WHERE id = %s", (libro[6],))
    autores_data = cursor.fetchall()
    cursor.execute("SELECT comentarios.id, comentarios.comentario, login.username, comentarios.user_id FROM comentarios INNER JOIN login ON comentarios.user_id = login.id WHERE comentarios.libro_id = %s", (libro_id,))
    comentarios = cursor.fetchall()
    cursor.close()
    if not libro:
        return render_template('error.html', error_message='Libro no encontrado')
    return render_template('detalle_libro.html', libro=libro, autores=autores_data, comentarios=comentarios)


@app.route('/admin/libros/<int:libro_id>/comentarios', methods=['POST'])
def agregar_comentario(libro_id):
    print("Recibida solicitud POST para agregar comentario.")
    comentario = request.form['comentario']
    user_id = session.get('id')  
    print("Comentario:", comentario)
    print("User ID:", user_id)
    # Verificar si user_id es None (no hay usuario en la sesión)
    if user_id is None:
        # Redirigir al usuario a la página de inicio de sesión o mostrar un mensaje de error
        return render_template('error.html', error_message='Debes iniciar sesión para comentar', back_url=request.referrer or '/')
    
    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("INSERT INTO comentarios (libro_id, comentario, user_id) VALUES (%s, %s, %s)", (libro_id, comentario, user_id))
    conexion.commit()
    conexion.close()    
    return redirect('/admin/libros/' + str(libro_id))
    return redirect(request.referrer)

@app.route('/admin/libros/comentarios/<int:comentario_id>/eliminar', methods=['POST', 'DELETE'])
def eliminar_comentario(comentario_id):
    user_id = session.get('id')
    if user_id is None:
        # Redirigir al usuario a la página de inicio de sesión o mostrar un mensaje de error
        return render_template('error.html', error_message='Debes iniciar sesión para eliminar comentarios', back_url=request.referrer or '/')
    if request.method in ['POST', 'DELETE']:
        try:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM comentarios WHERE id = %s", (comentario_id,))
            conexion.commit()
            return redirect(request.referrer)
        except Exception as e:
            print("Error al eliminar comentario:", e)
            return render_template('error.html', error_message='Error al eliminar comentario', back_url=request.referrer or '/')

@app.route('/favicon.ico')
def favicon():
    return '', 204
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

if not app.debug:
    handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')