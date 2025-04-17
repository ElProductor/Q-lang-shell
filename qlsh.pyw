import os
import time
import re
import platform
import datetime
import json
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

# Estilos de color
estilo = Style.from_dict({
    'prompt': 'bold cyan',
    'error': 'bold red',
    'info': 'italic yellow',
    'success': 'bold green',
    'warning': 'bold magenta',
    'system': 'bold blue'
})

# Comandos conocidos para autocompletar
comandos = [
    "ls", "dir", "exit", "help", "InitSensor(temp1)", "Read(temp1)", "ActivateFan()", "ActivateLED()",
    "if (Read(temp1) > 30)", "if (Read(temp1) < 22)", "if (SensorActive(motion1))",
    "let", "while", "read(\"archivo.txt\")", "write(\"archivo.txt\", \"contenido\")",
    "quantum.register(", "quantum.measure(", "!python", "clear", "version", "datetime", "sysinfo",
    "log", "save_session", "load_session", "assistant(\"\")", "monitor(\"temp1\")", "alias(\"\")",
    "explore()", "safe_mode", "run(\"script.qlang\")"
]
completer = WordCompleter(comandos, ignore_case=True)

# Variables globales
variables = {}
quantum_register = []
session_log = []
aliases = {}
safe_mode = False

# Arduino (opcional)
try:
    import serial
    PORT = "COM3"
    BAUD = 9600
    arduino = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    arduino_disponible = True
    print("[INFO] Arduino conectado.")
except:
    arduino_disponible = False
    print("[INFO] Modo simulado (Arduino no conectado).")

# Función IA asistente básica (placeholder)
def assistant(pregunta):
    respuestas = {
        "como estas": "¡Estoy funcionando a toda máquina!",
        "que puedes hacer": "Puedo simular sensores, usar lógica cuántica, guardar sesiones y más.",
        "hola": "¡Hola! ¿En qué te ayudo hoy?"
    }
    clave = pregunta.lower()
    for k in respuestas:
        if k in clave:
            return respuestas[k]
    return "No entendí tu pregunta, pero puedo aprender."

def enviar_micro_binario(binario):
    if arduino_disponible:
        arduino.write((binario + '\n').encode())
        print(f"[success] → Enviado a Arduino: {binario}")
    else:
        print(f"[info] Simulación Arduino → {binario}")

def ejecutar_clasico(cmd):
    if cmd in aliases:
        cmd = aliases[cmd]

    if cmd in ["ls", "dir"]:
        for f in os.listdir():
            print(" -", f)
    elif cmd == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
    elif cmd.startswith("read("):
        try:
            archivo = re.findall(r'read\(["\'](.+?)["\']\)', cmd)[0]
            with open(archivo, "r", encoding="utf-8") as f:
                print(f.read())
        except:
            print("[error] No se pudo leer el archivo.")
    elif cmd.startswith("write("):
        partes = re.findall(r'write\(["\'](.+?)["\'],\s*["\'](.+?)["\']\)', cmd)
        if partes:
            archivo, contenido = partes[0]
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(contenido)
            print("[success] Archivo escrito.")
        else:
            print("[error] Sintaxis incorrecta.")
    elif cmd == "datetime":
        print("[time]", datetime.datetime.now())
    elif cmd == "sysinfo":
        print("Sistema operativo:", platform.system(), platform.release())
        print("Procesador:", platform.processor())
        print("Python:", platform.python_version())
    elif cmd == "version":
        print("QLang Shell v6.0 UltraPRO")
    elif cmd == "log":
        for line in session_log:
            print(line)
    elif cmd == "save_session":
        with open("session_log.json", "w") as f:
            json.dump(session_log, f)
        print("[success] Sesión guardada.")
    elif cmd == "load_session":
        try:
            with open("session_log.json", "r") as f:
                data = json.load(f)
                for line in data:
                    print("[loaded]", line)
        except:
            print("[error] No se pudo cargar la sesión.")
    elif cmd.startswith("alias("):
        m = re.findall(r'alias\(["\'](.+?)["\'],\s*["\'](.+?)["\']\)', cmd)
        if m:
            aliases[m[0][0]] = m[0][1]
            print(f"[alias] '{m[0][0]}' → '{m[0][1]}'")
    elif cmd == "explore()":
        print("[explorer] Archivos en directorio:")
        for f in os.listdir():
            print(" ->", f)
    elif cmd == "safe_mode":
        global safe_mode
        safe_mode = not safe_mode
        print("[mode] Modo seguro:", "Activado" if safe_mode else "Desactivado")
    else:
        print("[info] Comando clásico no reconocido.")

