import mimetypes
import os
from urllib.parse import quote, urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from config.error_handlers import json_error_response
from .forms import ContactForm
from .models import Activity, Category, Material, Tag
from .tile_images import tile_image_url


SORT_FIELDS = {"title", "-title", "created_at", "-created_at"}

# Fallback when mimetypes.guess_type is wrong or returns None (common cause of
# "open in new tab" downloading as attachment-like behavior).
_EXT_FALLBACK = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "bmp": "image/bmp",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "ogg": "video/ogg",
    "txt": "text/plain; charset=utf-8",
    "md": "text/plain; charset=utf-8",
    "csv": "text/csv; charset=utf-8",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
}


def _content_type_for_filename(name):
    """Prefer extension map (reliable); mimetypes alone often yields octet-stream + nosniff → download."""
    base = os.path.basename(name)
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
    if ext in _EXT_FALLBACK:
        return _EXT_FALLBACK[ext]
    ctype, _ = mimetypes.guess_type(base)
    if ctype and ctype != "application/octet-stream":
        return ctype
    return ctype or "application/octet-stream"


def _preview_kind_for_material(m):
    """Preview uses optional preview_pdf first, then the main file."""
    if m.preview_pdf:
        return "pdf"
    fname = m.file.name if m.file else ""
    return _preview_kind(fname)


def _preview_kind(file_field_name):
    """Return preview type for inline browser display."""
    if not file_field_name:
        return "none"
    ext = file_field_name.rsplit(".", 1)[-1].lower() if "." in file_field_name else ""
    if ext == "pdf":
        return "pdf"
    if ext in ("jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"):
        return "image"
    if ext in ("mp4", "webm", "ogg"):
        return "video"
    if ext in ("txt", "md", "csv"):
        return "text"
    # Word / Excel / PowerPoint: preview via Office Online when URL is public
    if ext in ("doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp"):
        return "office"
    return "none"


def _is_localhost_request(request):
    host = request.get_host().split(":")[0].lower()
    return host in ("localhost", "127.0.0.1", "[::1]")


def _material_dict(m, request):
    kind = _preview_kind_for_material(m)
    file_open_url = None
    file_download_url = None
    if m.preview_pdf or m.file:
        file_open_url = request.build_absolute_uri(
            reverse("activities:material_open", kwargs={"material_id": m.id})
        )
        file_download_url = request.build_absolute_uri(
            reverse("activities:material_download", kwargs={"material_id": m.id})
        )
    show_preview_button = kind in ("pdf", "image", "video", "text")
    d = {
        "id": m.id,
        "title": m.title,
        "material_type": m.get_material_type_display(),
        "material_type_key": m.material_type,
        "file_url": file_open_url,
        "file_open_url": file_open_url,
        "file_download_url": file_download_url,
        "uploaded_at": m.uploaded_at.isoformat(),
        "preview_kind": kind,
        "show_preview_button": show_preview_button,
        "has_preview_pdf": bool(m.preview_pdf),
    }
    # Office Online cannot fetch login-protected URLs (no session cookie). PDF preview is preferred.
    if kind == "office" and file_open_url:
        d["office_embed_src"] = quote(file_open_url, safe="")
        d["office_preview_blocked_local"] = _is_localhost_request(request)
        d["office_preview_blocked_auth"] = True
    else:
        d["office_embed_src"] = None
        d["office_preview_blocked_local"] = False
        d["office_preview_blocked_auth"] = False
    return d


def _serve_file_field(file_field, *, as_attachment):
    """Stream a FileField from disk."""
    if not file_field:
        raise Http404
    fs_path = file_field.path
    if not os.path.isfile(fs_path):
        raise Http404
    basename = os.path.basename(file_field.name)
    content_type = _content_type_for_filename(file_field.name)
    response = FileResponse(
        open(fs_path, "rb"),
        as_attachment=as_attachment,
        filename=basename,
        content_type=content_type,
    )
    if not as_attachment:
        response.headers["Content-Disposition"] = "inline"
    return response


def _serve_material_open(request, material_id):
    """Inline: prefer dedicated Preview (PDF), else main file."""
    m = get_object_or_404(Material, pk=material_id)
    if m.preview_pdf:
        return _serve_file_field(m.preview_pdf, as_attachment=False)
    if m.file:
        return _serve_file_field(m.file, as_attachment=False)
    raise Http404


