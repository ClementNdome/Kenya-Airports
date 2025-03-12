# Kenya Airports Web GIS Application

## Project Overview
This project is a Web GIS application developed using Django and GeoDjango to visualize and analyze airports and airstrips in Kenya. The application connects to a spatial database (PostgreSQL + PostGIS) and provides various GIS functionalities, including spatial queries and proximity analysis.

## Features
### GIS Functions and Analysis Implemented
1. **Display and Visualization**
   - Displays all airports and airstrips on an interactive web map.
2. **Search by Runway Length**
   - Allows users to search and display airports or airstrips with a runway length of more than 1,500 meters.
3. **Search by Proximity to Equator**
   - Identifies and displays airports or airstrips located within 50 km of the equator.
4. **Nearest Airport Recommendation**
   - Recommends the closest airport or airstrip for passengers traveling from Kakamega to Nairobi using GIS proximity analysis.
5. **Additional Spatial Analysis**
   - Any other spatial analysis feature implemented to enhance the application.

## Technologies Used
- **Backend:** Django, GeoDjango
- **Frontend:** HTML, CSS, JavaScript (Leaflet for maps)
- **Database:** PostgreSQL with PostGIS extension
- **GIS Libraries:** GDAL, GeoDjango ORM, Leaflet.js

## Installation & Setup
### Prerequisites
Ensure you have the following installed:
- Python (>=3.8)
- PostgreSQL + PostGIS
- GDAL
- Django (>=4.0)
- GeoDjango dependencies

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/ClementNdome/Kenya-Airports.git
   cd Kenya-Airports
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up PostgreSQL and PostGIS:
   - Create a database in PostgreSQL
   - Enable the PostGIS extension:
     ```sql
     CREATE EXTENSION postgis;
     ```
   - Update `settings.py` with your database credentials.

5. Run migrations:
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Load spatial data:
   ```sh
   python manage.py loaddata airports.json  # Example dataset
   ```
7. Start the development server:
   ```sh
   python manage.py runserver
   ```
8. Open the application in a web browser:
   ```
   http://127.0.0.1:8000/
   ```

## Live Demo
This application is hosted live at Render:
[Kenya Airports Web GIS](https://kenya-airports.onrender.com/)

## Usage
- Use the interactive map to view and analyze airport locations.
- Perform spatial queries using the search functionalities.
- View recommendations for the closest airports for specific travel routes.

## Repository
The source code is available on GitHub:
[Kenya Airports Web GIS](https://github.com/ClementNdome/Kenya-Airports.git)

## License
This project is licensed under the MIT License.

## Contact
For inquiries, you can reach out via [GitHub Issues](https://github.com/ClementNdome/Kenya-Airports/issues).

