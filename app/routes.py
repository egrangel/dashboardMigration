from flask import flash, request, jsonify, render_template, redirect, url_for, session
from flask_login import current_user, login_required, login_user, logout_user
import urllib3
from app import app, db, dashboardMigration
from app.forms import ConfigurationForm, LoginForm, RegistrationForm
from app.models import Configuration, User

# Suppress only InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@app.route("/")
@login_required
def index():
    formConfig = ConfigurationForm()
    configurations = Configuration.query.all()

    return render_template("index.html", form=formConfig, configurations=configurations)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Get the page the user wanted to access originally, if any
            next_page = request.args.get('next')
            return redirect(next_page or url_for("index"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))
   
    return render_template("login.html", title="Sign In", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)

@app.route('/save_configuration', methods=['POST'])
@login_required
def save_configuration():
    form = ConfigurationForm(request.form)
    if form.validate_on_submit():
        config_id = request.form.get('config_id')

        if config_id:
            # Update the existing configuration
            config = Configuration.query.get(config_id)
            if config:
                config.config_name = form.config_name.data
                config.es_url = form.es_url.data
                config.es_port = form.es_port.data
                config.kb_url = form.kb_url.data
                config.kb_port = form.kb_port.data
                config.es_user = form.es_user.data
                config.es_pass = form.es_pass.data
                config.es_index_name = form.es_index_name.data

                db.session.commit()

                flash('Configuration updated successfully!', 'success')
                return redirect(url_for("index"))
            else:
                return jsonify({'error': 'Configuration not found'}), 404
        else:
            # Create a new configuration
            config = Configuration(
                config_name=form.config_name.data,
                es_url=form.es_url.data,
                es_port=form.es_port.data,
                kb_url=form.kb_url.data,
                kb_port=form.kb_port.data,
                es_user=form.es_user.data,
                es_pass=form.es_pass.data,
                es_index_name=form.es_index_name.data
            )

            try:
                db.session.add(config)
                db.session.commit()
            except Exception as e:
                return jsonify({'error': str(e)}), 500

            flash('Configuration included successfully!', 'success')
            return redirect(url_for("index"))
    else:
        return jsonify({'error': 'Invalid form data', 'errors': form.errors}), 400

@app.route('/configuration/<int:config_id>', methods=['GET', 'DELETE'])
@login_required
def get_configuration(config_id):
    if request.method == 'DELETE':
        config = Configuration.query.get_or_404(config_id)
        db.session.delete(config)
        db.session.commit()
        return jsonify({'message': 'Configuration deleted successfully!'})
    elif request.method == 'GET':
      config = Configuration.query.get_or_404(config_id)
      return {
          'config_id': config.config_id,
          'config_name': config.config_name,
          'es_url': config.es_url,
          'es_port': config.es_port,
          'kb_url': config.kb_url,
          'kb_port': config.kb_port,
          'es_user': config.es_user,
          'es_pass': config.es_pass,
          'es_index_name': config.es_index_name
      }

@app.route("/get_spaces", methods=["POST"])
@login_required
def get_spaces():
    try:
        data = request.json
        automation = dashboardMigration.ElasticAutomation.from_config(data)

        # Fetch spaces from Kibana
        spaces = automation.get_spaces()
        return jsonify({"spaces": spaces})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_roles", methods=["GET", "POST"])
