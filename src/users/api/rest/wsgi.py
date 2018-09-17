if __name__ == "__main__":
    import os
    os.environ['PRODUCCION'] = '1'
    from .main import app
    app.run()
