import os
from app import app
import data_csv as data


if __name__ == '__main__':
    data.init()
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
