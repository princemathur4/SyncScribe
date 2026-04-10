"""
LiveDraft Database Seed Script
==============================
Creates all tables and populates them with initial data.

Run from the backend/ directory:
    python seed.py

To wipe and re-seed from scratch:
    python seed.py --reset
"""

import sys
import argparse
from sqlalchemy import text

# Import everything from the existing project code.
# These are not duplicated here - we reuse what is already defined.
from modules.database.postgres import engine, SessionLocal, Base
from modules.models import User, Page
from modules.routers.auth import hash_password  # reuse the existing hashing function


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_tables():
    """Create all tables defined in models.py via SQLAlchemy metadata."""
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("  Tables created.")


def drop_tables():
    """Drop all tables. Used when --reset flag is passed."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("  Tables dropped.")


def update_search_vector(page_id: int, db):
    """Update the tsvector column for a page after inserting it."""
    db.execute(text("""
        UPDATE pages
        SET search_vector = to_tsvector(
            'english',
            coalesce(title, '') || ' ' || coalesce(body, '')
        )
        WHERE id = :id
    """), {"id": page_id})


# ── Seed data ─────────────────────────────────────────────────────────────────

def seed(db):
    print("Seeding data...")

    # ── Users ─────────────────────────────────────────────────────────────────
    print("  Creating users...")

    alice = User(
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("password123"),
    )
    bob = User(
        username="bob",
        email="bob@example.com",
        password_hash=hash_password("password123"),
    )
    db.add_all([alice, bob])
    db.flush()  # flush so alice.id and bob.id are populated before use below

    print(f"    alice (id={alice.id})")
    print(f"    bob   (id={bob.id})")

    # ── Root pages ────────────────────────────────────────────────────────────
    # parent_id = None means these are top-level pages in the sidebar tree
    print("  Creating root pages...")

    engineering = Page(
        title="Engineering",
        slug="engineering",
        body=(
            "# Engineering\n\n"
            "Welcome to the Engineering wiki.\n\n"
            "This is the root page for all engineering documentation.\n\n"
            "## Sections\n\n"
            "- [[Backend]] - server, API, and database docs\n"
            "- [[Frontend]] - React, components, and styling docs\n"
        ),
        parent_id=None,
        created_by=alice.id,
        last_edited_by=alice.id,
    )
    product = Page(
        title="Product",
        slug="product",
        body=(
            "# Product\n\n"
            "Product roadmap, specs, and decisions live here.\n\n"
            "## Sections\n\n"
            "- [[Roadmap]] - what we are building next\n"
        ),
        parent_id=None,
        created_by=alice.id,
        last_edited_by=alice.id,
    )
    db.add_all([engineering, product])
    db.flush()

    print(f"    Engineering (id={engineering.id}, slug={engineering.slug})")
    print(f"    Product     (id={product.id}, slug={product.slug})")

    # ── Child pages of Engineering ─────────────────────────────────────────────
    print("  Creating child pages...")

    backend = Page(
        title="Backend",
        slug="backend",
        body=(
            "# Backend\n\n"
            "All backend documentation.\n\n"
            "## Stack\n\n"
            "- **Framework:** FastAPI\n"
            "- **Database:** PostgreSQL\n"
            "- **ORM:** SQLAlchemy\n\n"
            "## Sub-pages\n\n"
            "- [[API Guidelines]]\n"
            "- [[Database Schema]]\n"
        ),
        parent_id=engineering.id,
        created_by=alice.id,
        last_edited_by=alice.id,
    )
    frontend_page = Page(
        title="Frontend",
        slug="frontend",
        body=(
            "# Frontend\n\n"
            "All frontend documentation.\n\n"
            "## Stack\n\n"
            "- **Framework:** React + Vite\n"
            "- **Editor:** CodeMirror 6\n"
            "- **Real-time:** Yjs + y-websocket\n\n"
            "## Sub-pages\n\n"
            "- [[Component Guide]]\n"
        ),
        parent_id=engineering.id,
        created_by=alice.id,
        last_edited_by=bob.id,
    )
    db.add_all([backend, frontend_page])
    db.flush()

    print(f"    Backend  (id={backend.id}, parent=Engineering)")
    print(f"    Frontend (id={frontend_page.id}, parent=Engineering)")

    # ── Grandchild pages ───────────────────────────────────────────────────────
    # These are nested one level deeper (child of Backend or Frontend)

    api_guidelines = Page(
        title="API Guidelines",
        slug="api-guidelines",
        body=(
            "# API Guidelines\n\n"
            "Follow these conventions for all API endpoints.\n\n"
            "## REST Conventions\n\n"
            "- Use nouns for resource names, not verbs\n"
            "- Use plural nouns: `/pages` not `/page`\n"
            "- Use HTTP methods correctly: GET, POST, PUT, DELETE\n\n"
            "## Response Codes\n\n"
            "| Code | Meaning       |\n"
            "|------|---------------|\n"
            "| 200  | OK            |\n"
            "| 201  | Created       |\n"
            "| 400  | Bad request   |\n"
            "| 401  | Unauthorized  |\n"
            "| 404  | Not found     |\n"
            "| 500  | Server error  |\n\n"
            "## Auth\n\n"
            "All protected routes require a Bearer token:\n\n"
            "```\n"
            "Authorization: Bearer <your_token>\n"
            "```\n\n"
            "## Example\n\n"
            "```python\n"
            "@app.get('/pages/{slug}')\n"
            "async def get_page(slug: str, db: Session = Depends(get_db)):\n"
            "    page = db.query(Page).filter(Page.slug == slug).first()\n"
            "    if not page:\n"
            "        raise HTTPException(status_code=404, detail='Page not found')\n"
            "    return page\n"
            "```\n"
        ),
        parent_id=backend.id,
        created_by=alice.id,
        last_edited_by=alice.id,
    )
    db_schema = Page(
        title="Database Schema",
        slug="database-schema",
        body=(
            "# Database Schema\n\n"
            "## Tables\n\n"
            "### users\n\n"
            "| Column        | Type         | Notes              |\n"
            "|---------------|--------------|--------------------||\n"
            "| id            | SERIAL       | Primary key        |\n"
            "| username      | VARCHAR(50)  | Unique, indexed    |\n"
            "| email         | VARCHAR(255) | Unique             |\n"
            "| password_hash | VARCHAR(255) |                    |\n"
            "| created_at    | TIMESTAMPTZ  | Auto set           |\n\n"
            "### pages\n\n"
            "| Column          | Type         | Notes                        |\n"
            "|-----------------|--------------|------------------------------|\n"
            "| id              | SERIAL       | Primary key                  |\n"
            "| title           | VARCHAR(255) |                              |\n"
            "| slug            | VARCHAR(255) | Unique, used in URL + Yjs    |\n"
            "| body            | TEXT         | Raw markdown content         |\n"
            "| parent_id       | INTEGER      | FK to pages.id, nullable     |\n"
            "| created_by      | INTEGER      | FK to users.id               |\n"
            "| last_edited_by  | INTEGER      | FK to users.id               |\n"
            "| search_vector   | TSVECTOR     | Updated on save, GIN indexed |\n"
            "| created_at      | TIMESTAMPTZ  | Auto set                     |\n"
            "| updated_at      | TIMESTAMPTZ  | Auto updated                 |\n"
        ),
        parent_id=backend.id,
        created_by=bob.id,
        last_edited_by=bob.id,
    )
    component_guide = Page(
        title="Component Guide",
        slug="component-guide",
        body=(
            "# Component Guide\n\n"
            "## Naming Conventions\n\n"
            "- Use PascalCase for component files: `Editor.jsx`, `Sidebar.jsx`\n"
            "- Use camelCase for hook files: `useAuth.js`, `usePageTree.js`\n\n"
            "## File Structure\n\n"
            "```\n"
            "src/\n"
            "  components/   shared reusable components\n"
            "  pages/        route-level page components\n"
            "  context/      React context providers\n"
            "  hooks/        custom hooks\n"
            "```\n\n"
            "## Example Component\n\n"
            "```jsx\n"
            "function Button({ label, onClick, disabled = false }) {\n"
            "  return (\n"
            "    <button onClick={onClick} disabled={disabled}>\n"
            "      {label}\n"
            "    </button>\n"
            "  );\n"
            "}\n\n"
            "export default Button;\n"
            "```\n"
        ),
        parent_id=frontend_page.id,
        created_by=bob.id,
        last_edited_by=bob.id,
    )

    # Child of Product
    roadmap = Page(
        title="Roadmap",
        slug="roadmap",
        body=(
            "# Roadmap\n\n"
            "## Current Sprint\n\n"
            "- [x] Page CRUD\n"
            "- [x] Real-time collaboration with Yjs\n"
            "- [x] JWT authentication\n"
            "- [ ] Full-text search UI\n"
            "- [ ] Page permissions\n\n"
            "## Next Sprint\n\n"
            "- [ ] Version history\n"
            "- [ ] Image uploads\n"
            "- [ ] Dark mode\n"
        ),
        parent_id=product.id,
        created_by=alice.id,
        last_edited_by=alice.id,
    )

    db.add_all([api_guidelines, db_schema, component_guide, roadmap])
    db.flush()

    print(f"    API Guidelines   (id={api_guidelines.id}, parent=Backend)")
    print(f"    Database Schema  (id={db_schema.id}, parent=Backend)")
    print(f"    Component Guide  (id={component_guide.id}, parent=Frontend)")
    print(f"    Roadmap          (id={roadmap.id}, parent=Product)")

    # ── Update search vectors for all pages ───────────────────────────────────
    print("  Updating search vectors...")
    all_page_ids = [
        engineering.id, product.id,
        backend.id, frontend_page.id,
        api_guidelines.id, db_schema.id, component_guide.id, roadmap.id,
    ]
    for page_id in all_page_ids:
        update_search_vector(page_id, db)

    db.commit()
    print("  Search vectors updated.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LiveDraft database seed script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before recreating and seeding. WARNING: destroys all data.",
    )
    args = parser.parse_args()

    if args.reset:
        print("WARNING: --reset will delete all existing data.")
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)
        drop_tables()

    create_tables()

    db = SessionLocal()
    try:
        # Check if data already exists to avoid duplicate seed
        existing_users = db.query(User).count()
        if existing_users > 0 and not args.reset:
            print(f"Database already has {existing_users} user(s). Skipping seed.")
            print("Run with --reset to wipe and re-seed.")
            sys.exit(0)

        seed(db)

        print()
        print("Seed complete.")
        print()
        print("Credentials:")
        print("  alice / password123  (admin)")
        print("  bob   / password123  (editor)")
        print()
        print("Page tree:")
        print("  Engineering")
        print("    Backend")
        print("      API Guidelines")
        print("      Database Schema")
        print("    Frontend")
        print("      Component Guide")
        print("  Product")
        print("    Roadmap")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()