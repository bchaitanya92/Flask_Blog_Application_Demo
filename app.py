from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from utils.db import db
from models.blog import Blog, Author
import os
from datetime import datetime
import re

# Create Flask application
flask_app = Flask(__name__)

# Configuration
flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
flask_app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Initialize database
db.init_app(flask_app)

# Create database tables
with flask_app.app_context():
    db.create_all()

# Template filters and functions
@flask_app.template_filter('formatdate')
def format_date(date_string):
    """Format date string for better display"""
    try:
        if isinstance(date_string, str):
            # Try different date formats
            for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    return date_obj.strftime('%B %d, %Y')
                except ValueError:
                    continue
        return date_string
    except:
        return date_string

@flask_app.template_global()
def moment():
    """Provide moment-like functionality for templates"""
    return datetime.now()

# Helper functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_date(date_string):
    """Validate and format date"""
    try:
        # Try different date formats
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
            try:
                date_obj = datetime.strptime(date_string, fmt)
                return date_obj.strftime('%d-%m-%Y')
            except ValueError:
                continue
        return None
    except:
        return None

# Routes
@flask_app.route('/')
def index():
    """Home page with featured content"""
    try:
        # Get recent blogs for featured section
        recent_blogs = Blog.query.order_by(Blog.id.desc()).limit(3).all()
        return render_template('index.html', recent_blogs=recent_blogs)
    except Exception as e:
        flask_app.logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html', recent_blogs=[])

@flask_app.route('/about')
def about():
    """About page"""
    try:
        # Get some stats for the about page
        total_blogs = Blog.query.count()
        total_authors = db.session.query(Author.id).distinct().count()
        
        stats = {
            'total_blogs': total_blogs,
            'total_authors': total_authors,
            'total_views': total_blogs * 150,  # Simulated view count
            'total_likes': total_blogs * 75    # Simulated like count
        }
        
        return render_template('about.html', stats=stats)
    except Exception as e:
        flask_app.logger.error(f"Error in about route: {str(e)}")
        return render_template('about.html', stats={})

@flask_app.route('/blogs')
def blogs():
    """Display all blogs with sorting and filtering options"""
    try:
        # Get sorting parameter
        sort_by = request.args.get('sort', 'newest')
        search = request.args.get('search', '').strip()
        
        # Base query
        query = Blog.query
        
        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Blog.title.contains(search),
                    Blog.content.contains(search),
                    Blog.author.has(Author.name.contains(search))
                )
            )
        
        # Apply sorting
        if sort_by == 'oldest':
            query = query.order_by(Blog.id.asc())
        elif sort_by == 'title':
            query = query.order_by(Blog.title.asc())
        elif sort_by == 'author':
            query = query.join(Author).order_by(Author.name.asc())
        else:  # newest (default)
            query = query.order_by(Blog.id.desc())
        
        blogs_list = query.all()
        
        # If it's an AJAX request, return JSON
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'blogs': [{
                    'id': blog.id,
                    'title': blog.title,
                    'content': blog.content,
                    'date': blog.date,
                    'author': blog.author.name
                } for blog in blogs_list]
            })
        
        return render_template('blogs.html', blogs=blogs_list, search=search, sort_by=sort_by)
        
    except Exception as e:
        flask_app.logger.error(f"Error in blogs route: {str(e)}")
        flash('An error occurred while loading blogs.', 'error')
        return render_template('blogs.html', blogs=[])

@flask_app.route('/add_blog', methods=['GET', 'POST'])
def add_blog():
    """Add a new blog post"""
    if request.method == 'POST':
        try:
            # Get form data
            author_name = request.form.get('author_name', '').strip()
            author_email = request.form.get('author_email', '').strip()
            blog_title = request.form.get('blog_title', '').strip()
            blog_content = request.form.get('blog_content', '').strip()
            blog_date = request.form.get('blog_date', '').strip()
            
            # Validation
            errors = []
            
            if not author_name:
                errors.append('Author name is required.')
            elif len(author_name) < 2:
                errors.append('Author name must be at least 2 characters long.')
            
            if not author_email:
                errors.append('Author email is required.')
            elif not validate_email(author_email):
                errors.append('Please provide a valid email address.')
            
            if not blog_title:
                errors.append('Blog title is required.')
            elif len(blog_title) < 5:
                errors.append('Blog title must be at least 5 characters long.')
            
            if not blog_content:
                errors.append('Blog content is required.')
            elif len(blog_content) < 10:
                errors.append('Blog content must be at least 10 characters long.')
            
            if not blog_date:
                errors.append('Publication date is required.')
            else:
                formatted_date = validate_date(blog_date)
                if not formatted_date:
                    errors.append('Please provide a valid date.')
                else:
                    blog_date = formatted_date
            
            # If there are validation errors, show them
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('add_blog.html')
            
            # Check if author exists, if not create new author
            author = Author.query.filter_by(email=author_email).first()
            
            if not author:
                # Create new author
                author = Author(name=author_name, email=author_email)
                db.session.add(author)
                db.session.commit()
            else:
                # Update author name if different
                if author.name != author_name:
                    author.name = author_name
                    db.session.commit()
            
            # Create new blog post
            new_blog = Blog(
                title=blog_title,
                content=blog_content,
                date=blog_date,
                author_id=author.id
            )
            
            db.session.add(new_blog)
            db.session.commit()
            
            flash(f'Blog "{blog_title}" has been published successfully!', 'success')
            return redirect(url_for('blogs'))
            
        except Exception as e:
            db.session.rollback()
            flask_app.logger.error(f"Error adding blog: {str(e)}")
            flash('An error occurred while publishing your blog. Please try again.', 'error')
            return render_template('add_blog.html')
    
    # GET request - show the form
    return render_template('add_blog.html')

