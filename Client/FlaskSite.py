import ObjManagement as obj
import utils, crypt

from flask import Flask, render_template, request, url_for, redirect, send_from_directory, jsonify
import socket, pickle, uuid, ast

app = Flask(__name__)

IP = "127.0.0.1"
PORT = 7891


def open_con(action, data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(pickle.dumps((action, data)))
    return client_socket


def get_mac_address():
    mac = uuid.getnode()
    return crypt.rblhash(':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2)))


def get_user():
    client_socket = open_con("get-user-by-addr", get_mac_address())
    user = client_socket.recv(1024).decode()
    client_socket.close()
    return user if user != '@' else ""


def get_vault(title):
    client_socket = open_con("get-vault-by-title", title)
    vault = client_socket.recv(1024)
    return pickle.loads(vault) if vault != b'@' else ""


def get_vault_gems(vault):
    client_socket = open_con("get-gems-by-vault", vault)
    gem = client_socket.recv(1024)
    gems = []
    while gem != b"@":
        gem = pickle.loads(gem)
        gems.append(gem)
        client_socket.send("next".encode())
        gem = client_socket.recv(1024)
    client_socket.close()
    return gems


def get_vaults(user, type):
    client_socket = open_con(f"get-vaults-by-type", (user, type))
    vault = client_socket.recv(1024)
    vaults = []
    while vault != b"@":
        vault = pickle.loads(vault)
        vaults.append(vault)
        client_socket.send("next".encode())
        vault = client_socket.recv(1024)
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
    user = get_user()
    if user:
        return redirect(url_for('dashboard'))
    return render_template("home.html")


@app.route('/connect', methods=['GET', 'POST'])
def connect():
    user = get_user()
    if user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form['identifier']
        password = crypt.rblhash(request.form['password'])

        client_socket = open_con("sign-in", (identifier, password))
        name = client_socket.recv(1024).decode()
        client_socket.close()

        if name != '@':
            client_socket = open_con("register-user", (name, get_mac_address()))
            already_connected = client_socket.recv(1024).decode()
            client_socket.close()
            if already_connected == "False":
                return redirect(url_for('dashboard'))
            return render_template('connect.html', errortext="The user is already connected somewhere else")

        return render_template('connect.html', errortext="Wrong information, try again")

    return render_template('connect.html')


@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    user = get_user()
    if user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']
        errortext = ""

        if password == confirm_password:
            client_socket = open_con("adduser", (name, email, crypt.rblhash(password)))
            new_name, new_email, valid_name = pickle.loads(client_socket.recv(1024))
            client_socket.close()

            if new_name and new_email:
                if valid_name:
                    client_socket = open_con("register-user", (name, get_mac_address()))
                    client_socket.close()
                    return redirect(url_for('dashboard'))
                else:
                    errortext = f"{name} is not a valid name"

            else:
                if not new_name:
                    errortext += f"The name {name} is already taken"
                if not new_email:
                    errortext += f" and {email} is already associated with an account" if errortext \
                        else f"{email} is already associated with an account"
        else:
            errortext = "Passwords do not match"

        return render_template('sign-up.html', errortext=errortext)

    return render_template('sign-up.html')


@app.route('/dashboard')
def dashboard():
    user = get_user()
    if user:
        return render_template('dashboard.html', user=user, greeting=utils.get_greeting())
    return redirect(url_for('home'))


@app.route('/<type>-vaults')
def vaults_hub(type):
    user = get_user()
    return render_template('vaults-hub.html', type=type, user=user, vaults=get_vaults(user, type))


@app.route('/new-vault/<type>')
def redirect_new_vault(type):
    return redirect(url_for('new_vault', type=type))


@app.route('/new-vault', methods=['GET', 'POST'])
def new_vault():
    user = get_user()
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

        client_socket = open_con("add-vault", vault)
        feedback = client_socket.recv(1024).decode()
        client_socket.close()

        if feedback == "ChangeTitle":
            return render_template('new-vault.html', user=user, errortext="Title already taken")

        return redirect(url_for('vault_page', type=type, vault=title))

    return render_template('new-vault.html', user=user, type=type)


@app.route('/<type>-vaults/<vault>', methods=["GET", "POST"])
def vault_page(type, vault):
    user = get_user()
    vault = get_vault(vault)
    gems = get_vault_gems(vault)

    if request.method == "POST":
        if 'searchtitle' in request.form:
            search = request.form['searchtitle']
            gems = [gem for gem in gems if search in gem.title]
        elif 'searchcontent' in request.form:
            search = request.form['searchcontent']
            gems = [gem for gem in gems if search in gem.content]

    if vault.is_in_vault(user):
        return render_template('vault-page.html', user=user, vault=vault, gems=gems)
    return redirect(url_for('no_access', user=user, title=vault.title))


@app.route('/no-access/<user>/<title>')
def no_access(user, title):
    vault = get_vault(title)
    return render_template('no-access.html', user=user, vault=vault)


@app.route('/update-description', methods=['POST'])
def update_description():
    data = request.get_json()
    user = get_user()
    title = data['vaultTitle']
    new_desc = data['description']

    client_socket = open_con("update-vault-desc", (user, title, new_desc))
    client_socket.close()

    return '', 200


@app.route('/check-description', methods=['POST'])
def check_description():
    data = request.get_json()
    user = get_user()
    title = data['vaultTitle']

    client_socket = open_con("find-desc", (user, title))
    desc = client_socket.recv(1024).decode()
    client_socket.close()

    return desc


@app.route('/add-new-gem', methods=['POST'])
def add_new_gem():
    data = request.get_json()
    user = get_user()
    vault_title = data['vaultTitle']
    new_gem_title = data['newGemTitle']
    new_gem_content = data['newGemContent']

    client_socket = open_con("add-gem-to-vault", (user, vault_title, new_gem_title, new_gem_content))
    client_socket.close()

    return '', 200


@app.route('/gem-title-validation', methods=['POST'])
def gem_title_validation():
    data = request.get_json()
    user = get_user()
    vault = data['vaultTitle']
    title = data['gemTitle']

    client_socket = open_con("gem-title-validation", (user, vault, title))
    response = int(client_socket.recv(1024).decode())
    client_socket.close()

    return '', response


@app.route('/delete-gem', methods=['POST'])
def delete_gem():
    data = request.get_json()
    gem = data['gem']
    vault = data['vault']

    client_socket = open_con("delete-gem-from-vault", (gem, vault))
    client_socket.close()

    return '', 200


@app.route('/making-<vault>-public')
def make_public(vault):
    client = open_con("make-public", vault)
    return redirect(f'/shared-vaults/{vault}')


@app.route("/sign-out")
def sign_out():
    client_socket = open_con("remove-mac", get_mac_address())
    client_socket.recv(1024)
    client_socket.close()

    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)