from flask import Flask, request, render_template, Response
import json
from base64 import b64encode
from PIL import Image, ImageChops
from urllib.request import urlopen
from io import BytesIO
from typing import Tuple, Dict
import sys

import torch
import torchvision.transforms as transforms
import numpy as np
import cv2

PATH_TO_MODEL = "model_1e-4_4.pt"
app = Flask(__name__)

# Load model once and be done with it
sys.path.insert(0, "model/")
model = torch.load(PATH_TO_MODEL, map_location="cpu")


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


def flow_to_image(flow: torch.Tensor) -> Image.Image:
    flow = flow.squeeze(0).numpy().transpose((1, 2, 0))
    hsv = np.zeros((flow.shape[0], flow.shape[1], 3), dtype=np.uint8)
    hsv[..., 1] = 255
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return Image.fromarray(bgr)


def weight_map_to_image(w: torch.Tensor) -> Image.Image:
    w = w.squeeze().numpy()
    return Image.fromarray((w * 255).astype(np.uint8), 'L')


def interpolate(im1: Image.Image, im2: Image.Image, t: float) -> Tuple[Image.Image, Dict[str, Image.Image]]:
    # Check image dimensions match
    # Pad to multiple of 8 each axis
    # Other normalising actions as needed
    # Send through interpolation model
    # Create image and return
    if im1.size != im2.size:
        raise ValueError("Image sizes don't match")

    if im1.size[0] & 64 != 0:
        # pad = 8 - (im1.size[0] & 8)
        raise ValueError("Dim 1 error")

    if im1.size[1] & 64 != 0:
        raise ValueError("Dim 2 error")

    # May be slow, consider cached loading
    transform = transforms.Compose([
        transforms.ToTensor()
    ])

    im1t, im2t = [transform(x).unsqueeze(0).to("cpu") for x in (im1, im2)]

    with torch.no_grad():
        img_recon, flow_t_0, flow_t_1, w1, w2 = model(im1t, im2t, t)

    img_recon = img_recon.squeeze(0).numpy().transpose((1, 2, 0)) * 255
    img_recon = img_recon.astype(np.uint8)
    iminter = Image.fromarray(img_recon)

    return iminter, {
        "w1": weight_map_to_image(w1),
        "w2": weight_map_to_image(w2),
        "flow_t_0": flow_to_image(flow_t_0),
        "flow_t_1": flow_to_image(flow_t_1)
    }


@ app.route('/process', methods=["POST"])
def process():
    frame1 = parse_data_url_for_image(request.form['frame1'])
    frame2 = parse_data_url_for_image(request.form['frame2'])
    try:
        t = float(request.form['t'])
    except (ValueError, KeyError):
        t = 0.5

    try:
        frameinter, extra = interpolate(frame1, frame2, t)
    except ValueError as e:
        return Response({
            "message": f"Invalid frames: {e.args[0]}"
        }, 400)
    except RuntimeError as e:
        return Response({
            "message": f"Model says: {e.args[0]}"
        }, 500)

    return {
        "frameinter": write_image_to_data_url(frameinter),
        "extra": {k: write_image_to_data_url(v) for k, v in extra.items()}
    }


@ app.route("/")
@ app.route("/index.html")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
