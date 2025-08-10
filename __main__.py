from app import app
import data_csv as data


if __name__ == '__main__':
    data.init()
    app.run(host="0.0.0.0", port=5000, debug=True)