from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from psycopg2 import connect, sql
import os
import secrets
from datetime import datetime, timedelta
import ssl
import base64
import urllib3

# Para enviar correos con Flask-Mail
from flask_mail import Mail, Message

# Para enviar correos con SendGrid (alternativa)
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SGMail, Email, To, Content

# Para manejar MIME de correos
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

import smtplib

app = Flask(__name__, static_url_path='/static')

# Configuración de la aplicación
app.secret_key = 'tu_secreto_aqui'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# Carpeta donde se guardarán las imágenes
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Configuración de la aplicación
app.secret_key = 'tu_secreto_aqui'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

context = ssl._create_unverified_context()

# Función para obtener la conexión a la base de datos
def get_connection():
    return connect(host='localhost', port=5432, dbname='pit', user='postgres', password='tesis')

@app.route('/')
def home():
    return redirect('/login')

@app.route('/cambioPass')
def cambioPass():
    return render_template('cambioPass.html')

@app.route('/send_email', methods=['POST'])
def send_email():
    correo = request.form["correo"]

    # Conectar a PostgreSQL y verificar si el correo existe
    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("SELECT correo FROM personas WHERE correo = %s", (correo,))
        resultado = cursor.fetchone()

        if resultado is None:
            return jsonify({"success": False, "message": "El correo no está registrado."})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error en la base de datos: {str(e)}"})

    finally:
        cursor.close()
        conexion.close()

    # 📌 Generar un token seguro (puede ser guardado en la BD si quieres mayor seguridad)
    token = secrets.token_urlsafe(32)

    # Crear el enlace de recuperación con el token y el correo
    reset_link = f"http://127.0.0.1:5000/reset_password?email={correo}&token={token}"


    # Enviar el correo con el enlace
    asunto = "Solicitud de Cambio de Clave"
    mensaje = f"Hola,\n\nHaz clic en el siguiente enlace para restablecer tu clave:\n{reset_link}\n\nSi no solicitaste esto, ignora este mensaje."

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login("pjavila97@gmail.com", "jmbo bevd oata yiir")

        msg = MIMEMultipart()
        msg['From'] = "pjavila97@gmail.com"
        msg['To'] = correo
        msg['Subject'] = asunto

        cuerpo = MIMEText(mensaje, 'plain', 'utf-8')
        msg.attach(cuerpo)

        servidor.sendmail("pjavila97@gmail.com", correo, msg.as_string())
        servidor.quit()

        return jsonify({"success": True, "message": "Correo de recuperación enviado exitosamente."})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error al enviar el correo: {str(e)}"})
    
@app.route('/reset_password', methods=['GET'])
def reset_password():
    email = request.args.get("email")
    token = request.args.get("token")

    print(f'Email recibido en reset_password: {email}')
    print(f'Token recibido en reset_password: {token}')

    if not email:
        return "Solicitud inválida", 400

    return render_template("NuevaPass.html", email=email)

@app.route('/update_password', methods=['POST'])
def update_password():
    correo = request.form["correo"]
    nueva_contraseña = request.form["new_password"]
    confirmar_contraseña = request.form["confirm_password"]

    if nueva_contraseña != confirmar_contraseña:
        return "Las contraseñas no coinciden", 400

    # Hash de la nueva contraseña antes de guardarla
    nueva_contraseña_hash = generate_password_hash(nueva_contraseña)

    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        cursor.execute("UPDATE personas SET contraseña = %s  WHERE correo = %s", (nueva_contraseña_hash, correo))
        conexion.commit()
        print(f'Email recibido en reset_password: {correo}')


    except Exception as e:
        return f"Error en la base de datos: {str(e)}", 500

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("login"))  # Redirige al login después de cambiar la contraseña




@app.route('/cuenta')
def cuenta():
    return render_template('cuenta.html', user_email=session.get('user_email'), user_correo=session.get('correo'))

@app.route('/NuevaPass')
def nuevaPass():
    return render_template('NuevaPass.html')

@app.route('/index')
def principal():
    if 'nombre' not in session:
        return redirect(url_for('login2'))
    return render_template('index.html', nombre=session.get('nombre'), user_email=session.get('user_email'))

@app.route('/perfil')
def perfil():
    if 'idPersona' not in session:
        return redirect(url_for('login'))

    user_id = session['idPersona']
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nombre, apellido, direccion, correo FROM personas WHERE \"idPersona\" = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()

    if not user_data:
        return "Usuario no encontrado", 404

    return render_template('perfil.html', user=user_data, user_email=session.get('user_email'))