@login_required
def get_roles():
    try:
        data = request.json
        automation = dashboardMigration.ElasticAutomation.from_config(data)

        # Fetch roles from Kibana
        roles = automation.get_roles()
        return jsonify({"roles": roles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_users", methods=["GET", "POST"])
@login_required
def get_users():
    try:
        data = request.json
        automation = dashboardMigration.ElasticAutomation.from_config(data)

        # Fetch users from Kibana
        users = automation.get_users()

        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/get_dataviews", methods=["GET", "POST"])
@login_required
def get_dataviews():
    try:
        data = request.json
        automation = dashboardMigration.ElasticAutomation.from_config(data)

        # Fetch dataviews from Kibana
        dataviews = automation.get_dataviews()
        return jsonify({"dataviews": dataviews})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route("/delete_space", methods=["DELETE"])
@login_required
def delete_space():
    try:
        data = request.json

        space_id = data.get("space_id")
        
        if not space_id:
            return jsonify({"success": False, "message": "No space ID provided"}), 400
            
        automation = dashboardMigration.ElasticAutomation.from_config(data)
        
        automation.delete_space(space_id)
        return jsonify({"success": True, "message": f"Space {space_id} deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/run_automation", methods=["POST"])
@login_required
def run_automation():
    data = request.json

    # Get the selected configuration
    config_id = data.get("config_id")
    if not config_id:
        return jsonify({"error": "No configuration selected"}), 400

    # Fetch the configuration from the database
    config = Configuration.query.get(config_id)
    if not config:
        return jsonify({"error": "Configuration not found"}), 404

    # Prepare the automation data
    automation_data = {
        "elastic_host": config.es_url,
        "elastic_port": config.es_port,
        "kibana_host": config.kb_url,
        "kibana_port": config.kb_port,
        "username": config.es_user,
        "password": config.es_pass,
        "es_index_name": config.es_index_name,
        "client_id": data.get("client_id"),
        "space_name": data.get("space_name")
    }

    # Initialize the automation object
    automation = dashboardMigration.ElasticAutomation.from_config(automation_data)

    # Prepare variables for automation tasks
    client_id = data.get("client_id")
    bi_client_name = f'client_{client_id}'
    bi_role_name = f'{bi_client_name}_role'
    bi_indice = "dguard-analytics-events-demo"
    bi_alias_name = f'{bi_client_name}_alias'
    bi_space_id = f'{bi_client_name}_space'
    bi_space_name = f'{data.get("space_name")}'
    bi_data_view_name = f'{bi_client_name}_data_view'

    results = []

    # Execute only the checked tasks
    if data.get("create_index_alias", False):
        results.append(automation.create_index_alias(bi_indice, bi_alias_name, client_id))

    if data.get("create_space", False):
        results.append(automation.create_space(bi_space_id, name=bi_space_name, description="Space for events analysis"))

    if data.get("create_role", False):
        results.append(automation.create_role(role_name=bi_role_name, indice=bi_alias_name, space=bi_space_id))

    if data.get("create_user", False):
        results.append(automation.create_user(username=bi_client_name, password=bi_client_name, roles=[bi_role_name]))

    if data.get("create_data_view", False):
        results.append(automation.create_data_view(space_id=bi_space_id, dataview_name=bi_data_view_name, index_pattern=bi_alias_name))

    if data.get("copy_dashboards", False):
        results.append(automation.copy_dashboards(config_id=config_id, client_id=client_id))

    # Refresh spaces (if applicable)
    get_spaces()

    return jsonify({"results": results})

@app.route("/create_index_alias", methods=["POST"])
@login_required
def create_index_alias():
    data = request.json
    bi_client_id = data.get("client_id")
    bi_client_name = f'client_{bi_client_id}'
    bi_alias_name = f'{bi_client_name}_alias'
    bi_indice = data.get("bi_indice")

    data = request.json
    automation = dashboardMigration.ElasticAutomation.from_config(data)

    result = automation.create_index_alias(bi_indice, bi_alias_name, bi_client_id)
    return jsonify({"result": result})

@app.route("/run_all", methods=["POST"])
@login_required
def run_all():
    try:
        data = request.json
        
        bi_client_id = data.get("client_id")
        bi_client_name = f'client_{bi_client_id}'
        bi_space_id = f'{bi_client_name}_space'
        bi_space_name = data.get("space_name", "Client Space")
        bi_role_name = f'{bi_client_name}_role'
        bi_index_name = data.get("bi_index_name")
        bi_alias_name = f'{bi_client_name}_alias'
        bi_data_view_name = f'{bi_client_name}_data_view'
        
        # Initialize automation
        automation = dashboardMigration.ElasticAutomation.from_config(data)

        results = []
        if data.get("create_index_alias"):
            results.append({
                "operation": "create_index_alias",
                "result": automation.create_index_alias(bi_index_name, bi_alias_name, bi_client_id)
            })
        if data.get("create_space"):
            results.append({
                "operation": "create_space",
                "result": automation.create_space(bi_space_id, name=bi_space_name, description="Space for events analysis")
            })
        if data.get("create_role"):
            results.append({
                "operation": "create_role",
                "result": automation.create_role(role_name=bi_role_name, indice=bi_alias_name, space=bi_space_id)
            })
        if data.get("create_user"):
            results.append({
                "operation": "create_user",
                "result": automation.create_user(username=bi_client_name, password=bi_client_name, roles=[bi_role_name])
            })
        if data.get("create_data_view"):
            results.append({
                "operation": "create_data_view", 
                "result": automation.create_data_view(space_id=bi_space_id, dataview_name=bi_data_view_name, index_pattern=bi_alias_name)
            })

        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500