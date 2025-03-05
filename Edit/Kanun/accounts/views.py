from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from .forms import RegisterForm, LoginForm
from django.contrib import messages
from chat import views
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")  # Success message
            if user.is_superuser:
                return redirect("admin:index")  # Redirect to admin panel if superuser
            else:
                return redirect("login")  # Redirect to login if normal user
        else:
            messages.error(request, "Registration failed. Please check the form and try again.")  # Error message
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


# Login view (using Django's built-in authentication view)
class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "login.html"

    def get_success_url(self):
        # Check if the user is superuser or normal user and redirect accordingly
        if self.request.user.is_superuser:
            return '/admin/'  # Redirect to the admin panel for superuser
        return '/dashboard/'  # Redirect to the dashboard for normal user

    def get_redirect_url(self):
        # This method will ensure that after login failure, the user is redirected back to the login page.
        return self.request.path  # Redirect back to the same page (login) on failure

class CustomLogoutView(LogoutView):
    next_page = 'login'
    pass