@app.route('/admindashboard')
def admDash():
    if 'nombre' not in session:
        return redirect(url_for('login2'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM personas p JOIN categoria c ON p.\"idCategoria\" = c.\"idCategoria\"")
        tickets = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admindashboard.html', tickets=tickets, user_email=session.get('user_email'))
    except Exception as e:
        return f"Error al obtener los datos: {str(e)}"

def obtener_persona(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personas WHERE \"idPersona\" = %s", (ticket_id,))
    persona = cursor.fetchone()
    cursor.close()
    conn.close()

    if persona:
        return {"nombre": persona[1], "apellido": persona[2], "telefono": persona[3], "direccion": persona[4], "correo": persona[5]}
    else:
        return {}

@app.route("/get_persona/<int:ticket_id>")
def get_persona(ticket_id):
    return jsonify(obtener_persona(ticket_id))



@app.route('/modificar_persona', methods=['POST'])
def modificar_persona():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE personas 
        SET nombre=%s, apellido=%s, telefono=%s, direccion=%s, correo=%s 
        WHERE "idPersona"=%s
    """, (data['nombre'], data['apellido'], data['telefono'], data['direccion'], data['correo'], data['id']))
    
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"mensaje": "Datos actualizados correctamente"})

from werkzeug.security import check_password_hash

@app.route('/login', methods=["POST"])
def login():
    correo = request.form.get('email')
    contraseña = request.form.get('password')  # Contraseña ingresada por el usuario

    if not correo or not contraseña:
        return jsonify({'error': 'Faltan campos'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener la contraseña hasheada desde la base de datos
        query = sql.SQL("SELECT \"idPersona\", nombre, correo, contraseña, \"idCategoria\" FROM personas WHERE correo = %s")
        cursor.execute(query, (correo,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            user_id, nombre, email, hash_guardado, categoria = user  # Extraer datos

            # Verificar la contraseña ingresada contra el hash almacenado
            if check_password_hash(hash_guardado, contraseña):
                session.permanent = True
                session['nombre'] = nombre
                session['user_email'] = categoria
                session['idPersona'] = user_id
                session['correo'] = email
                
                print(f'✅ Login exitoso: ID {categoria}')

                return render_template("index.html", nombre=nombre, correo=email, id=user_id, user_email=session.get('user_email'))
            else:
                return jsonify({'error': 'Credenciales incorrectas'}), 401
        else:
            return jsonify({'error': 'Credenciales incorrectas'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    except Exception as e:
        print(f"Error al actualizar las contraseñas: {str(e)}")



@app.route('/login')
def login2():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login2'))

@app.route('/tickets')
def ticket():
    if 'nombre' not in session:
        return redirect(url_for('login2'))
    return render_template('tickets.html', nombre=session.get('nombre'),user_email=session.get('user_email'))


@app.route('/creaTickets', methods=["GET", "POST"])
def creaTicket():
    if 'nombre' not in session:
        return redirect(url_for('login2'))

    if request.method == 'POST':
        detalle = request.form.get('detalle')
        descripcion = request.form.get('descripcion')
        fechaCreado = request.form.get('fechaCreado')
        prioridad = request.form.get('prioridad')
        user_id=session["idPersona"]
        imagen = request.files['imagen']

        # Guardar la imagen si se subió
        if imagen:
    # Abrimos la imagen en modo binario
          image_data = imagen.read()  # Leemos los datos binarios de la imagen
        else:
          image_data = None  # Si no hay imagen, asignamos None

       

       
       
        if not detalle or not descripcion or not fechaCreado:
            return jsonify({'error': 'Faltan campos'}), 400
        
         # Mapeo de prioridad a número
        prioridad_numerica = {
            "Alta": 1,
            "Media": 2,
            "Baja": 3
        }

        # Convertir la prioridad recibida en su número correspondiente, si no existe, asignar un valor por defecto
        id_prioridad = prioridad_numerica.get(prioridad, 3)  # Si no coincide, por defecto será "Baja" (3)

        

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT imagen FROM \"detalleTicket\"')
            tickets = cursor.fetchall()
            
            # Inserción del ticket
            
            query2 = sql.SQL("""INSERT INTO "detalleTicket" ("detalleTicket", descripcion, estado, imagen, "fechaCreado", "idPrioridad", "idPersona") 
                                VALUES (%s, %s,'Pendiente de Asignacion', %s, %s, %s, %s)""")
        
            cursor.execute(query2, (detalle, descripcion, image_data ,fechaCreado, id_prioridad, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            mensaje = 'Ticket creado exitosamente'
            return render_template('creaTickets.html', mensaje=mensaje,user_email=session.get('user_email'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('creaTickets.html')


@app.route("/contact")
def mostrarTecnicos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT \"idPersona\", nombre, apellido, correo, telefono FROM personas WHERE \"idCategoria\" = 1")
    personas = cursor.fetchall()
    cursor.close()
    
    return render_template("contact.html", personas=personas,user_email=session.get('user_email'))


@app.route('/detalle/<int:id>', methods=['GET'])
def detalle(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM personas WHERE \"idPersona\" = %s', (id,))
    persona = cur.fetchone()
    cur.close()
    conn.close()
    
    if persona:
        return jsonify({
            'id': persona[0],
            'nombre': persona[1],
            'apellido': persona[2],
            'telefono': persona[3],  # Si tienes más campos
            'email': persona[5]      # Si tienes más campos
        })
    else:
        return jsonify({'error': 'Persona no encontrada'}), 404

@app.route('/insertar_persona', methods=['POST'])
def insertar_persona():
    try:
        data = request.json
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        telefono = data.get('telefono')
        direccion = data.get('direccion')
        correo = data.get('correo')
        password = data.get('password')  # Contraseña sin cifrar
        categoria = data.get('categoria')

        if not all([nombre, apellido, telefono, direccion, correo, password, categoria]):
            return jsonify({'mensaje': 'Todos los campos son obligatorios'}), 400

        # Cifrar la contraseña antes de guardarla en la base de datos
        password_hash = generate_password_hash(password)

        # Mapeo de Categoria a Numero
        prioridad_numerica = {
            "tech": 1,
            "user": 2,
            "admin": 3
        }

        # Convertir la prioridad recibida en su número correspondiente
        id_categoria = prioridad_numerica.get(categoria, 2)  # Por defecto, "user" (2)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO personas (nombre, apellido, telefono, direccion, correo, contraseña, "idCategoria")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nombre, apellido, telefono, direccion, correo, password_hash, id_categoria))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'mensaje': 'Persona insertada correctamente'}), 201

    except Exception as e:
        return jsonify({'mensaje': f'Error al insertar persona: {str(e)}'}), 500

@app.route('/ticketAbierto')
def mostrar_tickets():
    if 'nombre' not in session:
        return redirect(url_for('login2'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        user_id=session.get('user_id')
        user_email=session.get('user_email')
        if user_email == 1 or user_email==3:
         cursor.execute("SELECT d.*, p.nombre AS nombre_solicitante, p.apellido AS apellido_solicitante, t_persona.nombre AS nombre_tecnico, t_persona.apellido AS apellido_tecnico FROM \"detalleTicket\" d JOIN personas p ON d.\"idPersona\" = p.\"idPersona\"LEFT JOIN tecnico t ON d.\"idTecnico\" = t.\"idTecnico\"LEFT JOIN personas t_persona ON t.\"idPersona\" = t_persona.\"idPersona\" WHERE d.estado = \'Abierto\'")
         tickets = cursor.fetchall()
         cursor.close()
         conn.close() 
            
        elif user_email == 2:
         cursor.execute("SELECT d.*, p.nombre AS nombre_solicitante, p.apellido AS apellido_solicitante, t_persona.nombre AS nombre_tecnico, t_persona.apellido AS apellido_tecnico FROM \"detalleTicket\" d JOIN personas p ON d.\"idPersona\" = p.\"idPersona\"LEFT JOIN tecnico t ON d.\"idTecnico\" = t.\"idTecnico\"LEFT JOIN personas t_persona ON t.\"idPersona\" = t_persona.\"idPersona\" WHERE d.estado = \'Abierto\' and p.\"idPersona\"=%s", (user_id,))
         tickets = cursor.fetchall()
         cursor.close()
         conn.close()          
        else:
                return jsonify({'error': 'Rol no reconocido'}), 401
        
        

        
        
        return render_template('ticketAbierto.html', tickets=tickets,user_email=session.get('user_email'))

    except Exception as e:
        return f"Error al obtener los tickets: {str(e)}"
    
@app.route('/obtener_imagen/<int:ticket_id>')
def obtener_imagen(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT imagen FROM "detalleTicket" WHERE "idDetalle" = %s', (ticket_id,))
    ticket = cursor.fetchone()

    cursor.close()
    conn.close()

    if ticket and ticket[0]:  # Si existe imagen
        # Convierte la imagen binaria a base64
        imagen_base64 = base64.b64encode(ticket[0]).decode('utf-8')
        print(imagen_base64[:1000])  # Verifica los primeros 50 caracteres de la imagen en base64 para asegurarte de que se convierte correctamente
        return jsonify({'imagen': imagen_base64})
    else:
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
  

    
@app.route('/contar_solicitudes')
def contar_solicitudes():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM \"detalleTicket\" where estado=\'Pendiente de Asignacion\'")  # Reemplaza 'solicitudes' con el nombre real de tu tabla
        cantidad = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"cantidad": cantidad})
    except Exception as e:
        return jsonify({"error": str(e)})
    
@app.route('/solicitudes')
def solicitudes():
    if 'nombre' not in session:
        return redirect(url_for('login2'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT d.*, p.nombre, p.apellido FROM \"detalleTicket\" d join personas p on d.\"idPersona\"=p.\"idPersona\" WHERE estado=\'Pendiente de Asignacion\'")
        tickets = cursor.fetchall()
        cursor.close()
        conn.close()
        

        
        return render_template('solicitudes.html', tickets=tickets,user_email=session.get('user_email'))

    except Exception as e:
        return f"Error al obtener los tickets: {str(e)}"

@app.route('/ticketCerrado')
def mostrar_tickets_cerrados():
    if 'nombre' not in session:
        return redirect(url_for('login2'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        user_id=session.get('user_id')
        user_email=session.get('user_email')
        if user_email == 1 or user_email==3:
         cursor.execute("SELECT d.*, p.nombre AS nombre_solicitante, p.apellido AS apellido_solicitante, t_persona.nombre AS nombre_tecnico, t_persona.apellido AS apellido_tecnico FROM \"detalleTicket\" d JOIN personas p ON d.\"idPersona\" = p.\"idPersona\"LEFT JOIN tecnico t ON d.\"idTecnico\" = t.\"idTecnico\"LEFT JOIN personas t_persona ON t.\"idPersona\" = t_persona.\"idPersona\" WHERE d.estado = \'Abierto\'")
         tickets = cursor.fetchall()
         cursor.close()
         conn.close() 
            
        elif user_email == 2:
         cursor.execute("SELECT d.*, p.nombre AS nombre_solicitante, p.apellido AS apellido_solicitante, t_persona.nombre AS nombre_tecnico, t_persona.apellido AS apellido_tecnico FROM \"detalleTicket\" d JOIN personas p ON d.\"idPersona\" = p.\"idPersona\"LEFT JOIN tecnico t ON d.\"idTecnico\" = t.\"idTecnico\"LEFT JOIN personas t_persona ON t.\"idPersona\" = t_persona.\"idPersona\" WHERE d.estado = \'Abierto\' and p.\"idPersona\"=%s", (user_id,))
         tickets = cursor.fetchall()
         cursor.close()
         conn.close()          
        else:
                return jsonify({'error': 'Rol no reconocido'}), 401
        
        return render_template('ticketCerrado.html', tickets=tickets,user_email=session.get('user_email'))

    except Exception as e:
        return f"Error al obtener los tickets: {str(e)}"
    
@app.route('/eliminar_persona/<int:id>', methods=['DELETE'])
def eliminar_persona(id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM personas WHERE \"idPersona\" = %s", (id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al eliminar usuario: {str(e)}"}), 500    
    
@app.route('/update_ticket_state', methods=["POST"])
def update_ticket_state():
    ticket_id = request.form['ticket_id']
    new_state = request.form['state']
    fechaCerrado = request.form.get('fecha_actual')

    # Si el estado es "Cerrado" y la fecha no se envió correctamente, usar la fecha actual
    if new_state == "Cerrado" and not fechaCerrado:
        fechaCerrado = datetime.today().strftime('%Y-%m-%d')

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Actualizar el estado del ticket en la base de datos
        query = sql.SQL("""
            UPDATE "detalleTicket" 
            SET estado = %s, "fechaCerrado" = %s 
            WHERE "idDetalle" = %s
        """)
        cursor.execute(query, (new_state, fechaCerrado, ticket_id))
        
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('mostrar_tickets'))  # Redirige a la página de tickets

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/update_password2', methods=['POST'])
def update_password2():
    # Obtener datos del formulario
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Verificar que las contraseñas nuevas coincidan
    if new_password != confirm_password:
        return jsonify({'error': 'Las contraseñas nuevas no coinciden'}), 400

    # Obtener el correo del usuario desde la sesión
    email = session.get('correo')

    if not email:
        return jsonify({'error': 'No se encontró el correo del usuario en la sesión'}), 400

    try:
        # Conectar a la base de datos
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener la contraseña almacenada en la base de datos usando el correo
        cursor.execute("SELECT contraseña FROM personas WHERE correo = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Verificar que la contraseña actual coincida con la almacenada
        stored_password_hash = user[0]

        if not check_password_hash(stored_password_hash, current_password):
            return jsonify({'error': 'La contraseña actual es incorrecta'}), 400

        # Hashear la nueva contraseña
        hashed_new_password = generate_password_hash(new_password)

        # Actualizar la contraseña en la base de datos
        cursor.execute("UPDATE personas SET contraseña = %s WHERE correo = %s", (hashed_new_password, email))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Contraseña actualizada correctamente'}), 200

    except Exception as e:
        return jsonify({'error': f'Error al actualizar la contraseña: {str(e)}'}), 500
    
@app.route('/update_ticket', methods=['POST'])
def update_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    user_id=session["idPersona"]

    print(f"Ticket ID: {user_id}")

    if not ticket_id:
        return jsonify({"message": "Error: ID del ticket no proporcionado"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
   
        cursor.execute("""SELECT t.\"idTecnico\" FROM personas p JOIN tecnico t ON p.\"idPersona\" = t.\"idPersona\" WHERE p.\"idPersona\" = %s""", (user_id,)) 

        result = cursor.fetchone()

      

        if result is not None:  # Verificar que hay un resultado
            id_tecnico = result  # Aquí asignamos directamente el valor entero
        else:
            return jsonify({"message": "Error: No se encontró un técnico asociado al usuario"}), 404


      
        
        

        # Actualizar estado del ticket a "Abierto"
        cursor.execute("""
                UPDATE "detalleTicket" 
                SET estado = %s, "idTecnico"=%s 
                WHERE "idDetalle" = %s
            """, ('Abierto',id_tecnico, ticket_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "El ticket ha sido creado exitosamente. "}), 200

    except Exception as e:
        return jsonify({"message": f"Error al actualizar el ticket: {str(e)}"}), 500
    
