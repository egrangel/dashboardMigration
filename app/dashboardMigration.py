import json
import requests

from app.models import Configuration

class ElasticAutomation:
    def __init__(self, elastic_host, elastic_port, kibana_host, kibana_port, username, password,
                 verify_ssl=True, ca_cert_path=None):
        self.elastic_base_url = f"https://{elastic_host}:{elastic_port}"
        self.kibana_base_url = f"https://{kibana_host}:{kibana_port}"
        self.auth = (username, password)
        self.headers = {'Content-Type': 'application/json', 'kbn-xsrf': 'true'}
        self.verify_ssl = ca_cert_path if ca_cert_path else verify_ssl

    @staticmethod
    def from_config(config):
        return ElasticAutomation(
            config.get('es_url'), 
            config.get('es_port', 9200), 
            config.get('kb_url'), 
            config.get('kb_port', 5601),
            config.get('es_user', 'elastic'), 
            config.get('es_pass', ''), 
            config.get('verify_ssl', False), 
            config.get('ca_cert_path', None)
        )

    def create_index_alias(self, index_pattern, alias_name, client_id):
        """
        Create an index alias with client_id filter

        Args:
            index_pattern (str): Index pattern to apply the alias
            alias_name (str): Alias name to create
            client_id (str): Client ID to filter the index pattern
        """
        if client_id is None:
            raise ValueError("client_id is required to create an alias")
        
        self.print_log(f"Creating alias {alias_name} for index pattern {index_pattern} with client_id filter {client_id}")
        
        url = f"{self.elastic_base_url}/_aliases"
        payload = {
            "actions": [
                {
                    "add": {
                        "index": index_pattern,
                        "alias": alias_name,
                        "filter": {
                            "term": {
                                "client_id": client_id
                            }
                        }
                    }
                }
            ]
        }
        response = requests.post(url, json=payload, auth=self.auth, verify=self.verify_ssl)

        if response.status_code == 200:
            return {"status": "success", "message": "Alias created successfully"}
        else:
            return {"status": "error", "message": response.text}

    def create_role(self, role_name, indice, space):
        """
        Create a role with specified index privileges

        Args:
            role_name (str): Role name to create
            indice (str): Index pattern to apply the role
            space (str): Space name to apply the role        
        """

        self.print_log(f"Creating role {role_name} for index pattern {indice} and space {space}")

        url = f"{self.elastic_base_url}/_security/role/{role_name}"
        privileges=["read", "view_index_metadata"]

        payload = {
            "indices": [
                {
                    "names": indice,
                    "privileges": privileges
                }
            ],
            "applications": [
                {
                  "application": "kibana-.kibana",
                  "privileges": ["feature_dashboard.read"],
                  "resources": [f"space:{space}"]
                }
            ]
        }
        response = requests.put(url, json=payload, auth=self.auth, headers=self.headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Role created successfully"}
        else:
            return {"status": "error", "message": response.text}

    def create_user(self, username, password, roles):
        """
        Create a user and assign roles

        Args:
            username (str): Username to create
            password (str): Password for the user
            roles (list): List of roles to assign
        """

        self.print_log(f"Creating user {username} with roles {roles}")

        url = f"{self.elastic_base_url}/_security/user/{username}"
        payload = {
            "password": password,
            "roles": roles,
            "full_name": username,
            "enabled": True
        }
        response = requests.put(url, json=payload, auth=self.auth, headers=self.headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return {"status": "success", "message": "User created successfully"}
        else:
            return {"status": "error", "message": response.text}

    def create_data_view(self, space_id, dataview_name, index_pattern):
        """
        Create a data view in Kibana

        Args:
            space_id (str): ID of the space to create the data view
            dataview_name (str): Name of the data view
            index_pattern (str): Index pattern to associate with the data view
        """

        self.print_log(f"Creating data view {dataview_name} for index pattern {index_pattern} in space {space_id}")

        url = f"{self.kibana_base_url}/s/{space_id}/api/data_views/data_view"
        payload = {
            "data_view": {
                "title": index_pattern,
                "name": dataview_name,
                "timeFieldName": "event_timestamp"
            }
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Data View created successfully"}
        else:
            return {"status": "error", "message": response.text}

    def create_space(self, space_id, name, description=""):
        """
        Create a Kibana space

        Args:
            space_id (str): ID of the space to create
            name (str): Name of the space
            description (str): Description of the space
        """
        self.print_log(f"Creating space {name} with ID {space_id}")

        url = f"{self.kibana_base_url}/api/spaces/space"

        disabled_features = [
            'enterpriseSearch', 'discover', 'canvas', 'maps', 'ml', 'logs', 'visualize', 'infrastructure', 
            'apm', 'uptime', 'observabilityCases', 'siem', 'securitySolutionCases', 'slo', 'dev_tools', 'advancedSettings', 
            'filesManagement', 'filesSharedImage', 'savedObjectsManagement', 'savedQueryManagement', 
            'savedObjectsTagging', 'osquery', 'actions', 'generalCases', 'guidedOnboardingFeature', 'rulesSettings', 
            'maintenanceWindow', 'stackAlerts', 'fleetv2', 'fleet', 'monitoring']

        payload = {
            "id": space_id,
            "name": name,
            "description": description,
            "disabledFeatures": disabled_features
        }
        response = requests.post(url, json=payload, auth=self.auth, headers=self.headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Space created successfully"}
        else:
            return {"status": "error", "message": response.text}
    
    def get_alias_structure(self, alias_name):
        """
        Retrieve the structure of an alias, including its associated indices and filters.

        Args:
            alias_name (str): The name of the alias to retrieve.

        Returns:
            dict: The alias structure, including indices and filters.
        """
        self.print_log(f"Retrieving alias structure for {alias_name}")

        url = f"{self.elastic_base_url}/_alias/{alias_name}"
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to retrieve alias structure: {response.status_code} - {response.text}")
      
    def get_kibana_features(self):
        """
        Retrieve a list of all Kibana features.

        Returns:
            list: A list of feature IDs that can be used in disabledFeatures.
        """
        self.print_log("Retrieving Kibana features")

        url = f"{self.kibana_base_url}/api/features"
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=self.verify_ssl)

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve Kibana features: {response.status_code} - {response.text}")

        features = response.json()
        feature_ids = [feature["id"] for feature in features]
        return feature_ids
    
    def export_dashboard(self, dashboard_id, source_space_id='default'):
        """
        Export a dashboard from a specific space
        
        Args:
            dashboard_id (str): ID of the dashboard to export
            space_id (str): Optional space ID. If None, uses default space
        """
        self.print_log(f"Exporting dashboard {dashboard_id} from space {source_space_id}")

        url = f"{self.kibana_base_url}/s/{source_space_id}/api/saved_objects/_export"
        headers = {'kbn-xsrf': 'true', 'Content-Type': 'application/json'}
        
        payload = json.dumps({
          "objects": [
            {
              "type": "dashboard",
              "id": dashboard_id
            }
          ],
          "includeReferencesDeep": True,
          "excludeExportDetails": False
        })

        response = requests.post(url, data=payload, auth=self.auth, headers=headers, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return response.content
        else:
            return {"status": "error", "message": response.text}
            

    def import_dashboard(self, export_content, target_space_id, source_data_view, target_data_view):
        """
        Import a dashboard into a specific space and update its data view
        
        Args:
            export_content (bytes): The exported dashboard content
            source_space_id (str): Source space ID
            target_space_id (str): Target space ID
            source_data_view (str): Original data view ID/name
            target_data_view (str): New data view ID/name to use
        """
        self.print_log(f"Importing dashboard to space {target_space_id} and updating data view from {source_data_view} to {target_data_view}")

        url = f"{self.kibana_base_url}/s/{target_space_id}/api/saved_objects/_import"
        
        params = {"overwrite": "true", "createNewCopies": "false"}
        
        # Create the multipart form data
        files = {
          'file': ('dashboard.ndjson', export_content if isinstance(export_content, bytes) else export_content.encode('utf-8'), 'application/ndjson'),
        }

        
        headers = {'kbn-xsrf': 'true'}

        # First import the dashboard
        response = requests.post(url, files=files, params=params, auth=self.auth, headers=headers, verify=self.verify_ssl)
        
        if response.status_code != 200:
            raise Exception(f"Import failed: {response.text}")
        
        # Get the imported dashboard ID from the response
        import_result = response.json()

        source_data_view_id = self.get_data_view_id(target_space_id, source_data_view,headers)
        target_data_view_id = self.get_data_view_id(target_space_id, target_data_view,headers)
        
        # Now update the data view reference
        for success_item in import_result.get('successResults', []):
            if success_item['type'] == 'dashboard':
                dashboard_id = success_item['destinationId']
                update_url = f"{self.kibana_base_url}/s/{target_space_id}/api/saved_objects/dashboard/{dashboard_id}"
                
                # Get current dashboard configuration
                get_response = requests.get(update_url, auth=self.auth, 
                                          headers=self.headers, verify=self.verify_ssl)
                if get_response.status_code != 200:
                    raise Exception(f"Failed to get dashboard config: {get_response.text}")
                
                dashboard_config = get_response.json()
                
                # Update the data view reference in the dashboard attributes
                references = dashboard_config.get('references', [])
                updated = False

                for ref in references:
                    if ref.get('type') == 'index-pattern' and ref.get('id') == source_data_view_id:
                        ref['id'] = target_data_view_id
                        updated = True

                if updated:
                  update_payload = {
                      "attributes": dashboard_config['attributes'],
                      "references": references
                  }
                
                  update_response = requests.put(update_url, json=update_payload, 
                                            auth=self.auth, headers=self.headers, 
                                            verify=self.verify_ssl)
                
                  if update_response.status_code != 200:
                    raise Exception(f"Failed to update dashboard: {update_response.text}")
        
        self.delete_data_view(target_space_id, source_data_view_id)

        return import_result

    def get_data_view_id(self, space_id, data_view_name, headers):
        """
        Fetch the data view ID for a given name in a specific space
        """
        self.print_log(f"Fetching data view ID for {data_view_name} in space {space_id}")

        data_views_url = f"{self.kibana_base_url}/s/{space_id}/api/data_views"
    
        response = requests.get(data_views_url, auth=self.auth, headers=headers, verify=self.verify_ssl)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch index patterns: {response.text}")

        data_views = response.json().get('data_view', [])
        data_view_id = None

        for data_view in data_views:
            if data_view.get('name') == data_view_name:
                data_view_id = data_view["id"]
                break

        if not data_view_id:
            raise Exception(f"Source data view '{data_view_name}' not found in Kibana.")
        return data_view_id

    def copy_dashboard_between_spaces(self, dashboard_id, source_space_id, target_space_id, 
                                    source_data_view, target_data_view):
        """
        Copy a dashboard from one space to another and update its data view
        
        Args:
            dashboard_id (str): ID of the dashboard to copy
            source_space_id (str): Space ID where the dashboard currently exists
            target_space_id (str): Space ID where to copy the dashboard
            source_data_view (str): Original data view ID/name
            target_data_view (str): New data view ID/name to use
        """
        self.print_log(f"Copying dashboard {dashboard_id} from space {source_space_id} to {target_space_id} with data view update")

        try:
            export_content = self.export_dashboard(dashboard_id, source_space_id)
            
            result = self.import_dashboard(export_content, target_space_id, 
                                        source_data_view, target_data_view)
            
            return result
        except Exception as e:
            raise Exception(f"Failed to copy dashboard: {str(e)}")    
        
    def copy_dashboards(self, config_id, client_id):
        config_id = config_id
        client_id = client_id
        bi_client_name = f'client_{client_id}'
        bi_space_id = f'{bi_client_name}_space'
        bi_data_view_name = f'{bi_client_name}_data_view'

        if not config_id:
            return {"error": "No configuration selected"}

        config = Configuration.query.get(config_id)
        if not config:
            return {"error": "Configuration not found"}

        dashboard_ids = [
            "3a81edc6-40d2-435a-87a3-41ce352a523d",  # people_count_dashboard_id
            "5b898e8b-12e9-4638-acf3-34fea03e7b61",  # people_count_area_dashboard_id
            "e1f0588e-41fd-45b8-8160-e334b866f2f7"   # car_count_dashboard_id
        ]

        try:
          for source_dashboard_id in dashboard_ids:
              self.copy_dashboard_between_spaces(
                  dashboard_id=source_dashboard_id,
                  source_space_id="default",
                  target_space_id=bi_space_id,
                  source_data_view="DGuard Demo",
                  target_data_view=bi_data_view_name
              )
        except Exception as e:
            raise Exception(f"Failed to copy dashboard: {str(e)}")    

        return {"status": "success", "message": "Dashboards copied successfully"}
    
    def delete_data_view(self, space_id, data_view_id):
        self.print_log(f"Deleting data view {data_view_id} from space {space_id}")
        
        url = f"{self.kibana_base_url}/s/{space_id}/api/saved_objects/index-pattern/{data_view_id}"
        
        headers = {"kbn-xsrf": "true"}

        response = requests.delete(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        if response.status_code == 200:
            return {"status": "success", "message": "Data View deleted successfully"}
        else:
            return {"status": "error", "message": response.text}
        
    def print_log(self, message):
        print("\n" + "*" * (len(message) + 8))
        print(f"*   {message}   *")
        print("*" * (len(message) + 8) + "\n")

    def get_spaces(self):
        """
        Fetch all Kibana spaces.
        """
        url = f"{self.kibana_base_url}/api/spaces/space?include_authorized_purposes=true"
        headers = {
            "kbn-xsrf": "true"
        }

        
        response = requests.get(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": response.text}

    def get_roles(self):
        """
        Fetch all Kibana roles.
        """
        url = f"{self.kibana_base_url}/api/security/role"
        headers = {
            "kbn-xsrf": "true"
        }

        
        response = requests.get(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": response.text}
        
    def get_users(self):
        """
        Fetch all Elastic users.
        """
        url = f"{self.elastic_base_url}/_security/user"
        headers = {
            "kbn-xsrf": "true"
        }
        
        response = requests.get(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        if response.status_code == 200:
            users = response.json()
            return users
        else:
            return {"status": "error", "message": response.text}
        
    def get_dataviews(self):
        """
        Fetch all Kibana dataviews.
        """
        url = f"{self.kibana_base_url}/api/data_views"
        headers = {
            "kbn-xsrf": "true"
        }

        
        response = requests.get(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch dataviews: {response.text}")
        
    def delete_space(self, space_id):
        """
        Delete a space by id
        """
        self.print_log(f"Deleting space: {space_id}")

        url = f"{self.kibana_base_url}/api/spaces/space/{space_id}"
        
        headers = {"kbn-xsrf": "true"}

        response = requests.delete(url, headers=headers, auth=self.auth, verify=self.verify_ssl)
        
        if response.status_code == 200:
            return {"status": "success", "message": "Data View deleted successfully"}
        else:
                return {"status": "error", "message": response.text}
