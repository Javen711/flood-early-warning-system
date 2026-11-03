from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from alerts.models import Alert
from residents.models import Resident

from .forms import ResidentSignUpForm


class RoleAwareLoginView(LoginView):
    """Normal login, but residents land on their own page and officers on the dashboard."""

    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        user = self.request.user
        return reverse('portal') if user.is_resident else reverse('dashboard')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ResidentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account is ready. You will get alerts for your zone.")
            return redirect('portal')
    else:
        form = ResidentSignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def portal_view(request):
    """A resident's own page: their zone's current risk and recent alerts."""
    if not request.user.is_resident:
        return redirect('dashboard')

    resident = Resident.objects.filter(user=request.user).select_related('zone').first()
    context = {'resident': resident, 'zone': None, 'prediction': None, 'alerts': []}
    if resident:
        zone = resident.zone
        context.update({
            'zone': zone,
            'prediction': zone.latest_prediction(),
            'alerts': Alert.objects.filter(prediction__zone=zone).select_related('prediction')[:10],
        })
    return render(request, 'portal.html', context)
