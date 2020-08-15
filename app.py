from flask import Flask, request, render_template, Response
import json
from base64 import b64encode
from PIL import Image, ImageChops
from urllib.request import urlopen
from io import BytesIO
from typing import Tuple, Dict
import sys
import os

import torch
import torchvision.transforms as transforms
import numpy as np
import cv2

PATH_TO_MODEL = "model_1e-4_4.pt"
GIT_REV = os.environ.get("GIT_REV", "unknown")[:8]
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


def write_image_to_data_url(image, format="png"):
    stream = BytesIO()
    image.save(stream, format)
    # stream.seek(0)
    enc = str(b64encode(stream.getbuffer()), "ascii")
    out = f'data:image/{format};base64,{enc}'
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


def process_image(im: Image.Image, downsample: bool) \
        -> Tuple[Image.Image, Tuple[int, int]]:
    # Convert color
    if im.mode != "RGB":
        im = im.convert("RGB")

    # Reduce the picture size to something reasonable
    if downsample and any(dim > 512 for dim in im.size):
        divisor = max(im.size) / 512
        # Lose fractional pixels if we have to
        resizedim = tuple(int(dim/divisor) for dim in im.size)
        restoredim = resizedim
        im = im.resize(resizedim)
    else:
        restoredim = im.size

    # Pad to multiple of 64
    pad = [(64 - (dim & 63)) & 63 for dim in im.size]
    if any(paddim > 0 for paddim in pad):
        newdim = tuple(dim+paddim for dim, paddim in zip(im.size, pad))
        impad = Image.new("RGB", newdim)
        impad.paste(im)
        im = impad

    return im, restoredim


def interpolate(im1: Image.Image, im2: Image.Image,
                t: float, downsample: bool) \
        -> Tuple[Image.Image, Dict[str, Image.Image]]:
    if im1.size != im2.size:
        raise ValueError("Image sizes don't match")

    # Both will be restored to the same size
    im1p, restoredim = process_image(im1, downsample)
    im2p, _ = process_image(im2, downsample)

    transform = transforms.Compose([
        transforms.ToTensor()
    ])

    im1t, im2t = [transform(x).unsqueeze(0).to("cpu") for x in (im1p, im2p)]

    with torch.no_grad():
        img_recon, flow_t_0, flow_t_1, w1, w2 = model(im1t, im2t, t)

    img_recon = img_recon.squeeze(0).numpy().transpose((1, 2, 0)) * 255
    img_recon = img_recon.astype(np.uint8)
    iminter = Image.fromarray(img_recon)

    extra = {
        "w1": weight_map_to_image(w1),
        "w2": weight_map_to_image(w2),
        "flow_t_0": flow_to_image(flow_t_0),
        "flow_t_1": flow_to_image(flow_t_1)
    }

    if iminter.size != restoredim:
        iminter = iminter.crop((0, 0, *restoredim))
        for k in extra:
            extra[k] = extra[k].crop((0, 0, *restoredim))

    return iminter, extra


@ app.route('/process', methods=["POST"])
def process():
    frame1 = parse_data_url_for_image(request.form['frame1'])
    frame2 = parse_data_url_for_image(request.form['frame2'])
    try:
        t = float(request.form['t'])
    except (ValueError, KeyError):
        t = 0.5

    try:
        downsample = request.form['downsample'] != "false"
    except (ValueError, KeyError):
        downsample = False

    try:
        outformat = str(request.form['outformat'])
    except (ValueError, KeyError):
        outformat = "png"

    try:
        frameinter, extra = interpolate(frame1, frame2, t, downsample)
    except ValueError as e:
        return {
            "message": f"Invalid frames: {e.args[0]}"
        }, 400
    except RuntimeError as e:
        return {
            "message": f"Model says: {e.args[0]}"
        }, 500

    return {
        "frameinter": write_image_to_data_url(frameinter, outformat),
        "extra": {k: write_image_to_data_url(v, outformat)
                  for k, v in extra.items()}
    }


@ app.route("/")
@ app.route("/index.html")
def index():
    return render_template("index.html",
                           GIT_REV=GIT_REV,
                           formats=["jpeg", "png"])


if __name__ == "__main__":
    app.run(debug=True)
