import os # Nos permite enviar información
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from flaskext.mysql import MySQL
from datetime import datetime


app=Flask(__name__)
app.secret_key= os.urandom(24)
mysql=MySQL()

app.config['MYSQL_DATABASE_HOST']='localhost'
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABASE_PASSWORD']=''
app.config['MYSQL_DATABASE_DB']='sitio'
#app.config['MYSQL_DATABASE_DB']='admin'
mysql.init_app(app)

@app.route('/')
def inicio():
    return render_template('sitio/index.html')

# Añadimos estilos 
@app.route('/css/<archivocss>') 
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'),archivocss)

# Esto es una carpeta donde se guardan las imagenes 
@app.route('/img/<imagen>') 
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

@app.route('/libros')
def libros():
    conexion=mysql.connect() #estamos conectadonos con la base de datos 
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros`")
    libros=cursor.fetchall()
    conexion.commit()
    print(libros)

    return render_template('sitio/libros.html', libros=libros)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')


@app.route('/admin/')
def admin_index():
    if not 'login' in session:
        return redirect('/admin/login')
    return render_template('admin/index.html')


@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/libros')
def admin_libros():

    if not 'login' in session:
        return redirect('/admin/login')

    conexion=mysql.connect() #estamos conectadonos con la base de datos 
    cursor= conexion.cursor()
    cursor.execute("SELECT * FROM `libros`")
    libros=cursor.fetchall()
    conexion.commit()
    print(libros)

    # Obtener el mensaje de error si existe
    mensaje_error = request.args.get('mensaje_error')
    
    return render_template('admin/libros.html', libros=libros,mensaje_error=mensaje_error)

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username=request.form['txtUsuario']
    password=request.form['txtPassword']

    conexion=mysql.connect()
    cursor =conexion.cursor()
    cursor.execute("SELECT * FROM login WHERE username =%s AND password =%s",(username, password))
    login=cursor.fetchone()
    conexion.close()
    print(login)

    if login is not None :
        session['login']=True
        session['username']=login[3]
        return redirect('/admin')
    else:
        return render_template('admin/login.html', mensaje='Acceso Denegado' )


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


if __name__ == '__main__':
    app.run(debug = True )