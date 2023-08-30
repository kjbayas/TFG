import os # Nos permite enviar información
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, jsonify
from flaskext.mysql import MySQL
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import json
import random
import string
import logging
from logging.handlers import RotatingFileHandler



app=Flask(__name__)
app.secret_key= os.urandom(24)
mysql=MySQL()
app.static_folder = 'static'
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587  # Puerto para TLS
app.config['MAIL_USE_TLS'] = True  # Usar TLS
app.config['MAIL_USERNAME'] = 'karolbayas@gmail.com'
app.config['MAIL_PASSWORD'] = '123'

mail = Mail(app)


#app.config['MYSQL_DATABASE_HOST']='10.22.2.63'
app.config['MYSQL_DATABASE_HOST']='192.168.1.17'
app.config['MYSQL_DATABASE_USER']='karolbayas'
app.config['MYSQL_DATABASE_PASSWORD']='urjc2023'
app.config['MYSQL_DATABASE_DB']='sitio'

mysql.init_app(app)



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
                return render_template('admin/login.html', mensaje='Acceso Denegado usuario no creado')
        else:
            return render_template('admin/login.html', mensaje='Esperando confirmación')
    else:
        return render_template('admin/login.html', mensaje='Acceso Denegado verifica credenciales')


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


@app.route('/admin/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        token = generate_reset_token()  # Generar un token seguro para restablecer la contraseña

        # Guardar el token en la base de datos (puedes usar la misma base de datos o una tabla diferente)
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO reset_tokens (email, token) VALUES (%s, %s)", (email, token))
        conexion.commit()
        conexion.close()

        # Crear y enviar el correo electrónico
        enlace_para_resetear_contrasena = url_for('restablecer_contrasena', token=token, _external=True)
        msg = Message('Restablecimiento de contraseña', sender='karolbayas@gmail.com', recipients=[email])
        msg.body = f'Haz clic en el enlace para restablecer tu contraseña: {enlace_para_resetear_contrasena}'

    try:
        mail.send(msg)
        mensaje = "Se ha enviado un correo con instrucciones para restablecer la contraseña."
        return render_template('/admin/login.html', mensaje=mensaje)
    except Exception as e:
        mensaje = "Ha ocurrido un error al enviar el correo. Por favor, inténtalo más tarde."
        return render_template('/admin/olvide_contrasena.html', mensaje=mensaje)


# Ruta para restablecer la contraseña
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
            # Actualizar la contraseña en la base de datos (puedes usar la misma tabla de usuarios)
            cursor.execute("UPDATE usuarios SET password = %s WHERE email = %s", (nueva_contrasena, resultado[0]))
            conexion.commit()
            # Eliminar el token de la base de datos después de usarlo
            cursor.execute("DELETE FROM reset_tokens WHERE token = %s", (token,))
            conexion.commit()
            conexion.close()
            
            mensaje = "Contraseña restablecida con éxito. Ahora puedes iniciar sesión con tu nueva contraseña."
            return render_template('/admin/login.html', mensaje=mensaje)
        else:
            mensaje = "El token no es válido. Por favor, solicita otro restablecimiento de contraseña."
            return render_template('/admin/login.html', mensaje=mensaje)

    return render_template('/admin/restablecer_contrasena.html', token=token)


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

    _nombre=request.form['txtNombre']
    _url=request.form['txtURL']
    _archivo=request.files['txtImagen']

    # Verificar si algún campo está vacío
    if not _nombre or not _url or not _archivo:
        mensaje_error = 'Por favor, rellene todos los campos.'
        return redirect(url_for('admin_libros', mensaje_error=mensaje_error))

    tiempo=datetime.now()
    horaActual=tiempo.strftime('%Y%H%M%S')
    if _archivo.filename!="":
        nuevoNombre=horaActual + "_" + _archivo.filename
        _archivo.save("templates/sitio/img/"+ nuevoNombre)

    sql="INSERT INTO `libros` (`id`, `nombre`, `imagen`, `url`) VALUES (NULL, %s, %s, %s);" 
    datos=(_nombre,nuevoNombre,_url)

    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute(sql,datos)
    conexion.commit()

    print(_nombre)
    print(_url)
    print(_archivo)
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