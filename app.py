"""
UPI QR Code Generator API
-------------------------
Generates a QR code image that, when scanned, opens the user's UPI app
with payee, amount, and transaction note pre-filled.

Endpoint: GET /genqr/<upi_id>/<amount>?transaction_note=<note>
Response: PNG image of the QR code.
"""

import re
import qrcode
from io import BytesIO
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# Basic UPI ID validation pattern
UPI_REGEX = r'^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}$'


def validate_upi(upi_id: str) -> bool:
    """Check if the UPI ID has a valid format."""
    return re.match(UPI_REGEX, upi_id) is not None


def build_upi_uri(upi_id: str, amount: float, txn_note: str = None) -> str:
    """
    Construct a UPI deep link URI.
    Standard format: upi://pay?pa=<upi>&am=<amount>&cu=INR&tn=<note>
    """
    uri = f"upi://pay?pa={upi_id}&am={amount:.2f}&cu=INR"
    if txn_note:
        uri += f"&tn={txn_note}"
    return uri


@app.route('/genqr/<upi_id>/<amount>', methods=['GET'])
def generate_qr(upi_id: str, amount: str):
    """
    Generate a QR code for a UPI payment.

    Path parameters:
        upi_id  : UPI address (e.g., example@paytm)
        amount  : Payment amount (must be a positive number)

    Query parameters:
        transaction_note (optional) : Description for the transaction

    Returns:
        PNG image of the QR code.
    """
    # 1. Validate UPI ID
    if not validate_upi(upi_id):
        return jsonify({"error": "Invalid UPI ID format"}), 400

    # 2. Validate amount
    try:
        amt = float(amount)
        if amt <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Amount must be a positive number"}), 400

    # 3. Get optional transaction note from query string
    txn_note = request.args.get('transaction_note')

    # 4. Build the UPI URI
    upi_uri = build_upi_uri(upi_id, amt, txn_note)

    # 5. Generate QR code
    qr = qrcode.QRCode(
        version=1,                     # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low redundancy (enough for simple text)
        box_size=10,                   # Pixel size of each QR module
        border=4,                      # White border (in modules)
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)

    # Create image with black QR on white background – clean and mature
    img = qr.make_image(fill_color="black", back_color="white")

    # 6. Save image to an in-memory bytes buffer
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    # 7. Return the image as a PNG response
    return send_file(buf, mimetype='image/png')


if __name__ == '__main__':
    # Run the Flask development server
    # For production, use a WSGI server like Gunicorn or Waitress
    app.run(debug=True, host='0.0.0.0', port=5000)