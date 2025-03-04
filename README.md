# Elastic Dashboard Migration Tool

The **Elastic Dashboard Migration Tool** is a Flask-based web application designed to automate the migration and management of Elasticsearch and Kibana configurations, including spaces, roles, users, data views, and dashboards. This tool simplifies the process of setting up and managing multi-tenant environments in Elasticsearch and Kibana by providing a user-friendly interface and RESTful API endpoints.

---

## Features

- **User Authentication**: Secure login and registration system with Flask-Login.
- **Configuration Management**: Create, update, and delete Elasticsearch and Kibana configurations.
- **Automation Tasks**:
  - Create index aliases.
  - Create Kibana spaces.
  - Define roles with specific permissions.
  - Create users and assign roles.
  - Create data views for Kibana.
  - Copy dashboards between spaces.
- **RESTful API**: Perform operations programmatically via API endpoints.
- **Role-Based Access Control**: Ensure only authenticated users can perform actions.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Flask
- Flask-Login
- SQLAlchemy
- Elasticsearch and Kibana instances

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/elastic-dashboard-migration-tool.git
   cd elastic-dashboard-migration-tool
