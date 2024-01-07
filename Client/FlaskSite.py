import ObjManagement as obj
import utils, crypt

from flask import Flask, render_template, request, url_for, redirect, send_from_directory, jsonify
import socket

app = Flask(__name__)

IP = "127.0.0.1"
PORT = 7891


def get_user(remote_addr):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"get-user-by-addr;{remote_addr}".encode())
    user = client_socket.recv(1024).decode()
    client_socket.close()

    return user if user != '@' else ""


def get_vault(title):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"get-vault-by-title;{title}".encode())
    vault = obj.vaultfromstr(client_socket.recv(1024).decode())
    return vault if vault != '@' else ""


def get_vault_gems(vault):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"get-gems-by-vault;{vault.title}:{vault.user}".encode())
    gem_str = client_socket.recv(1024).decode()
    gems = []
    while gem_str != "@":
        #print(gem_str)
        gem = obj.gemfromstr(gem_str)
        gems.append(gem)
        client_socket.send("next".encode())
        gem_str = client_socket.recv(1024).decode()
    client_socket.close()
    return gems


def get_vaults(user, type):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"get-{type}-vaults;{user}".encode())
    vault_str = client_socket.recv(1024).decode()
    vaults = []
    while vault_str != "@":
        vault = obj.vaultfromstr(vault_str)
        vaults.append(vault)
        client_socket.send("next".encode())
        vault_str = client_socket.recv(1024).decode()
    client_socket.close()
    return vaults


@app.route('/static/<path:filepath>')
def serve_static(filepath):
    return send_from_directory('static', filepath)


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
        password = crypt.rblhash(request.form['password'])

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
            already_connected = client_socket.recv(1024).decode()
            client_socket.close()
            if already_connected == "False":
                return redirect(url_for('dashboard'))
            return render_template('connect.html', errortext="The user is already connected somewhere else")

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
            info = ":".join([name, email, crypt.rblhash(password)])
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((IP, PORT))
            client_socket.send(f"adduser;{info}".encode())
            new_name, new_email, valid_name = client_socket.recv(1024).decode().split(":")
            client_socket.close()

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


@app.route('/<type>-vaults')
def vaults_hub(type):
    user = get_user(request.remote_addr)
    return render_template('vaults-hub.html', type=type, user=user, vaults=get_vaults(user, type))


@app.route('/new-vault/<type>')
def redirect_new_vault(type):
    return redirect(url_for('new_vault', type=type))


@app.route('/new-vault', methods=['GET', 'POST'])
def new_vault():
    user = get_user(request.remote_addr)
    type = request.args.get('type')

    if request.method == "POST":
        title = request.form['title']
        description = request.form['description']
        need_to_choose_type = False
        if not type:
            is_private = request.form.get('private')
            is_shared = request.form.get('shared')
            need_to_choose_type = not is_shared and not is_private
            type = "private" if is_private else "shared"

        if need_to_choose_type:
            return render_template('new-vault.html', user=user, errortext="Choose type")

        if not title or not description:
            return render_template('new-vault.html', user=user, errortext="Missing information")

        vault = obj.Vault(title, user, description, type)

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))
        client_socket.send(f"add-vault;{str(vault)}".encode())
        feedback = client_socket.recv(1024).decode()
        client_socket.close()

        if feedback == "ChangeTitle":
            return render_template('new-vault.html', user=user, errortext="Title already taken")

        return redirect(url_for('vault_page', type=type, vault=title))

    return render_template('new-vault.html', user=user, type=type)


@app.route('/<type>-vaults/<vault>')
def vault_page(type, vault):
    user = get_user(request.remote_addr)
    vault = get_vault(vault)
    gems = get_vault_gems(vault)
    return render_template('vault-page.html', user=user, vault=vault, gems=gems)


@app.route('/update-description', methods=['POST'])
def update_description():
    data = request.get_json()
    user = get_user(request.remote_addr)
    title = data['vaultTitle']
    new_desc = data['description']

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"update-vault-desc;{user}:{title}:{new_desc}".encode())
    client_socket.close()

    return '', 200


@app.route('/check-description', methods=['POST'])
def check_description():
    data = request.get_json()
    user = get_user(request.remote_addr)
    title = data['vaultTitle']

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"find-desc;{user}:{title}".encode())
    desc = client_socket.recv(1024).decode()
    client_socket.close()

    return desc


@app.route("/sign-out")
def sign_out():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(f"remove-ip;{request.remote_addr}".encode())
    client_socket.close()

    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)