@app.route('/get_persons', methods=['GET'])
def get_persons():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT p.\"idPersona\", p.nombre, p.apellido, c.\"detalleCat\", t.\"idTecnico\" FROM personas p JOIN categoria c ON p.\"idCategoria\"  = c.\"idCategoria\" JOIN tecnico t on t.\"idPersona\"=p.\"idPersona\" WHERE c.\"detalleCat\" = 'Tecnico'")  
        
        rows = cursor.fetchall()
        print("Resultados de la consulta:", rows)  # ← Imprime los datos en consola

        persons = [{"id": row[4], "nombre": row[1], "apellido": row[2], "categoria": row[3]} for row in rows]  
        
        cursor.close()
        conn.close()
        return jsonify(persons)
    except Exception as e:
        print(f"Error en la consulta SQL: {e}")  # ← Muestra el error en consola
        return jsonify({"message": f"Error al obtener la lista de personas: {str(e)}"}), 500
    



@app.route('/assign_ticket', methods=['POST'])
def assign_ticket():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    person_id = data.get('person_id')  # Aquí recibimos el person_id
  


    print(f"Ticket ID: {ticket_id}, Person ID: {person_id}")  # Verifica que el person_id no sea undefined

    if not ticket_id or not person_id:
        return jsonify({"message": "Error: Faltan datos"}), 400

    try:
        # Verificar que la persona seleccionada es un técnico antes de asignarla al ticket
        conn = get_connection()
        cursor = conn.cursor()

        # Consultar la categoría de la persona seleccionada
        cursor.execute("SELECT c.\"detalleCat\" FROM tecnico t JOIN categoria c ON t.\"idCategoria\" = c.\"idCategoria\" WHERE t.\"idTecnico\" = %s", (person_id))

        categoria_result = cursor.fetchone()
        if categoria_result and categoria_result[0] == 'Tecnico':
            # Si la persona es un técnico, actualizar el ticket
            cursor.execute("""
                UPDATE "detalleTicket" 
                SET estado = %s, "idTecnico"=%s 
                WHERE "idDetalle" = %s
            """, ('Abierto',person_id, ticket_id))
            conn.commit()
            cursor.close()
            conn.close()

            # Mostrar los datos en la consola del servidor
            print(f'Ticket actualizado: ID del Ticket: {ticket_id}, ID de Persona Asignada: {person_id}, Estado: Abierto')

            return jsonify({
                "message": "El ticket ha sido asignado correctamente.",
                "ticket_id": ticket_id,
                "person_id": person_id,
                "estado": "Abierto"
            }), 200
        else:
            return jsonify({"message": "Error: La persona seleccionada no es un técnico."}), 400
    except Exception as e:
        print(f'Error al asignar el ticket: {str(e)}')  # Muestra el error en la consola del servidor
        return jsonify({"message": f"Error al asignar el ticket: {str(e)}"}), 500

    

if __name__ == '__main__':
    app.run(debug=True)
