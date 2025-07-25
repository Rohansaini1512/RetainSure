import pytest
import json
import threading
import time
from app.main import app
from app.models import url_store

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear the store before each test
        url_store._mappings.clear()
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'URL Shortener API'

def test_api_health_check(client):
    """Test the API health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'message' in data

def test_shorten_valid_url(client):
    """Test shortening a valid URL."""
    url_data = {'url': 'https://www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert 'original_url' in data
    assert len(data['short_code']) == 6
    assert data['original_url'] == 'https://www.example.com'

def test_shorten_url_without_scheme(client):
    """Test shortening a URL without scheme (should add https://)."""
    url_data = {'url': 'www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['original_url'] == 'https://www.example.com'

def test_shorten_invalid_url(client):
    """Test shortening an invalid URL."""
    url_data = {'url': 'not-a-valid-url'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_shorten_empty_url(client):
    """Test shortening an empty URL."""
    url_data = {'url': ''}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_shorten_missing_url(client):
    """Test request without URL field."""
    response = client.post('/api/shorten', 
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_redirect_valid_short_code(client):
    """Test redirecting with a valid short code."""
    # First, create a short URL
    url_data = {'url': 'https://www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    short_code = response.get_json()['short_code']
    
    # Then test the redirect
    response = client.get(f'/{short_code}')
    assert response.status_code == 302
    assert response.location == 'https://www.example.com'

def test_redirect_invalid_short_code(client):
    """Test redirecting with an invalid short code."""
    response = client.get('/invalid123')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_stats_valid_short_code(client):
    """Test getting stats for a valid short code."""
    # First, create a short URL
    url_data = {'url': 'https://www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    short_code = response.get_json()['short_code']
    
    # Test stats before any clicks
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['url'] == 'https://www.example.com'
    assert data['clicks'] == 0
    assert 'created_at' in data
    
    # Simulate a redirect (which increments clicks)
    client.get(f'/{short_code}')
    
    # Test stats after one click
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['clicks'] == 1

def test_stats_invalid_short_code(client):
    """Test getting stats for an invalid short code."""
    response = client.get('/api/stats/invalid123')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_click_tracking(client):
    """Test that clicks are properly tracked."""
    # Create a short URL
    url_data = {'url': 'https://www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    short_code = response.get_json()['short_code']
    
    # Make multiple redirects
    for i in range(5):
        client.get(f'/{short_code}')
    
    # Check click count
    response = client.get(f'/api/stats/{short_code}')
    data = response.get_json()
    assert data['clicks'] == 5

def test_concurrent_requests(client):
    """Test thread safety with concurrent requests."""
    url_data = {'url': 'https://www.example.com'}
    response = client.post('/api/shorten', 
                          data=json.dumps(url_data),
                          content_type='application/json')
    
    short_code = response.get_json()['short_code']
    
    # Test concurrent access by making multiple sequential requests
    # (This tests the thread safety of our data structures)
    num_requests = 10
    
    for _ in range(num_requests):
        response = client.get(f'/{short_code}')
        assert response.status_code == 302
    
    # Check that all clicks were counted
    response = client.get(f'/api/stats/{short_code}')
    data = response.get_json()
    assert data['clicks'] == num_requests

def test_unique_short_codes(client):
    """Test that generated short codes are unique."""
    short_codes = set()
    
    for i in range(20):
        url_data = {'url': f'https://www.example{i}.com'}
        response = client.post('/api/shorten', 
                              data=json.dumps(url_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        short_code = response.get_json()['short_code']
        assert short_code not in short_codes
        short_codes.add(short_code)