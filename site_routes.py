from flask import Blueprint, render_template

site_bp = Blueprint("site", __name__)

@site_bp.route("/")
def index():
    return render_template("index.html")

@site_bp.route("/for-job-seekers")
def job_seekers():
    return render_template("iexchange-jobseekers.html")

@site_bp.route("/for-employers")
def employers():
    return render_template("iexchange-employers.html")


@site_bp.route("/how-it-works")
def how_it_works():
    return render_template("iexchange-how-it-works.html")
