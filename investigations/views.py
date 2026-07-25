from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Membership, Incident, Investigation
from .forms import StartForm, ReviewForm
from .jobs import start_investigation, cancel
from .reviews import save_review
from .timeline import build_timeline
from .tools import Scope


def organization(request):
    return get_object_or_404(Membership, user=request.user).org_id


def owned(request, pk):
    return get_object_or_404(Investigation, id=pk, org_id=organization(request))


@login_required
def index(request):
    org = organization(request)
    return render(
        request,
        "investigations/index.html",
        {
            "incidents": Incident.objects.filter(service__org_id=org),
            "runs": Investigation.objects.filter(org_id=org).order_by("-id")[:30],
        },
    )


@login_required
def incident(request, pk):
    item = get_object_or_404(Incident, id=pk, service__org_id=organization(request))
    rows = item.evidence_set.order_by("at")
    first, last = rows.first(), rows.last()
    initial = {
        "start": first.at if first is not None else None,
        "end": last.at if last is not None else None,
    }
    form = StartForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            run = start_investigation(
                organization(request), item.id, request.user.id, **form.cleaned_data
            )
            return redirect("run", pk=run.id)
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(
        request, "investigations/incident.html", {"incident": item, "form": form}
    )


@login_required
def detail(request, pk):
    run = owned(request, pk)
    timeline = build_timeline(Scope(run.org_id, run.incident_id, run.start, run.end))
    form = ReviewForm(initial={"revision": run.revision})
    return render(
        request,
        "investigations/run.html",
        {"run": run, "timeline": timeline, "form": form},
    )


@login_required
def events(request, pk):
    run = owned(request, pk)
    return render(request, "investigations/events.html", {"run": run})


@login_required
@require_POST
def cancel_view(request, pk):
    run = owned(request, pk)
    cancel(run.org_id, run.id)
    return redirect("run", pk=pk)


@login_required
@require_POST
def review(request, pk):
    run = owned(request, pk)
    form = ReviewForm(request.POST)
    if form.is_valid():
        try:
            save_review(run.org_id, run.id, request.user.id, **form.cleaned_data)
            return redirect("run", pk=pk)
        except ValueError as exc:
            return HttpResponse(str(exc), status=409, content_type="text/plain")
    return HttpResponse("Invalid review", status=400)


@login_required
def brief(request, pk):
    run = owned(request, pk)
    item = get_object_or_404(run.briefs.order_by("-id"))
    response = HttpResponse(item.text, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = (
        'attachment; filename="synthetic-incident-brief.txt"'
    )
    return response
