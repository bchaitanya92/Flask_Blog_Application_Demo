from utils.db import db
from datetime import datetime
import re

class Author(db.Model):
    """Author model for blog authors"""
    __tablename__ = 'authors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with blogs
    blogs = db.relationship('Blog', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, email, bio=None, avatar_url=None):
        self.name = name.strip()
        self.email = email.lower().strip()
        self.bio = bio.strip() if bio else None
        self.avatar_url = avatar_url
        
        # Validate email format
        if not self._validate_email(self.email):
            raise ValueError("Invalid email format")
    
    def _validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @property
    def blog_count(self):
        """Get the number of blogs by this author"""
        return len(self.blogs)
    
    @property
    def latest_blog(self):
        """Get the latest blog by this author"""
        return Blog.query.filter_by(author_id=self.id).order_by(Blog.id.desc()).first()
    
    @property
    def avatar_initial(self):
        """Get the first letter of author's name for avatar"""
        return self.name[0].upper() if self.name else 'A'
    
    def to_dict(self):
        """Convert author to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'blog_count': self.blog_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Author {self.name} ({self.email})>'


class Blog(db.Model):
    """Blog model for blog posts"""
    __tablename__ = 'blogs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)  # Stored as string in DD-MM-YYYY format
    slug = db.Column(db.String(250), unique=True, nullable=True, index=True)
    excerpt = db.Column(db.String(300), nullable=True)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    like_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationship
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False, index=True)
    
    def __init__(self, title, content, date, author_id, slug=None, excerpt=None, featured=False, published=True):
        self.title = title.strip()
        self.content = content.strip()
        self.date = date
        self.author_id = author_id
        self.slug = slug or self._generate_slug(title)
        self.excerpt = excerpt or self._generate_excerpt(content)
        self.featured = featured
        self.published = published
        
        # Validate required fields
        if not self.title:
            raise ValueError("Blog title is required")
        if not self.content:
            raise ValueError("Blog content is required")
        if len(self.title) < 5:
            raise ValueError("Blog title must be at least 5 characters long")
        if len(self.content) < 10:
            raise ValueError("Blog content must be at least 10 characters long")
    
    def _generate_slug(self, title):
        """Generate URL-friendly slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]  # Limit to 50 characters
    
    def _generate_excerpt(self, content):
        """Generate excerpt from content"""
        # Remove extra whitespace and get first 150 characters
        clean_content = ' '.join(content.split())
        if len(clean_content) <= 150:
            return clean_content
        
        # Try to break at sentence end
        excerpt = clean_content[:150]
        last_period = excerpt.rfind('.')
        last_exclamation = excerpt.rfind('!')
        last_question = excerpt.rfind('?')
        
        # Find the last sentence ending
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > 100:  # If we have a reasonable sentence break
            return excerpt[:last_sentence_end + 1]
        else:
            # Break at last space to avoid cutting words
            last_space = excerpt.rfind(' ')
            return excerpt[:last_space] + '...' if last_space > 0 else excerpt + '...'
    
    @property
    def formatted_date(self):
        """Get formatted date for display"""
        try:
            # Parse DD-MM-YYYY format
            day, month, year = self.date.split('-')
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%B %d, %Y')
        except:
            return self.date
    
    @property
    def date_object(self):
        """Convert string date to datetime object"""
        try:
            day, month, year = self.date.split('-')
            return datetime(int(year), int(month), int(day))
        except:
            return datetime.now()
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        # Average reading speed is about 200 words per minute
        word_count = len(self.content.split())
        reading_time = max(1, round(word_count / 200))
        return f"{reading_time} min read"
    
    @property
    def word_count(self):
        """Get word count of the blog content"""
        return len(self.content.split())
    
    @property
    def character_count(self):
        """Get character count of the blog content"""
        return len(self.content)
    
    @property
    def is_long_form(self):
        """Check if this is a long-form blog post (>1000 words)"""
        return self.word_count > 1000
    
    def increment_view_count(self):
        """Increment the view count"""
        self.view_count += 1
        db.session.commit()
    
    def increment_like_count(self):
        """Increment the like count"""
        self.like_count += 1
        db.session.commit()
    
    def decrement_like_count(self):
        """Decrement the like count"""
        if self.like_count > 0:
            self.like_count -= 1
            db.session.commit()
    
    def get_related_blogs(self, limit=3):
        """Get related blogs by the same author"""
        return Blog.query.filter(
            Blog.author_id == self.author_id,
            Blog.id != self.id,
            Blog.published == True
        ).order_by(Blog.created_at.desc()).limit(limit).all()
    
    def to_dict(self, include_content=True):
        """Convert blog to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'formatted_date': self.formatted_date,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'featured': self.featured,
            'published': self.published,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'word_count': self.word_count,
            'reading_time': self.reading_time,
            'author': self.author.to_dict() if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_content:
            data['content'] = self.content
        
        return data
    
    @staticmethod
    def get_featured_blogs(limit=3):
        """Get featured blog posts"""
        return Blog.query.filter_by(featured=True, published=True).order_by(Blog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_recent_blogs(limit=5):
        """Get recent blog posts"""
        return Blog.query.filter_by(published=True).order_by(Blog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_popular_blogs(limit=5):
        """Get popular blog posts based on view count"""
        return Blog.query.filter_by(published=True).order_by(Blog.view_count.desc()).limit(limit).all()
    
    @staticmethod
    def search_blogs(query, limit=None):
        """Search blogs by title, content, or author name"""
        search_query = Blog.query.join(Author).filter(
            db.or_(
                Blog.title.contains(query),
                Blog.content.contains(query),
                Author.name.contains(query)
            ),
            Blog.published == True
        ).order_by(Blog.created_at.desc())
        
        if limit:
            return search_query.limit(limit).all()
        return search_query.all()
    
    def __repr__(self):
        return f'<Blog "{self.title}" by {self.author.name if self.author else "Unknown"}>'


# Database event listeners
from sqlalchemy import event

@event.listens_for(Blog, 'before_update')
def blog_before_update(mapper, connection, target):
    """Update the updated_at timestamp before updating a blog"""
    target.updated_at = datetime.utcnow()

@event.listens_for(Author, 'before_update')
def author_before_update(mapper, connection, target):
    """Update the updated_at timestamp before updating an author"""
    target.updated_at = datetime.utcnow()

# Database constraints and indexes
db.Index('idx_blog_author_date', Blog.author_id, Blog.date)
db.Index('idx_blog_published_featured', Blog.published, Blog.featured)
db.Index('idx_blog_created_at', Blog.created_at.desc())