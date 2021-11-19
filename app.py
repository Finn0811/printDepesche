import base64
import pdfkit
import tempfile
from flask import Flask
from flask import request
from flask import jsonify

# This import won't work on windows ;)
import cups

# Installation
#
# $ apt install cups libcups2-dev wkhtmltopdf python3 python3-pip python3-dev
# $ python3 -m venv .venv
# $ source .venv/bin/activate
# $ pip3 install pycups
# $ pip3 install pdfkit
# $ pip3 install Flask
#
# Update to wkhtmltopdf with patched QT
# apt-get remove --purge wkhtmltopdf
# apt-get install openssl build-essential xorg libssl-dev
# wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.raspbian.stretch_armhf.deb
# dpkg -i wkhtmltox_0.12.5-1.raspbian.stretch_armhf.deb
#


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config.from_object('config')


def print_pdf(pdf_file, copies):
    conn = cups.Connection()
    conn.printFile(app.config["PRINTER"], pdf_file, "Alarmdepesche", {"copies": str(copies)})


@app.route('/')
def index():
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_names = list(printers.keys())

    return jsonify({
        'availablePrinters': printer_names,
        'chosenPrinter': app.config['PRINTER']
    })


@app.route('/print', methods=['GET', 'POST'])
def print_depesche():
    if request.method == 'GET':
        return jsonify({"status": "NOK", "message": "Unsupported request method."})

    if request.method == 'POST':
        if "html" not in request.json:
            return jsonify({"status": "NOK", "message": "Missing html key in request JSON."})

        print("Received printing request.")

        html_data = base64.b64decode(request.json['html'])

        amount = app.config["COPIES"]
        if "amount" in request.json:
            if request.json['amount'] > 0:
                amount = request.json['amount']

        # print(request.json)
        # with open('alarmdepesche.html', 'w') as file:
        #     file.write(html_data.decode("utf8"))
        # print(html_data.decode("utf8"))

        # config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
        config = pdfkit.configuration()

        options = {
            'dpi': 365,
            'page-size': 'A4',
            'margin-top': '0.25in',
            'margin-right': '0.25in',
            'margin-bottom': '0.25in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'no-outline': None,
        }

        pdf = pdfkit.from_string(html_data.decode("utf8"), False, configuration=config)

        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".pdf", delete=False) as tempFile:
            tempFile.write(pdf)
            print_pdf(tempFile.name, amount)

        print("Finished printing request.")

        return jsonify({"status": "OK", "message": "Printing job successfully started."})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
