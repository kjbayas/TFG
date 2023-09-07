import os
import json
import random
import string
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, jsonify
from flaskext.mysql import MySQL
from flask_mail import Mail, Message
from config import Config 

app = Flask(__name__)
app.config.from_object(Config)  # Configura la aplicación con la configuración de Config
app.secret_key = '2023K4rol'
# Inicializa extensiones, como MySQL y Mail
mysql = MySQL()
mysql.init_app(app)

mail = Mail(app)


@app.route('/')
def inicio():
    conexion = mysql.connect()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM nodos")
    nodos = cursor.fetchall()

    cursor.execute("SELECT * FROM enlaces")
    enlaces = cursor.fetchall()
    nodos_json = json.dumps(nodos)
    enlaces_json = json.dumps(enlaces)
    # Imprime los valores de nodos y enlaces en la consola del servidor Flask
    print(nodos_json)
    print(enlaces_json)

    conexion.close()
    return render_template('sitio/index.html' , nodos=nodos_json, enlaces=enlaces_json)

# Añadimos estilos de forma general 
@app.route('/css/<archivocss>') 
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'),archivocss)

# Almacenar Imagenes  
@app.route('/img/<imagen>') 
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

# llamada a la web de books 
@app.route('/libros')
def libros():

    conexion=mysql.connect()  # Establecemos una conexion a la Base de datos
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros`")
    libros=cursor.fetchall()
    conexion.commit()
    print(libros)

    return render_template('sitio/libros.html', libros=libros)


@app.route('/nosotros')
def nosotros():

    id_rol = 0  # id_rol lo definimos 0 para que solo pueda visualizar karolbayas
    tiene_permiso = False  # Otros roles no tienen permiso para editar

    conexion = mysql.connect()  
    cursor = conexion.cursor()
    cursor.execute("SELECT id, title, place, str_to_date(start_event, '%Y-%m-%d %H:%i:%s'), str_to_date(end_event, '%Y-%m-%d %H:%i:%s') FROM events")
    calendar = cursor.fetchall()
    conexion.close()

    return render_template('sitio/nosotros.html', calendar=calendar, tiene_permiso=tiene_permiso)

# Insertar eventos en el calendario
@app.route("/insert", methods=["POST", "GET"])
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
    # Verificar si se ha iniciado sesión
    if 'login' not in session:
        return redirect('/admin/login')  # Redireccionar al formulario de inicio de sesión si no ha iniciado sesión
    # Verificar el rol del usuario actual
    id_rol = session['id_rol'] # Obtén el valor del rol del usuario actual desde tu sistema de autenticación

    if id_rol == 1:  # Si el usuario tiene el rol = 1 "admin"
        tiene_permiso = True  # Usuario administrador tiene permiso para editar
    else:
        tiene_permiso = False  # rol = 0 no tienen permiso para editar

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

    conexion=mysql.connect()  
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros`")
    libros=cursor.fetchall()
    conexion.commit()
    print(libros)

    mensaje_error = request.args.get('mensaje_error')
    
    return render_template('admin/libros.html', libros=libros,mensaje_error=mensaje_error)


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


@app.route('/admin/libros/guardar', methods=['POST'])
def admin_libros_guardar():

    if not 'login' in session:
        return redirect('/admin/login')

    _nombre = request.form['txtNombre']
    _url = request.form['txtURL']
    _archivo = request.files['txtImagen']
    _year = request.form['txtYear']
    _area_seleccionada = request.form['txtArea']
    _autor_nombre = request.form['txtAutorNombre']
    _autor_apellido = request.form['txtAutorApellido']

    # Verificar si algún campo está vacío
    if not _nombre or not _url or not _archivo or not _autor_nombre or not _autor_apellido:
        mensaje_error = 'Please fill in all the fields.'
        return redirect(url_for('admin_libros', mensaje_error=mensaje_error))

    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    if _archivo.filename != "":
        nuevoNombre = horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/" + nuevoNombre)

    # Verificar si el autor ya existe en la base de datos de autores
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
    sql = "INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`, `year`, `area_id`, `autor_id`) VALUES (NULL, %s, %s, %s, %s, %s, %s);"
    datos = (_nombre, nuevoNombre, _url, _year, _area_id, _autor_id)

    cursor.execute(sql, datos)
    conexion.commit()
    conexion.close()

    print(_nombre)
    print(_url)
    print(_archivo)
    return redirect('/admin/libros')

@app.route('/sitio/libros', methods=['GET'])
def sitio_libros():
    year = request.args.get('year')
    area = request.args.get('area')
    author = request.args.get('author')

    # Obtener la lista de autores
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, apellido FROM autores")
    autores = cursor.fetchall()  # Extraer los resultados antes de cerrar la conexión

    # Construir la consulta SQL basada en los parámetros
    sql = "SELECT * FROM libros WHERE 1=1"

    # Crear la consulta SQL base sin filtrar
    sql_base = "SELECT * FROM libros"
    # Agregar condiciones para filtrar por año, área y autor si se seleccionaron
    conditions = []
    params = []

    if year:
        conditions.append("year = %s")
        params.append(year)
    if area:
        conditions.append("area_id = (SELECT id FROM areas WHERE nombre = %s)")
        params.append(area)
    if author:
        # Utiliza el valor de author directamente como author_id
        author_id = author

        conditions.append("autor_id = %s")
        params.append(author_id)

    if conditions:
        sql += " AND " + " AND ".join(conditions)

    cursor.execute(sql, params)
    libros = cursor.fetchall()
    conexion.close()

    return render_template('sitio/libros.html', libros=libros, autores=autores)


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

    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("DELETE FROM libros WHERE id =%s",(_id))
    conexion.commit()
    
    return redirect('/admin/libros')

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