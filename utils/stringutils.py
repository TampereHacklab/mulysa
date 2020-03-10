from django.utils.html import strip_tags


def strip_tags_and_whitespace(s: str):
    """
    helper method for removing html tags and minimizing whitespace
    and empty lines
    """
    # strip html tags
    s = strip_tags(s)

    # strip every line. lstrip will remove the newline on "empty" lines also
    s = "".join([l.lstrip() for l in s.splitlines(True)])

    # strip the last newline if it exists
    s = s.rstrip()

    return s
