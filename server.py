import socket
import sqlite3
import threading
from datetime import datetime
import hashlib

conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_name TEXT,
                    task_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')

conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def handle_client(client_socket):
    user_id = None
    while True:
        client_socket.send(b"Choose an option:\n1. Sign Up\n2. Log In\n")
        option = client_socket.recv(1024).decode().strip()
        
        if option == "1":
            client_socket.send(b"Enter username: ")
            username = client_socket.recv(1024).decode().strip()
            client_socket.send(b"Enter password: ")
            password = hash_password(client_socket.recv(1024).decode().strip())

            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                client_socket.send(b"Sign up successful!\n")
            except sqlite3.IntegrityError:
                client_socket.send(b"Username already exists. Try again.\n")

        elif option == "2":
            client_socket.send(b"Enter username: ")
            username = client_socket.recv(1024).decode().strip()
            client_socket.send(b"Enter password: ")
            password = hash_password(client_socket.recv(1024).decode().strip())

            cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
            result = cursor.fetchone()
            if result:
                user_id = result[0]
                client_socket.send(b"Login successful!\n")
                break
            else:
                client_socket.send(b"Invalid credentials. Try again.\n")

    while True:
        client_socket.send(b"Choose an option:\n1. Add Task\n2. View All Tasks\n3. View Today's Tasks\n4. View Tasks by Date\n5. Log Out\n")
        option = client_socket.recv(1024).decode().strip()

        if option == "1":
            client_socket.send(b"Enter task name: ")
            task_name = client_socket.recv(1024).decode().strip()
            client_socket.send(b"Enter task date (YYYY-MM-DD): ")
            task_date = client_socket.recv(1024).decode().strip()

            cursor.execute("INSERT INTO tasks (user_id, task_name, task_date) VALUES (?, ?, ?)", (user_id, task_name, task_date))
            conn.commit()
            client_socket.send(b"Task added successfully!\n")

        elif option == "2":
            cursor.execute("SELECT task_name, task_date FROM tasks WHERE user_id = ?", (user_id,))
            tasks = cursor.fetchall()
            response = "The Tasks:\n" + "\n".join([f"{task[0]} - {task[1]}" for task in tasks]) if tasks else "No tasks found."
            client_socket.send(response.encode())

        elif option == "3":
            today = datetime.now().strftime("%Y-%m-%d")  
            cursor.execute("SELECT task_name FROM tasks WHERE user_id = ? AND task_date = ?", (user_id, today))
            tasks = cursor.fetchall()
            response = "The Tasks:\n" + "\n".join([task[0] for task in tasks]) if tasks else "No tasks for today."
            client_socket.send(response.encode())

        elif option == "4":
            client_socket.send(b"Enter date (YYYY-MM-DD): ")
            date = client_socket.recv(1024).decode().strip()
            cursor.execute("SELECT task_name FROM tasks WHERE user_id = ? AND task_date = ?", (user_id, date))
            tasks = cursor.fetchall()
            response = "The Tasks:\n" + "\n".join([task[0] for task in tasks]) if tasks else f"No tasks for {date}."
            client_socket.send(response.encode())

        elif option == "5":
            client_socket.send(b"Logged out.\n")
            break

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 8000))
server.listen(5)
print("Server is running...")

while True:
    client_socket, addr = server.accept()
    print(f"Connection from {addr}")
    client_handler = threading.Thread(target=handle_client, args=(client_socket,))
    client_handler.start()
