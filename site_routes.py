from flask import Blueprint, render_template

site_bp = Blueprint("site", __name__)

@site_bp.route("/")
def index():
    return render_template("index.html")