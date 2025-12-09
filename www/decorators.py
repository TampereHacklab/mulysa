from django.contrib.auth.views import redirect_to_login


def self_or_staff_member_required(function):
    def wrapper(request, id, *args, **kwargs):

        if not request.user.is_staff and request.user.id != id:
            return redirect_to_login(request.path)

        return function(request, id, *args, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper


def instructor_or_staff_member_required(function):
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or not (getattr(user, "is_staff", False) or getattr(user, "is_instructor", False)):
            return redirect_to_login(request.path)
        return function(request, *args, **kwargs)

    wrapper.__doc__ = function.__doc__
    wrapper.__name__ = function.__name__
    return wrapper
