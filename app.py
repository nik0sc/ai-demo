from flask import Flask, request, render_template
import json
from base64 import b64encode
from PIL import Image, ImageChops
from urllib.request import urlopen
from io import BytesIO

app = Flask(__name__)


def parse_data_url_for_image(url):
    with urlopen(url) as r:
        data = r.file.read()
        # mimetype = r.info()["Content-Type"]
        image = Image.open(BytesIO(data))
        # closes BytesIO
        image.load()
        return image


def write_image_to_data_url(image):
    stream = BytesIO()
    image.save(stream, "png")
    # stream.seek(0)
    enc = str(b64encode(stream.getbuffer()), "ascii")
    out = f'data:image/png;base64,{enc}'
    stream.close()
    return out


def interpolate(im1, im2):
    # Check image dimensions match
    # Pad to multiple of 8 each axis
    # Other normalising actions as needed
    # Send through interpolation model
    # Create image and return
    return ImageChops.difference(im1, im2)


@app.route('/process', methods=["POST"])
def process():
    frame1 = parse_data_url_for_image(request.form['frame1'])
    frame2 = parse_data_url_for_image(request.form['frame2'])

    frameinter = interpolate(frame1, frame2)

    return {
        "frameinter": write_image_to_data_url(frameinter),
        "info": {}
    }


@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
