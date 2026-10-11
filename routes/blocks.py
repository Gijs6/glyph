from flask import Blueprint, abort, flash, redirect, request, url_for

from models import Block, Page, db
from utils.blocks import BLOCK_TYPES, default_data, extract_data

blocks_bp = Blueprint("blocks", __name__, url_prefix="/pages/<page_id>/blocks")


def _back_to(page_id, block_id=None):
    url = url_for("pages.edit_page", page_id=page_id)
    if block_id:
        url = f"{url}?open={block_id}#block-{block_id}"
    return url


@blocks_bp.post("/")
def add_block(page_id):
    Page.query.get_or_404(page_id)

    block_type = request.form.get("type")
    if block_type not in BLOCK_TYPES:
        abort(400)

    next_position = (
        db.session.query(db.func.max(Block.position))
        .filter(Block.page_id == page_id)
        .scalar()
        or 0
    ) + 1
    block = Block(
        page_id=page_id,
        type=block_type,
        position=next_position,
        data=default_data(block_type),
    )
    db.session.add(block)
    db.session.commit()

    flash(f"{BLOCK_TYPES[block_type]['label']} block added.", "success")
    return redirect(_back_to(page_id, block.id), code=303)


@blocks_bp.put("/<block_id>")
def update_block(page_id, block_id):
    block = Block.query.filter_by(id=block_id, page_id=page_id).first_or_404()
    block.data = extract_data(block.type, request.form)
    db.session.commit()

    flash("Block saved.", "success")
    return redirect(_back_to(page_id, block.id), code=303)


@blocks_bp.delete("/<block_id>")
def delete_block(page_id, block_id):
    block = Block.query.filter_by(id=block_id, page_id=page_id).first_or_404()
    db.session.delete(block)
    db.session.commit()

    flash("Block deleted.", "success")
    return redirect(_back_to(page_id), code=303)


@blocks_bp.post("/<block_id>/move")
def move_block(page_id, block_id):
    direction = request.form.get("direction")
    blocks = list(Block.query.filter_by(page_id=page_id).order_by(Block.position.asc()))
    index = next((i for i, b in enumerate(blocks) if b.id == block_id), None)

    if index is not None:
        swap_with = index - 1 if direction == "up" else index + 1
        if 0 <= swap_with < len(blocks):
            blocks[index].position, blocks[swap_with].position = (
                blocks[swap_with].position,
                blocks[index].position,
            )
            db.session.commit()

    return redirect(_back_to(page_id, block_id), code=303)
