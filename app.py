from flask import Flask, render_template, request, redirect, url_for
from estructuras import ArbolBinarioBusqueda, ListaDoblementeLigada, busqueda_secuencial
import csv
import os
import time
from datetime import datetime

app = Flask(__name__)

db_pacientes = ArbolBinarioBusqueda()
historial_busquedas = ListaDoblementeLigada()

CSV_FILE = 'pacientes.csv'

def cargar_datos():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            pass
        return

    with open(CSV_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:
                try:
                    db_pacientes.insertar(int(row[0]), row[1], int(row[2]), row[3])
                except (ValueError, IndexError):
                    continue

def guardar_datos():
    lista = db_pacientes.obtener_en_orden()
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for p in lista:
            writer.writerow([p['id'], p['nombre'], p['edad'], p['diagnostico']])

cargar_datos()

@app.route('/')
def index():
    pacientes = db_pacientes.obtener_en_orden()
    historial = historial_busquedas.obtener_historial()
    
    estadisticas = {}
    for p in pacientes:
        estadisticas[p['diagnostico']] = estadisticas.get(p['diagnostico'], 0) + 1

    return render_template('index.html', pacientes=pacientes, historial=historial, estadisticas=estadisticas)

@app.route('/agregar', methods=['POST'])
def agregar():
    id_p = int(request.form['id'])
    nombre = request.form['nombre']
    edad = int(request.form['edad'])
    diagnostico = request.form['diagnostico']
    
    db_pacientes.insertar(id_p, nombre, edad, diagnostico)
    guardar_datos()
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id_p>')
def eliminar(id_p):
    db_pacientes.eliminar(id_p)
    guardar_datos()
    return redirect(url_for('index'))

@app.route('/buscar', methods=['POST'])
def buscar():
    id_buscado = int(request.form['id_busqueda'])
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    t_inicio_bst = time.perf_counter()
    resultado_bst = db_pacientes.buscar(id_buscado)
    t_fin_bst = time.perf_counter()
    tiempo_bst = (t_fin_bst - t_inicio_bst) * 1000
    
    lista_plana = db_pacientes.obtener_en_orden()
    t_inicio_seq = time.perf_counter()
    _ = busqueda_secuencial(lista_plana, id_buscado)
    t_fin_seq = time.perf_counter()
    tiempo_seq = (t_fin_seq - t_inicio_seq) * 1000
    
    if resultado_bst:
        status = f"Encontrado ({resultado_bst.nombre})"
    else:
        status = "No encontrado"
    
    historial_busquedas.insertar_inicio(fecha_actual, id_buscado, status)
    
    pacientes = db_pacientes.obtener_en_orden()
    historial = historial_busquedas.obtener_historial()
    
    estadisticas = {}
    for p in pacientes:
        estadisticas[p['diagnostico']] = estadisticas.get(p['diagnostico'], 0) + 1
        
    experimento = {
        "id": id_buscado,
        "tiempo_bst": f"{tiempo_bst:.6f} ms",
        "tiempo_seq": f"{tiempo_seq:.6f} ms",
        "eficiencia": f"{tiempo_seq / (tiempo_bst if tiempo_bst > 0 else 0.000001):.1f}x más rápido"
    }

    return render_template('index.html', pacientes=pacientes, historial=historial, estadisticas=estadisticas, experimento=experimento)

if __name__ == '__main__':
    app.run(debug=True)
    
@app.route('/paciente/<int:id_p>')
def ver_paciente(id_p):
    resultado = db_pacientes.buscar(id_p)
    if resultado:
        paciente = {
            "id": resultado.id,
            "nombre": resultado.nombre,
            "edad": resultado.edad,
            "diagnostico": resultado.diagnostico
        }
        return render_template('paciente.html', paciente=paciente)
    return "Paciente no encontrado", 404 
