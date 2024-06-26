import ObjManagement as obj
from flask import Flask, render_template, request, url_for, redirect, send_from_directory, jsonify
import socket, pickle, uuid, ast

app = Flask(__name__)

IP = "192.168.1.113"
PORT = 7891
util = obj.Utils()


def open_con(action, data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.send(util.flipbase(pickle.dumps((action, data)), 'e'))
    return client_socket


def get_mac_address():
    mac = uuid.getnode()
    return util.rblhash(':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2)))


def get_user():
    client_socket = open_con("get-user-by-addr", get_mac_address())
    user = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()
    return user if user != '@' else ""


def get_vault(title):
    client_socket = open_con("get-vault-by-title", title)
    vault = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()
    return vault if vault != b'@' else ""


def get_vaults(user, type):
    client_socket = open_con(f"get-vaults-by-type", (user, type))
    vault = util.flipbase(client_socket.recv(1024), 'd')
    vaults = []
    while vault != "@":
        vaults.append(vault)
        client_socket.send("next".encode())
        vault = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()
    return vaults


def private_vaults(self):
    return get_vaults(self.name, "private")


def shared_vaults(self):
    return get_vaults(self.name, "shared")


obj.UserInfo.private_vaults = private_vaults
obj.UserInfo.shared_vaults = shared_vaults


def get_userinfo():
    client_socket = open_con("get-user-by-addr", get_mac_address())
    user = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()
    return obj.UserInfo(user) if user != '@' else ""


def get_vault_gems(vault):
    client_socket = open_con("get-gems-by-vault", vault)
    gem = util.flipbase(client_socket.recv(1024), 'd')
    gems = []
    while gem != "@":
        gems.append(gem)
        client_socket.send("next".encode())
        gem = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()
    return gems


@app.route('/static/<path:filepath>')
def serve_static(filepath):
    return send_from_directory('static', filepath)


user = ""


@app.route('/')
def base():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    user = get_user()
    if user:
        return redirect(url_for('dashboard'))
    return render_template("home.html")


@app.route('/about')
def about():
    user = get_user()
    return render_template("home.html", user=user)


@app.route('/connect', methods=['GET', 'POST'])
def connect():
    user = get_user()
    if user:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form['identifier']
        password = util.rblhash(request.form['password'])

        client_socket = open_con("sign-in", (identifier, password))
        name = util.flipbase(client_socket.recv(1024), 'd')
        client_socket.close()

        if name != '@':
            client_socket = open_con("register-user", (name, get_mac_address()))
            already_connected = util.flipbase(client_socket.recv(1024), 'd')
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
            client_socket = open_con("adduser", (name, email, util.rblhash(password)))
            new_name, new_email, valid_name = util.flipbase(client_socket.recv(1024), 'd')
            client_socket.close()

            if new_name and new_email:
                if valid_name:
                    client_socket = open_con("register-user", (name, get_mac_address()))
                    client_socket.recv(1024)
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
        return render_template('dashboard.html', user=user, greeting=util.get_greeting())
    return redirect(url_for('home'))


@app.route('/<type>-vaults')
def vaults_hub(type):
    user = get_userinfo()
    if type == "shared":
        return render_template('vaults-hub.html', type=type, user=user.name, vaults=user.shared_vaults())
    return render_template('vaults-hub.html', type=type, user=user.name, vaults=user.private_vaults())


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
        feedback = util.flipbase(client_socket.recv(1024), 'd')
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
    desc = util.flipbase(client_socket.recv(1024), 'd')
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
    response = int(util.flipbase(client_socket.recv(1024), 'd'))
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


@app.route('/get-gem-content', methods=['POST'])
def get_gem_content():
    data = request.get_json()
    user = get_user()
    vault_title = data['vaultTitle']
    gem_title = data['gemTitle']

    client_socket = open_con("get-gem-content", (gem_title, vault_title))
    content = util.flipbase(client_socket.recv(1024), 'd')
    client_socket.close()

    return content


@app.route('/update-gem-content', methods=['POST'])
def update_gem_content():
    data = request.get_json()
    user = get_user()
    vault_title = data['vaultTitle']
    gem_title = data['gemTitle']
    updated_content = data['updatedContent']

    client_socket = open_con("update-gem-content", (user, vault_title, gem_title, updated_content))
    client_socket.close()

    return obj.string_preview(updated_content, 14, 21)


@app.route('/making-<vault>-public')
def make_public(vault):
    client = open_con("make-public", vault)
    client.close()
    return redirect(f'/shared-vaults/{vault}')


@app.route('/produce-shared-key', methods=["POST"])
def produce_key():
    data = request.get_json()
    vault_title = data['vaultTitle']
    key = util.create_key()
    client = open_con("produce-shared-key", (vault_title, key))
    client.close()
    return key


@app.route('/send-key-request', methods=['POST'])
def send_key_request():
    data = request.get_json()
    key = data['key']
    user = data['user']

    client_socket = open_con("check-key-and-pend-request", (key, user))
    response = int(util.flipbase(client_socket.recv(1024), 'd'))
    client_socket.close()

    return '', response


@app.route("/add-collaborator", methods=['POST'])
def add_collaborator():
    data = request.get_json()
    user = data['user']
    rank = data['rank'].lower()
    vault = data['vault']

    client_socket = open_con("pending-to-collaborator", (user, rank, vault))
    client_socket.close()

    return '', 200


@app.route("/deny-collaborator", methods=["POST"])
def deny_collaborator():
    data = request.get_json()
    user = data['user']
    vault = data['vault']

    client_socket = open_con("delete-pending", (user, vault))
    client_socket.close()

    return '', 200


@app.route("/sign-out")
def sign_out():
    client_socket = open_con("remove-mac", get_mac_address())
    client_socket.recv(1024)
    client_socket.close()

    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)