@flask_app.route('/blog/<int:blog_id>')
def view_blog(blog_id):
    """View a specific blog post"""
    try:
        blog = Blog.query.get_or_404(blog_id)
        
        # Get related blogs by the same author
        related_blogs = Blog.query.filter(
            Blog.author_id == blog.author_id,
            Blog.id != blog_id
        ).limit(3).all()
        
        return render_template('view_blog.html', blog=blog, related_blogs=related_blogs)
        
    except Exception as e:
        flask_app.logger.error(f"Error viewing blog {blog_id}: {str(e)}")
        flash('Blog not found.', 'error')
        return redirect(url_for('blogs'))

@flask_app.route('/author/<int:author_id>')
def view_author(author_id):
    """View all blogs by a specific author"""
    try:
        author = Author.query.get_or_404(author_id)
        author_blogs = Blog.query.filter_by(author_id=author_id).order_by(Blog.id.desc()).all()
        
        return render_template('author_blogs.html', author=author, blogs=author_blogs)
        
    except Exception as e:
        flask_app.logger.error(f"Error viewing author {author_id}: {str(e)}")
        flash('Author not found.', 'error')
        return redirect(url_for('blogs'))

@flask_app.route('/api/blogs')
def api_blogs():
    """API endpoint for blogs"""
    try:
        blogs = Blog.query.order_by(Blog.id.desc()).all()
        return jsonify({
            'success': True,
            'blogs': [{
                'id': blog.id,
                'title': blog.title,
                'content': blog.content[:200] + '...' if len(blog.content) > 200 else blog.content,
                'date': blog.date,
                'author': {
                    'id': blog.author.id,
                    'name': blog.author.name,
                    'email': blog.author.email
                }
            } for blog in blogs]
        })
    except Exception as e:
        flask_app.logger.error(f"Error in API blogs: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to fetch blogs'}), 500

@flask_app.route('/search')
def search_blogs():
    """Search blogs"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return redirect(url_for('blogs'))
        
        # Search in title, content, and author name
        blogs = Blog.query.filter(
            db.or_(
                Blog.title.contains(query),
                Blog.content.contains(query),
                Blog.author.has(Author.name.contains(query))
            )
        ).order_by(Blog.id.desc()).all()
        
        return render_template('blogs.html', blogs=blogs, search=query)
        
    except Exception as e:
        flask_app.logger.error(f"Error searching blogs: {str(e)}")
        flash('An error occurred during search.', 'error')
        return redirect(url_for('blogs'))

# Error handlers
@flask_app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@flask_app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

@flask_app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return render_template('errors/403.html'), 403

# Context processors
@flask_app.context_processor
def inject_global_vars():
    """Inject global variables into templates"""
    return {
        'current_year': datetime.now().year,
        'app_name': 'Blog App',
        'version': '2.0'
    }

# Template filters
@flask_app.template_filter('truncate_words')
def truncate_words(text, length=20):
    """Truncate text by word count"""
    words = text.split()
    if len(words) <= length:
        return text
    return ' '.join(words[:length]) + '...'

# CLI Commands
@flask_app.cli.command()
def init_db():
    """Initialize the database with sample data"""
    try:
        # Create tables
        db.create_all()
        
        # Create sample author
        sample_author = Author(
            name="John Doe",
            email="john@example.com"
        )
        db.session.add(sample_author)
        db.session.commit()
        
        # Create sample blog
        sample_blog = Blog(
            title="Welcome to Our Blog",
            content="This is a sample blog post to demonstrate the features of our blogging platform. You can write amazing stories, share your thoughts, and connect with readers from around the world.",
            date="01-01-2024",
            author_id=sample_author.id
        )
        db.session.add(sample_blog)
        db.session.commit()
        
        print("Database initialized with sample data!")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    # Development server configuration
    flask_app.run(
        host='127.0.0.1',
        port=8004,
        debug=True,
        use_reloader=True,
        threaded=True
    )