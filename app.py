from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from pygments import lexers
from pygments.util import ClassNotFound
import string
import random

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model for storing text
class TextSnippet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    unique_id = db.Column(db.String(6), unique=True, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

# Generate unique ID (6 characters long)
def generate_unique_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get text and duration from user
        content = request.form['content']
        
        # Set default expiry to 48 hours
        expiry_time = datetime.now() + timedelta(hours=48)

        # Generate unique ID
        unique_id = generate_unique_id()
        
        # Save to database
        snippet = TextSnippet(content=content, expiry_time=expiry_time, unique_id=unique_id)
        db.session.add(snippet)
        db.session.commit()
        
        # Redirect to the unique link
        return redirect(url_for('view_text', unique_id=unique_id))
    
    return render_template('index.html')

@app.route('/<unique_id>')
def view_text(unique_id):
    # Retrieve snippet by unique_id
    snippet = TextSnippet.query.filter_by(unique_id=unique_id).first()

    # Check if snippet exists and is not expired
    if snippet and snippet.expiry_time > datetime.now():
        return render_template('view.html', content=snippet.content, unique_id=unique_id)
    else:
        # Handle expired or non-existent snippet
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return "Text not found or expired.", 404

# Cleanup expired entries (can be scheduled with a cron job or manually triggered)
@app.route('/cleanup')
def cleanup():
    now = datetime.now()
    expired = TextSnippet.query.filter(TextSnippet.expiry_time < now).all()
    for snippet in expired:
        db.session.delete(snippet)
    db.session.commit()
    return f"Deleted {len(expired)} expired snippets."

if __name__ == '__main__':
    app.run(debug=True)

