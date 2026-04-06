from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from slugify import slugify as python_slugify

from ..database.postgres import get_db
from ..models import Page, User
from ..schemas import PageCreate, PageUpdate, PageOut, PageSearchResult, PageTreeNode
from ..api.deps import get_current_user
from ..services.pages import update_search_vector, ensure_unique_slug, build_tree

router = APIRouter(tags=["pages"])


@router.get("/pages/tree", response_model=list[PageTreeNode])
async def get_page_tree(db: Session = Depends(get_db)):
    """
    Returns all pages as a nested tree. Used by the sidebar.
    Root pages are at the top level. Children are nested inside their parent.
    """
    all_pages: list = db.query(Page).order_by(Page.title).all()
    return build_tree(all_pages)


@router.get("/pages/search", response_model=list[PageSearchResult])
async def search_pages(q: str, db: Session = Depends(get_db)):
    if not q.strip():
        return []

    results = db.execute(text("""
        SELECT
            p.title,
            p.slug,
            ts_headline(
                'english',
                p.body,
                plainto_tsquery('english', :query),
                'MaxWords=15, MinWords=5, StartSel=<mark>, StopSel=</mark>'
            ) as snippet
        FROM pages p
        WHERE p.search_vector @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(p.search_vector, plainto_tsquery('english', :query)) DESC
        LIMIT 20
    """), {"query": q}).fetchall()

    return [
        PageSearchResult(title=r.title, slug=r.slug, snippet=r.snippet)
        for r in results
    ]


@router.get("/pages", response_model=list[PageOut])
async def list_pages(db: Session = Depends(get_db)):
    return db.query(Page).order_by(Page.updated_at.desc()).all()


@router.get("/pages/{slug}", response_model=PageOut)
async def get_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/pages", response_model=PageOut)
async def create_page(
        payload: PageCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    # Validate parent exists if provided
    if payload.parent_id:
        parent = db.query(Page).filter(Page.id == payload.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent page not found")

    base_slug = python_slugify(payload.title)
    slug = await ensure_unique_slug(base_slug, db)

    page = Page(
        title=payload.title,
        slug=slug,
        body=payload.body,
        parent_id=payload.parent_id,
        created_by=current_user.id,
        last_edited_by=current_user.id,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    await update_search_vector(page.id, db)
    return page


@router.put("/pages/{slug}", response_model=PageOut)
async def update_page(
        slug: str,
        payload: PageUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if payload.title is not None:
        page.title = payload.title
        new_slug = python_slugify(payload.title)
        page.slug = await ensure_unique_slug(new_slug, db, exclude_id=page.id)

    if payload.body is not None:
        page.body = payload.body

    # Allow explicitly setting parent_id to null (move to root)
    # or to a new parent id
    if "parent_id" in payload.model_fields_set:
        if payload.parent_id:
            # Prevent circular references: a page cannot be its own ancestor
            if payload.parent_id == page.id:
                raise HTTPException(status_code=400, detail="A page cannot be its own parent")
            parent = db.query(Page).filter(Page.id == payload.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent page not found")
        page.parent_id = payload.parent_id

    page.last_edited_by = current_user.id

    db.commit()
    db.refresh(page)
    await update_search_vector(page.id, db)
    return page


@router.delete("/pages/{slug}")
async def delete_page(
        slug: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    db.delete(page)
    db.commit()
    return {"status": "deleted", "slug": slug}
