from app import app
import data_csv as data


if __name__ == '__main__':
    data.init()
    app.run(debug=True)