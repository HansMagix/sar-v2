from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode is True in DevelopmentConfig, which is default
    app.run(host='127.0.0.1', port=5000, debug=True)
