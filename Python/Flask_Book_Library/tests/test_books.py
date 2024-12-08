import pytest
from Python.Flask_Book_Library.project.books.models import Book
from Python.Flask_Book_Library.project import db, app


@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory DB for testing
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.mark.parametrize(
    "name,author,year_published,book_type,status",
    [
        ("Title A", "Author XYZ", 2024, "Biography", "available"),
        ("Title B", "Author ABC", 2023, "Dictionary", "checked out"),
        ("A" * 64, "B" * 64, 2020, "D" * 20, "E" * 20),
    ],
)
def test_book_creation_valid_data(test_client, name, author, year_published, book_type, status):
    with app.app_context():
        book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
        db.session.add(book)
        db.session.commit()

        retrieved = Book.query.filter_by(name=name).first()
        assert retrieved is not None
        assert retrieved.name == name
        assert retrieved.author == author
        assert retrieved.year_published == year_published
        assert retrieved.book_type == book_type
        assert retrieved.status == status

def test_book_creation_default_status(test_client):
    with app.app_context():
        book = Book(name="Title", author="Author", year_published=2024, book_type="Unknown")
        db.session.add(book)
        db.session.commit()

        retrieved = Book.query.filter_by(name="Title").first()
        assert retrieved is not None
        assert retrieved.name == "Title"
        assert retrieved.author == "Author"
        assert retrieved.year_published == 2024
        assert retrieved.book_type == "Unknown"
        assert retrieved.status == "available"

def test_book_year_published_forward(test_client):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name="Title", author="Author", year_published=9999, book_type="Unknown")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name,author,year_published,book_type",
    [
        (None, "Author", 2024, "Unknown"),
        ("Title", None, 2024, "Unknown"),
        ("Title", "Author", None, "Unknown"),
        ("Title", "Author", 2024, None),
        (0, "Author", 2024, "Unknown"),
        ("Title", 0, 2024, "Unknown"),
        ("Title", "Author", "Twenty Twenty Four", "Unknown"),
        ("Title", "Author", 2024, 0),
    ],
)
def test_book_creation_invalid_data(test_client, name, author, year_published, book_type):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type)
            db.session.add(book)
            db.session.commit()

def test_invalid_book_duplicate_name(test_client):
    with app.app_context():
        book1 = Book(name="Unique", author="XYZ", year_published=2020, book_type="Biography")
        book2 = Book(name="Unique", author="ABC", year_published=2024, book_type="Dictionary")

        db.session.add(book1)
        db.session.commit()

        with pytest.raises(Exception):
            db.session.add(book2)
            db.session.commit()

@pytest.mark.parametrize(
    "name",
    [
        "-- or #",
        "\" OR 1 = 1 -- -",
        "'''''''''''UNION SELECT '2",
        "1' ORDER BY 1--+",
        "' UNION SELECT(columnname ) from tablename --",
        ",(select * from (select(sleep(10)))a)",
        "Test'; DROP TABLE books;--",
    ],
)
def test_sql_injection(test_client, name):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author="Author", year_published=2024, book_type="Biography")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name",
    [
        "\"-prompt(8)-\"",
        "'-prompt(8)-'",
        "<img/src/onerror=prompt(8)>",
        "<script\\x20type=\"text/javascript\">javascript:alert(1);</script>",
        "<script src=1 href=1 onerror=\"javascript:alert(1)\"</script>",
        "<script>alert('XSS');</script>",
    ],
)
def test_javascript_injection(test_client, name):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author="Author", year_published=2024, book_type="Biography")
            db.session.add(book)
            db.session.commit()

@pytest.mark.parametrize(
    "name,author,year_published,book_type,status",
    [
        ("A" * 1000, "Author", 2024, "Biography", "available"),
        ("A" * 1000000, "Author", 2024, "Biography", "available"),
        ("A" * 9999999, "Author", 2024, "Biography", "available"),
        ("Book", "B" * 1000, 2024, "Biography", "available"),
        ("Book", "B" * 1000000, 2024, "Biography", "available"),
        ("Book", "B" * 9999999, 2024, "Biography", "available"),
        ("Book", "Author", 0, "Biography", "available"),
        ("Book", "Author", 1000000, "Biography", "available"),
        ("Book", "Author", 9999999, "Biography", "available"),
        ("Book", "Author", 2024, "D" * 1000, "available"),
        ("Book", "Author", 2024, "D" * 1000000, "available"),
        ("Book", "Author", 2024, "D" * 9999999, "available"),
        ("Book", "Author", 2024, "Biography", "E" * 1000),
        ("Book", "Author", 2024, "Biography", "E" * 1000000),
        ("Book", "Author", 2024, "Biography", "E" * 9999999),
    ],
)
def test_extreme(test_client, name, author, year_published, book_type, status):
    with app.app_context():
        with pytest.raises(Exception):
            book = Book(name=name, author=author, year_published=year_published, book_type=book_type, status=status)
            db.session.add(book)
            db.session.commit()