def _serve_material_download(request, material_id):
    """Attachment: main file for download; if only preview PDF exists, offer that."""
    m = get_object_or_404(Material, pk=material_id)
    if m.file:
        return _serve_file_field(m.file, as_attachment=True)
    if m.preview_pdf:
        return _serve_file_field(m.preview_pdf, as_attachment=True)
    raise Http404


@login_required
@require_GET
def material_open(request, material_id):
    """Serve file with Content-Disposition: inline so browsers display PDF/images/video in-tab."""
    return _serve_material_open(request, material_id)


@login_required
@require_GET
def material_download(request, material_id):
    """Serve main file as download (or preview PDF only if no main file)."""
    return _serve_material_download(request, material_id)


@require_GET
def home(request):
    """Landing page describing the teaching activities platform."""
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def contact(request):
    """Contact page with a message form that emails CONTACT_EMAIL."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if form.is_spam():
                # Silently accept honeypot hits without sending.
                messages.success(request, "Thanks — your message has been sent.")
                return redirect("contact")
            data = form.cleaned_data
            subject = data.get("subject") or f"Contact from {data['name']}"
            body = (
                f"Name: {data['name']}\n"
                f"Email: {data['email']}\n\n"
                f"{data['message']}"
            )
            recipient = getattr(settings, "CONTACT_EMAIL", settings.DEFAULT_FROM_EMAIL)
            email = EmailMessage(
                subject=f"[TeachOrange] {subject}",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
                reply_to=[data["email"]],
            )
            try:
                email.send(fail_silently=False)
            except Exception:
                messages.error(
                    request,
                    "Sorry — we couldn't send your message right now. "
                    "Please email us directly at " + recipient + ".",
                )
            else:
                messages.success(
                    request, "Thanks — your message has been sent. We'll be in touch."
                )
                return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form})


@require_GET
def team(request):
    """Meet the team page."""
    return render(request, "team.html")


@require_GET
def consulting(request):
    """TeachOrange Consulting page."""
    return render(request, "consulting.html")


def _get_filtered_queryset(request):
    """Build filtered activity queryset from request params."""
    qs = Activity.objects.select_related("category").prefetch_related("tags", "materials")

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(tags__name__icontains=q)
        ).distinct()

    tag_name = request.GET.get("tag", "").strip()
    if tag_name:
        qs = qs.filter(tags__name__iexact=tag_name)

    category_id = request.GET.get("category", "").strip()
    if category_id:
        try:
            qs = qs.filter(category_id=int(category_id))
        except ValueError:
            return None, "Invalid category id."

    sort = request.GET.get("sort", "-created_at").strip()
    if sort in SORT_FIELDS:
        qs = qs.order_by(sort)
    else:
        qs = qs.order_by("-created_at")

    return qs, None


def _first_previewable(activity, request):
    """First material that can render inline (PDF/image) — used by the list popout."""
    for m in activity.materials.all():
        kind = _preview_kind_for_material(m)
        if kind in ("pdf", "image") and (m.preview_pdf or m.file):
            return {
                "open_url": request.build_absolute_uri(
                    reverse("activities:material_open", kwargs={"material_id": m.id})
                ),
                "kind": kind,
            }
    return None


@require_GET
def activity_list(request):
    """
    List activities with optional search, filters, pagination, and sorting.
    Returns HTML for browsers, JSON for API requests.
    """
    qs, err = _get_filtered_queryset(request)
    if err:
        return json_error_response(400, detail=err)

    # Pagination
    try:
        per_page = max(1, min(100, int(request.GET.get("limit", 20))))
    except ValueError:
        per_page = 20
    paginator = Paginator(qs, per_page)
    try:
        page_num = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page_num = 1
    page_obj = paginator.get_page(page_num)

    # HTML response
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        tags_qs = Tag.objects.order_by("name")
        tags = list(tags_qs)
        tag_param = request.GET.get("tag", "").strip()
        categories = list(Category.objects.order_by("name").values("id", "name", "description"))
        pagination_params = {k: v for k, v in request.GET.items() if k != "page"}
        pagination_base = urlencode(pagination_params) if pagination_params else ""
        # Query string without tag/page (preserve q, category, sort) — for clearing tag chips + banner link
        get_no_tag_no_page = request.GET.copy()
        get_no_tag_no_page.pop("page", None)
        get_no_tag_no_page.pop("tag", None)
        clear_tag_query = get_no_tag_no_page.urlencode()
        list_reverse = reverse("activities:list")
        if clear_tag_query:
            clear_tag_url = f"{list_reverse}?{clear_tag_query}"
        else:
            clear_tag_url = list_reverse
        active_tag_name = tag_param.lower() if tag_param else ""
        # Preserve other filters when clicking a tag on a card (reset page when tag changes)
        tag_apply_queries = {}
        for tag in tags:
            gb = request.GET.copy()
            gb.pop("page", None)
            gb["tag"] = tag.name
            tag_apply_queries[tag.name] = gb.urlencode()
        active_filtered_tag = None
        if tag_param:
            for tag in tags:
                if tag.name.lower() == tag_param.lower():
                    active_filtered_tag = tag
                    break
        has_active_filters = bool(
            request.GET.get("q", "").strip()
            or request.GET.get("category", "").strip()
            or request.GET.get("tag", "").strip()
            or (
                request.GET.get("sort", "").strip()
                and request.GET.get("sort") != "-created_at"
            )
        )
        activity_rows = [
            {
                "activity": a,
                "tile_image": tile_image_url(a),
                "preview": _first_previewable(a, request),
            }
            for a in page_obj.object_list
        ]
        return render(
            request,
            "activities/activity_list.html",
            {
                "activity_rows": activity_rows,
                "page_obj": page_obj,
                "total": paginator.count,
                "tags": tags,
                "tag_apply_queries": tag_apply_queries,
                "clear_tag_query": clear_tag_query,
                "clear_tag_url": clear_tag_url,
                "active_tag_name": active_tag_name,
                "active_filtered_tag": active_filtered_tag,
                "has_active_filters": has_active_filters,
                "categories": categories,
                "pagination_base": pagination_base,
            },
        )

    # JSON response
    activities = [
        {
            "id": a.id,
            "slug": a.slug,
            "title": a.title,
            "description": a.description,
            "category": a.category.name if a.category else None,
            "category_id": a.category_id,
            "tags": [t.name for t in a.tags.all()],
            "tags_display": [t.display_name for t in a.tags.all()],
            "created_at": a.created_at.isoformat(),
        }
        for a in page_obj.object_list
    ]
    return JsonResponse(
        {
            "activities": activities,
            "count": len(activities),
            "total": paginator.count,
            "page": page_obj.number,
            "limit": per_page,
        }
    )


@require_GET
def activity_detail(request, slug):
    """Retrieve a single activity by slug. Returns HTML or JSON."""
    activity = get_object_or_404(
        Activity.objects.select_related("category").prefetch_related("tags", "materials"),
        slug=slug,
    )

    materials = [_material_dict(m, request) for m in activity.materials.all()]

    # HTML response
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        return render(
            request,
            "activities/activity_detail.html",
            {"activity": activity, "materials": materials},
        )

    # JSON response
    return JsonResponse(
        {
            "id": activity.id,
            "slug": activity.slug,
            "title": activity.title,
            "description": activity.description,
            "category": activity.category.name if activity.category else None,
            "category_id": activity.category_id,
            "tags": [t.name for t in activity.tags.all()],
            "tags_display": [t.display_name for t in activity.tags.all()],
            "materials": materials,
            "created_at": activity.created_at.isoformat(),
            "updated_at": activity.updated_at.isoformat(),
        }
    )


@require_GET
def tag_list(request):
    """List all tags for filter dropdowns."""
    tags = [
        {"id": t.id, "name": t.name, "display_name": t.display_name}
        for t in Tag.objects.order_by("name")
    ]
    return JsonResponse({"tags": tags})


@require_GET
def category_list(request):
    """List all categories for filter dropdowns."""
    categories = Category.objects.order_by("name").values("id", "name", "description")
    return JsonResponse({"categories": list(categories)})
