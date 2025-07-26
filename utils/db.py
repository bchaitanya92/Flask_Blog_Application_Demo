from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# Initialize SQLAlchemy
db = SQLAlchemy()

# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def init_database(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

def reset_database(app):
    """Reset the database (drop all tables and recreate)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")

def seed_database(app):
    """Seed the database with sample data"""
    from models.blog import Author, Blog
    
    with app.app_context():
        # Check if data already exists
        if Author.query.first():
            print("Database already contains data. Skipping seed.")
            return
        
        try:
            # Create sample authors
            authors_data = [
                {
                    'name': 'Alice Johnson',
                    'email': 'alice@example.com',
                    'bio': 'A passionate writer and technology enthusiast with over 5 years of experience in web development.'
                },
                {
                    'name': 'Bob Smith',
                    'email': 'bob@example.com',
                    'bio': 'Creative writer and storyteller who loves sharing experiences and insights about life and technology.'
                },
                {
                    'name': 'Carol Davis',
                    'email': 'carol@example.com',
                    'bio': 'Professional blogger and content creator specializing in lifestyle and productivity topics.'
                }
            ]
            
            authors = []
            for author_data in authors_data:
                author = Author(**author_data)
                db.session.add(author)
                authors.append(author)
            
            db.session.commit()
            
            # Create sample blogs
            blogs_data = [
                {
                    'title': 'Getting Started with Flask Web Development',
                    'content': '''Flask is a lightweight and powerful web framework for Python that makes it easy to build web applications quickly. In this comprehensive guide, we'll explore the fundamentals of Flask development.

Flask follows the WSGI (Web Server Gateway Interface) standard and is built on the Werkzeug toolkit and Jinja2 templating engine. What makes Flask special is its simplicity and flexibility - it provides the essential tools you need without forcing you into a specific project structure or requiring many dependencies by default.

Getting started with Flask is straightforward. You can create a simple web application with just a few lines of code. The framework provides routing, templating, request handling, and session management out of the box. Whether you're building a small personal project or a large-scale application, Flask can adapt to your needs.''',
                    'date': '15-01-2024',
                    'author_id': 1,
                    'featured': True
                },
                {
                    'title': 'Modern Web Design Principles',
                    'content': '''Web design has evolved significantly over the past decade. Today's web designers must consider user experience, accessibility, performance, and mobile responsiveness as core principles.

Modern web design emphasizes clean, minimalist layouts that prioritize content and user interaction. The use of white space, typography, and color psychology plays a crucial role in creating engaging user experiences. Responsive design is no longer optional - it's essential for reaching users across all devices.

Key principles include mobile-first design, fast loading times, intuitive navigation, and accessible interfaces. Tools like CSS Grid and Flexbox have revolutionized how we approach layout design, making it easier to create complex, responsive layouts.''',
                    'date': '10-01-2024',
                    'author_id': 2,
                    'featured': True
                },
                {
                    'title': 'The Art of Creative Writing',
                    'content': '''Creative writing is a journey of self-expression and imagination. It's about finding your unique voice and sharing stories that resonate with readers. Whether you're writing fiction, poetry, or personal narratives, the fundamentals remain the same.

Developing your writing skills requires practice, patience, and persistence. Start by reading widely in your chosen genre. Pay attention to how successful authors craft their sentences, develop characters, and build tension. Keep a journal to capture ideas and observations from daily life.

The writing process involves multiple stages: brainstorming, drafting, revising, and editing. Don't expect perfection in your first draft. Good writing is rewriting. Set aside dedicated time for writing, create a comfortable workspace, and develop routines that support your creativity.''',
                    'date': '08-01-2024',
                    'author_id': 3
                },
                {
                    'title': 'Database Design Best Practices',
                    'content': '''Effective database design is crucial for building scalable and maintainable applications. A well-designed database ensures data integrity, optimal performance, and easy maintenance.

Start with understanding your data requirements. Identify entities, relationships, and constraints. Normalize your data to eliminate redundancy, but be mindful of over-normalization which can impact performance. Choose appropriate data types and set up proper indexing strategies.

Consider scalability from the beginning. Plan for data growth and query patterns. Use foreign key constraints to maintain referential integrity. Document your schema and establish clear naming conventions for consistency across your development team.''',
                    'date': '05-01-2024',
                    'author_id': 1
                },
                {
                    'title': 'Building Responsive User Interfaces',
                    'content': '''Creating responsive user interfaces that work seamlessly across all devices is a fundamental skill for modern web developers. The mobile-first approach has become the standard in contemporary web development.

CSS frameworks like Bootstrap and Tailwind CSS provide excellent starting points, but understanding the underlying principles is essential. Learn CSS Grid and Flexbox thoroughly - these layout systems give you powerful tools for creating flexible, responsive designs.

Consider performance implications of your design choices. Optimize images, minimize HTTP requests, and use efficient CSS selectors. Test your interfaces on real devices, not just browser dev tools. User experience should be consistent and intuitive regardless of screen size.''',
                    'date': '02-01-2024',
                    'author_id': 2
                },
                {
                    'title': 'Productivity Tips for Writers',
                    'content': '''Writing productivity isn't just about writing faster - it's about writing consistently and effectively. Developing good habits and systems can dramatically improve your output and quality.

Establish a regular writing schedule that works with your natural rhythms. Some writers are most creative in the early morning, while others prefer late-night sessions. Find your optimal time and protect it fiercely.

Use tools that support your workflow. Whether it's a simple text editor or a full-featured writing application, choose tools that don't distract from your creativity. Set realistic daily word count goals and track your progress. Celebrate small wins to maintain motivation over long projects.''',
                    'date': '28-12-2023',
                    'author_id': 3
                }
            ]
            
            for blog_data in blogs_data:
                blog = Blog(**blog_data)
                db.session.add(blog)
            
            db.session.commit()
            print("Database seeded with sample data successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {str(e)}")
            raise

def get_db_stats(app):
    """Get database statistics"""
    from models.blog import Author, Blog
    
    with app.app_context():
        stats = {
            'total_authors': Author.query.count(),
            'total_blogs': Blog.query.count(),
            'published_blogs': Blog.query.filter_by(published=True).count(),
            'featured_blogs': Blog.query.filter_by(featured=True).count(),
            'total_views': db.session.query(db.func.sum(Blog.view_count)).scalar() or 0,
            'total_likes': db.session.query(db.func.sum(Blog.like_count)).scalar() or 0
        }
        return stats

def backup_database(app, backup_path):
    """Create a backup of the database"""
    import shutil
    import os
    from datetime import datetime
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"blog_backup_{timestamp}.db"
            full_backup_path = os.path.join(backup_path, backup_filename)
            
            shutil.copy2(db_path, full_backup_path)
            print(f"Database backed up to: {full_backup_path}")
            return full_backup_path
        else:
            print("Database file not found!")
            return None

def restore_database(app, backup_file_path):
    """Restore database from backup"""
    import shutil
    import os
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if os.path.exists(backup_file_path):
            # Close all connections
            db.session.close()
            db.engine.dispose()
            
            # Replace current database with backup
            shutil.copy2(backup_file_path, db_path)
            print(f"Database restored from: {backup_file_path}")
            return True
        else:
            print("Backup file not found!")
            return False

# Database maintenance functions
def optimize_database(app):
    """Optimize database performance"""
    with app.app_context():
        try:
            # For SQLite, we can run VACUUM and ANALYZE
            db.engine.execute('VACUUM;')
            db.engine.execute('ANALYZE;')
            print("Database optimized successfully!")
        except Exception as e:
            print(f"Error optimizing database: {str(e)}")

def check_database_integrity(app):
    """Check database integrity"""
    with app.app_context():
        try:
            result = db.engine.execute('PRAGMA integrity_check;').fetchone()
            if result[0] == 'ok':
                print("Database integrity check passed!")
                return True
            else:
                print(f"Database integrity check failed: {result[0]}")
                return False
        except Exception as e:
            print(f"Error checking database integrity: {str(e)}")
            return False