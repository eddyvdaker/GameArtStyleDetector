import os
import base64
import imghdr

import numpy as np
from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from secrets import token_urlsafe
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image as tf_image

app = Flask(__name__)
app.config["SECRET_KEY"] = token_urlsafe()


MODELS_FOLDER = "./models"
MODEL = "v8-noslice-biggerkernels2"
IMAGE_FOLDER = "./images"
IMG_TARGET_SIZE = (224, 224)

if not os.path.exists(IMAGE_FOLDER):
    os.mkdir(IMAGE_FOLDER)

model = load_model(os.path.join(MODELS_FOLDER, MODEL))


def predict(img_id: str) -> str:
    img = tf_image.load_img(
        os.path.join(IMAGE_FOLDER, img_id), target_size=IMG_TARGET_SIZE
    )
    img = tf_image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    pred = model.predict(img)[0]
    if pred[0] > pred[1]:
        new_img_name = f"P-{str(pred[0])}-{img_id}"
    else:
        new_img_name = f"O-{str(pred[1])}-{img_id}"
    os.rename(
        os.path.join(IMAGE_FOLDER, img_id), os.path.join(IMAGE_FOLDER, new_img_name)
    )
    return new_img_name


class UploadForm(FlaskForm):
    image = FileField(
        "Select game screenshot",
        validators=[
            FileRequired(),
            FileAllowed(("jpg", "jpeg", "png"), "Must be jpg, jpeg or png file"),
        ],
    )
    submit = SubmitField("Detect!")


class ConfirmForm(FlaskForm):
    confirmation = SelectField(
        "Is this prediction correct?",
        validators=[DataRequired()],
        choices=[("yes", "yes"), ("no", "no")],
    )
    submit = SubmitField("Confirm")


@app.route("/", methods=["GET", "POST"])
def home():
    form = UploadForm()
    if form.validate_on_submit():
        img_id = token_urlsafe()
        form.image.data.save(os.path.join(IMAGE_FOLDER, img_id))
        new_image_name = predict(img_id)
        return redirect(url_for("confirm", img_id=new_image_name))
    return render_template("index.html", form=form)


@app.route("/confirm/<img_id>", methods=["GET", "POST"])
def confirm(img_id: str):
    form = ConfirmForm()
    show_form = not (img_id.endswith("-C") or img_id.endswith("-I"))
    if form.validate_on_submit() and show_form:
        show_form = False
        old_img_id = img_id
        if form.confirmation.data == "yes":
            img_id = f"{img_id}-C"
        else:
            img_id = f"{img_id}-I"
        os.rename(
            os.path.join(IMAGE_FOLDER, old_img_id),
            os.path.join(IMAGE_FOLDER, f"{img_id}"),
        )
    if img_id.startswith("P"):
        style = "PIXEL"
    else:
        style = "OTHER"
    percent = float(img_id.split("-")[1])
    img_path = os.path.join(IMAGE_FOLDER, img_id)
    img_type = imghdr.what(img_path)
    with open(os.path.join(IMAGE_FOLDER, img_id), "rb") as image_file:
        base64_img = base64.b64encode(image_file.read()).decode()
    return render_template(
        "confirm.html",
        form=form,
        show_form=show_form,
        style=style,
        percent=percent * 100,
        img=f"data:image/{img_type};base64,{base64_img}",
    )


if __name__ == "__main__":
    app.run()
