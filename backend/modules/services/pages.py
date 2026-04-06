from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Page
from ..schemas import PageTreeNode


async def ensure_unique_slug(base_slug: str, db: Session, exclude_id: int = None) -> str:
    slug = base_slug
    counter = 1
    while True:
        query = db.query(Page).filter(Page.slug == slug)
        if exclude_id:
            query = query.filter(Page.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


async def update_search_vector(page_id: int, db: Session):
    db.execute(text("""
        UPDATE pages
        SET search_vector = to_tsvector(
            'english',
            coalesce(title, '') || ' ' || coalesce(body, '')
        )
        WHERE id = :id
    """), {"id": page_id})
    db.commit()


def build_tree(pages: list[Page]) -> list[PageTreeNode]:
    """
    Convert a flat list of all pages into a nested tree structure.

    Strategy:
      1. Build a dict of id -> PageTreeNode for every page.
      2. Walk the list: if a page has a parent_id, attach it to its parent's
         children list. If no parent_id, it is a root node.
      3. Return only the root nodes. Their children are already nested inside.

    This runs in O(n) time - one pass through the list.
    """
    node_map: dict[int, PageTreeNode] = {}
    roots: list[PageTreeNode] = []

    # First pass: create a node for every page
    for page in pages:
        node_map[page.id] = PageTreeNode(
            id=page.id,
            title=page.title,
            slug=page.slug,
            parent_id=page.parent_id,
            children=[],
        )

    # Second pass: attach each node to its parent or to the root list
    for page in pages:
        node = node_map[page.id]
        if page.parent_id and page.parent_id in node_map:
            node_map[page.parent_id].children.append(node)
        else:
            # parent_id is null OR parent does not exist: treat as root
            roots.append(node)

    return roots

