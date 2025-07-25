from flask import Flask, jsonify, request, redirect, url_for
from .models import url_store
from .utils import is_valid_url, generate_unique_short_code, normalize_url

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """
    Shorten a URL endpoint.
    
    Expects JSON: {"url": "https://example.com"}
    Returns: {"short_code": "abc123", "short_url": "http://localhost:5000/abc123"}
    """
    try:
        print("Starting URL shortening process...")
        
        # Get JSON data
        data = request.get_json(force=True)  # force=True parses JSON even if content-type is not application/json
        
        if not data:
            print("ERROR: No JSON data found!")
            return jsonify({
                'error': 'No JSON data in request body',
                'message': 'Please provide a JSON request with Content-Type: application/json'
            }), 400
            
        if 'url' not in data:
            print("ERROR: 'url' key not found in JSON data!")
            return jsonify({
                'error': 'Missing URL in request body',
                'message': 'Please provide a URL in JSON format: {"url": "https://example.com"}'
            }), 400
        
        original_url = data['url'].strip()
        print(f"Original URL: {original_url}")
        
        # Validate URL
        if not original_url:
            return jsonify({
                'error': 'Empty URL provided',
                'message': 'URL cannot be empty'
            }), 400
            
        # Normalize URL (add https:// if missing scheme)
        normalized_url = normalize_url(original_url)
        
        if not is_valid_url(normalized_url):
            return jsonify({
                'error': 'Invalid URL format',
                'message': 'Please provide a valid URL (e.g., https://example.com)'
            }), 400
            
        # Generate unique short code
        short_code = generate_unique_short_code(url_store.exists)
        if not short_code:
            return jsonify({
                'error': 'Failed to generate unique short code',
                'message': 'Please try again'
            }), 500
            
        print(f"Generated short code: {short_code}")
        # Store the mapping
        mapping = url_store.add_mapping(normalized_url, short_code)
        
        # Build short URL
        short_url = request.host_url + short_code
        
        return jsonify({
            'short_code': short_code,
            'short_url': short_url,
            'original_url': normalized_url
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """
    Redirect to the original URL using the short code.
    
    Args:
        short_code: The short code to redirect
        
    Returns:
        Redirect to original URL or 404 if not found
    """
    mapping = url_store.get_mapping(short_code)
    
    if not mapping:
        return jsonify({
            'error': 'Short code not found',
            'message': f'The short code "{short_code}" does not exist'
        }), 404
    
    # Increment click count
    mapping.increment_clicks()
    
    # Redirect to original URL
    return redirect(mapping.original_url)

@app.route('/api/stats/<short_code>')
def get_url_stats(short_code):
    """
    Get analytics for a short code.
    
    Args:
        short_code: The short code to get stats for
        
    Returns:
        JSON with URL, clicks, and creation timestamp
    """
    mapping = url_store.get_mapping(short_code)
    
    if not mapping:
        return jsonify({
            'error': 'Short code not found',
            'message': f'The short code "{short_code}" does not exist'
        }), 404
    
    return jsonify(mapping.to_dict()), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)