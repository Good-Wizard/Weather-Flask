from flask import Flask, request, abort, jsonify, render_template
import requests
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_folder='static')

# Constants for Weather API
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
API_KEY = "8ec6af652686cbe5b7b800002c8fba1a"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a file handler and set the format
file_handler = RotatingFileHandler('api_logs.log', maxBytes=10000, backupCount=1, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - IP: %(ip)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def validate_response_data(data):
    """Validate the weather data response from the API."""
    if "main" not in data or "weather" not in data:
        abort(500, description="Invalid weather data format")

@app.before_request
def log_request_info():
    """Log request information before handling the request."""
    logger.info('Request Headers: %s', request.headers, extra={'ip': request.remote_addr})

@app.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@app.route('/weather')
def weather():
    """
    Fetch weather data for a given city and return it as JSON.
    
    :return: JSON response with weather data
    """
    city = request.args.get('city')
    units = request.args.get('units', 'metric')
    
    if not city:
        abort(400, description="City parameter is required")

    try:
        params = {"q": city, "appid": API_KEY, "units": units}
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        
        weather_data = response.json()
        validate_response_data(weather_data)

        data = {
            'city': city,
            'weather_description': weather_data['weather'][0]['description'],
            'temperature': weather_data['main']['temp'],
            'humidity': weather_data['main']['humidity'],
            'wind_speed': weather_data['wind']['speed'],
            'pressure': weather_data['main']['pressure'],
            'weather_icon': weather_data['weather'][0]['icon']
        }
        
        app.logger.info("Weather data fetched successfully for city: %s", city, extra={'ip': request.remote_addr})
        return jsonify(data)

    except requests.exceptions.HTTPError as e:
        logger.error("HTTP Error occurred: %s", e, extra={'ip': request.remote_addr})
        if response.status_code == 404:
            abort(404, description="City not found")
        else:
            abort(response.status_code, description="HTTP Error")
    
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection Error occurred: %s", e, extra={'ip': request.remote_addr})
        abort(500, description="Failed to connect to weather service")
    
    except requests.exceptions.Timeout as e:
        logger.error("Request Timeout occurred: %s", e, extra={'ip': request.remote_addr})
        abort(500, description="Request to weather service timed out")
    
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e, extra={'ip': request.remote_addr})
        abort(500, description="An unexpected error occurred")

    logger.error("Unexpected response from API: %s", response.text, extra={'ip': request.remote_addr})
    abort(500, description="Unexpected response from weather service")

if __name__ == "__main__":
    context = ('C:/ssl/cert.pem', 'C:/ssl/key.pem')
    app.run(debug=True, ssl_context=context)
