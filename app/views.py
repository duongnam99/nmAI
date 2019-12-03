from app import app
from flask import request, redirect, jsonify
from flask import render_template
from werkzeug.utils import secure_filename
import sys
import os
from pprint import pprint
import base64
import urllib.request
import json
# import cv2

import http.client
from cv2 import cv2
import numpy as np
from keras.models import load_model

app.config["IMAGE_STATIC"] = 'app/static/img/object_detected'
app.config["MODEL"] = 'app/core'
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

@app.route("/")
def index():
    return render_template("public/index.html")

@app.route("/about")
def about():
    return """
    <h1 style='color: red;'>I'm a red H1 heading!</h1>
    <p>This is a lovely little paragraph</p>
    <code>Flask is <em>awesome</em></code>
    """

def allowed_image(filename):
    
    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_image_filesize(filesize):

    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False


@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():
    
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            execution_path = os.getcwd()

            model_path = os.path.join(execution_path, app.config["MODEL"], 'model.h5')
            filename = secure_filename(image.filename)
            uploaded_path = os.path.join(execution_path, app.config["IMAGE_STATIC"], 'input', filename)
            image.save(uploaded_path)
            output_path_img_temp = os.path.join(execution_path, app.config["IMAGE_STATIC"], 'output', filename)


            model = load_model(model_path, compile = False)
            img = cv2.imread(uploaded_path)

            mapping = ['0', '1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            res_read = ''

            ret, thresh = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY_INV)

            contours, hier = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            sorted_ctrs = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[0])

            for i, crt in enumerate(sorted_ctrs):
                x, y, w, h = cv2.boundingRect(crt)
                if 500 > w > 10 and 500 > h > 50:
                    roi = img[y-20:y+h+20, x-20:x+w+20]
                    cv2.imwrite(output_path_img_temp, roi)
                    cropped_img = cv2.imread(output_path_img_temp, 0)
                    blur = cv2.GaussianBlur(cropped_img, (5, 5), 0)
                    ret3, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    th3 = cv2.subtract(255, th3)
                    pred_img = th3
                    pred_img = cv2.resize(pred_img, (28, 28))
                    pred_img = pred_img / 255.0
                    pred_img = pred_img.reshape(1, 784)
                    prediction = mapping[model.predict_classes(pred_img)[0]]
                    res_read = res_read + prediction
                    # cv2.imshow('charachter'+str(i), roi)
                    # cv2.waitKey(0)

            params = "/api/e_search?q=" + res_read

            connection = http.client.HTTPSConnection("nhqt-dict.herokuapp.com")
            connection.request("GET", params)

            req = connection.getresponse()
            # connection.close()

            # return("Status: {} and reason: {}".format(req.status, req.reason))
            # return json.loads(req.read())

            # query = {'q': res_read}
            # req = requests.get('https://nhqt-dict.herokuapp.com/api/check')
            # return req.text
            # rs = []
            # rs.append(req.read())
            # rs.append(res_read)
            # return req.read()
            data = {'result': req.read(),'read_text': res_read}
            return json.dumps(data)
        # return jsonify({
        #     'result': 'error',
        #     'read_text': ''}), 201   

    return render_template("public/upload_image.html")

   
