import utils

from flask import Flask, render_template, request, url_for, redirect
import socket

app = Flask(__name__)

IP = "127.0.0.1"
PORT = 6010


def get_user(remote_addr):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"get-user-by-addr;{remote_addr}".encode())
    user = client_socket.recv(1024).decode()
    client_socket.close()

    return user if user != '@' else ""


user = ""


@app.route('/')
def base():
    return render_template("base.html")


@app.route('/home')
def home():
    user = get_user(request.remote_addr)
    if user:
        return redirect(url_for('dashboard'))
    return render_template("home.html")


@app.route('/connect', methods=['GET', 'POST'])
def connect():
    user = get_user(request.remote_addr)
    if user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']

        info = ":".join([identifier, password])
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))
        client_socket.send(f"sign-in;{info}".encode())
        name = client_socket.recv(1024).decode()
        client_socket.close()

        if name != '@':
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((IP, PORT))
            client_socket.send(f"register-user;{name}:{request.remote_addr}".encode())
            client_socket.close()
            return redirect(url_for('dashboard'))

        return render_template('connect.html', errortext="Wrong information, try again")

    return render_template('connect.html')


@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    user = get_user(request.remote_addr)
    if user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']
        errortext = ""

        if password == confirm_password:
            info = ":".join([name, email, password])
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((IP, PORT))
            client_socket.send(f"adduser;{info}".encode())
            new_name, new_email, valid_name = client_socket.recv(1024).decode().split(":")
            client_socket.close()
            print('socket closed')

            if new_name == "True" and new_email == "True":
                if valid_name == "True":
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((IP, PORT))
                    client_socket.send(f"register-user;{name}:{request.remote_addr}".encode())
                    client_socket.close()
                    return redirect(url_for('dashboard'))
                else:
                    errortext = f"{name} is not a valid name"

            else:
                if new_name == "False":
                    errortext += f"The name {name} is already taken"
                if new_email == "False":
                    errortext += f" and {email} is already associated with an account" if errortext \
                        else f"{email} is already associated with an account"
        else:
            errortext = "Passwords do not match"

        return render_template('sign-up.html', errortext=errortext)

    return render_template('sign-up.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user=get_user(request.remote_addr), greeting=utils.get_greeting())


@app.route('/my-vaults')
def myvaults():
    return render_template('my-vaults.html')


@app.route("/sign-out")
def sign_out():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"remove-ip;{request.remote_addr}".encode())
    client_socket.close()

    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)