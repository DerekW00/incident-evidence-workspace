from django.db import transaction
from django.utils import timezone
from .models import Investigation


def reserve(run_id: int, input_bytes: int, tool_count: int) -> None:
    with transaction.atomic():
        run = Investigation.objects.select_for_update().get(id=run_id)
        if run.status not in ["queued", "running"] or timezone.now() >= run.deadline:
            raise ValueError("Investigation terminal or deadline expired")
        if (
            run.steps >= 4
            or tool_count < 0
            or run.tools + tool_count > 8
            or not 0 <= input_bytes <= 32768
        ):
            raise ValueError("Investigation budget exceeded")
        run.steps += 1
        run.tools += tool_count
        run.guard_units += 2000
        run.save(update_fields=["steps", "tools", "guard_units"])
