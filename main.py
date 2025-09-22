import sys
import urllib3
from  app import dashboardMigration

# Suppress only InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == "__main__":
    elastic_host="prod-mq.seventh.com.br"
    elastic_port="9200"
    kibana_host="prod-mq.seventh.com.br"
    kibana_port="5601"
    username=""
    password=""

    automation = dashboardMigration.ElasticAutomation(
        elastic_host=elastic_host,
        elastic_port=elastic_port,
        kibana_host=kibana_host,
        kibana_port=kibana_port,
        username=username,
        password=password,
        verify_ssl=False
    )

    # Check if client_id parameter exists in the command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "client_id":
        # If client_id is provided as an argument, use it instead of client_id
        if len(sys.argv) > 2:
            client_id = int(sys.argv[2])  # Use the next argument as client_id
        else:
            print("Please provide the client ID after 'client_id'")
            sys.exit(1)  # Exit if client ID is not provided after client_id
    else:
        # Default client_id if no client_id is provided
        client_id = 7777
        
    bi_client_name = f'client_{client_id}'
    bi_role_name = f'{bi_client_name}_role'
    bi_indice = "dguard-analytics-events-demo"
    bi_alias_name = f'{bi_client_name}_alias'
    bi_space_name = f'{bi_client_name}_space'
    bi_data_view_name = f'{bi_client_name}_data_view'

    # Create an index alias
    print(automation.create_index_alias(bi_indice, bi_alias_name, client_id))
    # print(automation.get_alias_structure(bi_alias_name))

    # # Create a space
    # print(automation.get_kibana_features())
    print(automation.create_space(bi_space_name, name=bi_client_name+" Space",description="Space for events analysis"))

    # # Create a role
    print(automation.create_role(role_name=bi_role_name,indice=bi_alias_name,space=bi_space_name))

    # # Create a user
    print(automation.create_user(username=bi_client_name, password=bi_client_name, roles=[bi_role_name]))

    # # Create a data view
    print(automation.create_data_view(space_id=bi_space_name, dataview_name=bi_data_view_name, index_pattern=bi_alias_name))

    # Copy a dashboard between spaces with different data views
    people_count_dashboard_id = "3a81edc6-40d2-435a-87a3-41ce352a523d"
    people_count_area_dashboard_id = "5b898e8b-12e9-4638-acf3-34fea03e7b61"
    car_count_dashboard_id = "e1f0588e-41fd-45b8-8160-e334b866f2f7"
    source_space_id = "default"
    target_space_id = bi_space_name
    source_data_view = "DGuard Demo"
    target_data_view = bi_data_view_name

    for source_dashboard_id in [people_count_dashboard_id, people_count_area_dashboard_id, car_count_dashboard_id]:
        print(automation.copy_dashboard_between_spaces(
            dashboard_id=source_dashboard_id,
            source_space_id=source_space_id,
            target_space_id=bi_space_name,
            source_data_view=source_data_view,
            target_data_view=bi_data_view_name
        ))