def ejecutar_cuantico(cmd):
    global quantum_register
    if cmd.startswith("quantum.register("):
        n = int(cmd.split("(")[1].split(")")[0])
        quantum_register = [0] * n
        print(f"[success] Registro cuántico inicializado con {n} qubits.")
    elif cmd.startswith("quantum.measure("):
        i = int(cmd.split("(")[1].split(")")[0])
        if 0 <= i < len(quantum_register):
            print(f"[Q] Qubit {i} mide: {quantum_register[i]}")
        else:
            print("[Q] Qubit fuera de rango.")
    elif cmd == "help quantum":
        print("Comandos cuánticos disponibles:")
        print(" - quantum.register(N)")
        print(" - quantum.measure(I)")
    else:
        print("[Q] Comando cuántico no reconocido.")

def evaluar_expresion(expr):
    for var in variables:
        expr = expr.replace(var, str(variables[var]))
    try:
        return eval(expr)
    except Exception as e:
        print("[error] Evaluando expresión:", e)
        return None

def procesar_estructura(cmd):
    if cmd.startswith("let "):
        partes = cmd[4:].split("=")
        if len(partes) == 2:
            nombre = partes[0].strip()
            valor = evaluar_expresion(partes[1].strip())
            if valor is not None:
                variables[nombre] = valor
                print(f"[VAR] {nombre} = {valor}")
        else:
            print("[error] Sintaxis de variable incorrecta.")
    elif cmd.startswith("if "):
        condicion = cmd[3:].strip()
        if evaluar_expresion(condicion):
            print("[IF] Condición verdadera.")
        else:
            print("[IF] Condición falsa.")
    elif cmd.startswith("while "):
        match = re.match(r'while (.+):\s*(.+)', cmd)
        if match:
            cond, accion = match.groups()
            while evaluar_expresion(cond):
                procesar_comando(accion)
        else:
            print("[error] Sintaxis de while incorrecta.")
    else:
        print("[error] Estructura no reconocida.")

def procesar_comando(cmd):
    cmd = cmd.strip()
    session_log.append(cmd)

    if cmd.lower() == 'exit':
        print("Saliendo de QLang Shell.")
        exit()
    elif cmd == "help":
        mostrar_ayuda()
    elif cmd.startswith("assistant("):
        pregunta = re.findall(r'assistant\(["\'](.+?)["\']\)', cmd)
        if pregunta:
            print("[IA]", assistant(pregunta[0]))
    elif cmd in MICRO_BINARY_TABLE:
        enviar_micro_binario(MICRO_BINARY_TABLE[cmd])
    elif cmd.startswith("quantum."):
        ejecutar_cuantico(cmd)
    elif cmd.startswith("let ") or cmd.startswith("if ") or cmd.startswith("while "):
        procesar_estructura(cmd)
    elif cmd.startswith("!python"):
        try:
            exec(input(">>> "))
        except Exception as e:
            print("[python-error]", e)
    else:
        ejecutar_clasico(cmd)

def mostrar_ayuda():
    print("\n[AYUDA GENERAL]")
    print(" - ls / dir: listar archivos")
    print(" - clear: limpiar pantalla")
    print(" - read('archivo') / write('archivo', 'contenido')")
    print(" - let x = 5: definir variables")
    print(" - while condición:loop")
    print(" - quantum.register(N) / quantum.measure(I)")
    print(" - version / datetime / sysinfo / log")
    print(" - alias('nuevo', 'comando real')")
    print(" - explore(): explorador simple de archivos")
    print(" - assistant('pregunta'): IA simple integrada")
    print(" - safe_mode: activa/desactiva modo seguro")
    print(" - exit: salir\n")

def shell():
    session = PromptSession(completer=completer, style=estilo)
    print("\nQLang Shell v6.0 UltraPRO [IA + Quantum + Safe Mode + Explorador + Alias + Plugins]")
    print("Escribe 'help' para ver comandos disponibles. Usa tabulación para autocompletar.\n")

    while True:
        try:
            cmd = session.prompt("[QLang] > ", style=estilo)
            procesar_comando(cmd)
        except KeyboardInterrupt:
            print("\n[INTERRUPCION] Usa 'exit' para salir.")
        except Exception as e:
            print("[ERROR]", e)

if __name__ == "__main__":
    shell()
