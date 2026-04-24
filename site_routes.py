from flask import Blueprint, render_template
import json
import os

site_bp = Blueprint("site", __name__)

def get_articles():
    """Read blogs.json and return list of articles."""
    blogs_file = os.path.join(os.path.dirname(__file__), "blogs.json")
    if not os.path.exists(blogs_file):
        return []
    with open(blogs_file, "r", encoding="utf-8") as f:
        return json.load(f)



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

@site_bp.route("/blog")
def blog_2():
    articles = get_articles()
    return render_template("iexchange-blog.html", articles=articles)

@site_bp.route("/blog/ai-matching")
def blog_ai_matching_2():
    return render_template("../blogs/blog-ai-matching.html")

@site_bp.route("/blog/9-country-expansion")
def blog_page_9_country_expansion():
    return render_template("../blogs/blog-9-country-expansion.html")

@site_bp.route("/about")
def about():
    return render_template("iexchange-about.html")

@site_bp.route("/blog/skill-gap-navigator")
def blog_skill_gap_navigator():
    return render_template("../blogs/blog-skill-gap-navigator.html")

@site_bp.route("/blog")
def blog():
    articles = get_articles()
    return render_template("iexchange-blog.html", articles=articles)
