from django import template

register = template.Library()


@register.simple_tag
def page_window(page_obj, paginator, window: int = 2):
    current = int(getattr(page_obj, "number", 1))
    last = int(getattr(paginator, "num_pages", 1))
    window = int(window)

    if last <= 1:
        return [1]

    left = max(1, current - window)
    right = min(last, current + window)

    pages = [1]

    if left > 2:
        pages.append(None)

    for p in range(left, right + 1):
        if p not in (1, last):
            pages.append(p)

    if right < last - 1:
        pages.append(None)

    if last > 1:
        pages.append(last)

    return pages