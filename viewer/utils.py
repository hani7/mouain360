import qrcode # type: ignore
from PIL import Image
from io import BytesIO

def generate_qr_code(url):
    """
    Generates a QR code for the given URL and returns it as an image in PNG format.
    """
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR Code
    img = qr.make_image(fill='black', back_color='white')

    # Save the image to a BytesIO object and return it
    img_byte_array = BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)  # Go to the start of the BytesIO object

    return img_byte_array
