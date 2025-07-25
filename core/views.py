from . import models
from django.views import generic
from django.contrib.auth.views import LoginView as Login
from django.contrib.auth.views import LogoutView as logout
from . import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from project import models as project_models
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from .permissions import role_required
from experiment.models import ExperimentRequest, ExperimentApproval
from project.models import ProjectLayer
from datetime import datetime, timedelta
from django.utils import timezone
from django.urls import reverse, NoReverseMatch
# Create your views here.

class LoginView(Login):
    redirect_authenticated_user = True
    template_name = "core/login.html"
    def get_success_url(self):
        return "/"

class LogoutView(logout):
    template_name = "core/logout.html"
    

class HomeView(LoginRequiredMixin,generic.ListView):
    template_name = "core/home.html"
    model = project_models.Project
    
    def get_queryset(self):
        return self.model.objects.all().order_by('-updated_at')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_projects'] = self.get_queryset()
        
        # محاسبه وضعیت کلی پروژه‌ها
        total_projects = self.model.objects.count()
        active_projects = self.model.objects.filter(end_date__isnull=True).count()
        completed_projects = self.model.objects.filter(end_date__isnull=False).count()
        stopped_projects = total_projects - active_projects - completed_projects
        
        context['project_status'] = {
            'active': round((active_projects / total_projects) * 100) if total_projects > 0 else 0,
            'completed': round((completed_projects / total_projects) * 100) if total_projects > 0 else 0,
            'stopped': round((stopped_projects / total_projects) * 100) if total_projects > 0 else 0
        }
        
        # محاسبه پیشرفت پروژه‌ها
        projects = self.get_queryset()
        project_progress = []
        for project in projects:
            total_layers = project.projectlayer_set.count()
            completed_layers = project.projectlayer_set.filter(status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            project_progress.append({
                'name': project.name,
                'progress': progress
            })
        context['project_progress'] = project_progress
        
        # محاسبه کیفیت آزمایشات در 6 ماه اخیر
        six_months_ago = timezone.now() - timedelta(days=180)
        
        # محاسبه تعداد آزمایشات تایید شده برای هر ماه
        experiment_quality = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timedelta(days=30 * i)
            
            # تعداد آزمایشات تایید شده در این ماه
            month_approved = ExperimentApproval.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status=ExperimentApproval.APPROVED
            ).count()
            
            # تعداد کل آزمایشات در این ماه
            month_total = ExperimentRequest.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            # محاسبه درصد قبولی
            approval_rate = round((month_approved / month_total) * 100) if month_total > 0 else 0
            
            # اضافه کردن اطلاعات به لیست
            experiment_quality.append({
                'month': month_start.strftime('%Y-%m'),
                'approved_count': month_approved,
                'total_count': month_total,
                'approval_rate': approval_rate
            })
        
        context['experiment_quality'] = experiment_quality
        
        # محاسبه وضعیت مالی (فعلاً تخمینی)
        total_budget = sum(project.budget or 0 for project in self.model.objects.all())
        if total_budget > 0:
            context['financial_status'] = {
                'spent': 60,  # فعلاً تخمینی - 60% کل بودجه
                'remaining': 35,  # فعلاً تخمینی - 35% کل بودجه
                'unexpected': 5  # فعلاً تخمینی - 5% کل بودجه
            }
        else:
            context['financial_status'] = {
                'spent': 0,
                'remaining': 0,
                'unexpected': 0
            }

        return context

class ProfileView(LoginRequiredMixin, generic.UpdateView):
    template_name = "core/profile.html"
    model = models.User
    form_class = forms.UserProfileForm
    success_url = reverse_lazy("profile")
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات پروفایل با موفقیت به‌روزرسانی شد.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from project.models import Project
        # جمع‌آوری پروژه‌های مرتبط با کاربر
        projects = set()
        project_roles = {}
        # مدیر پروژه
        for p in user.managed_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر پروژه')
        # مدیر فنی
        for p in user.technical_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر فنی')
        # مدیر کنترل کیفیت
        for p in user.qc_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر کنترل کیفیت')
        # کارشناس پروژه
        for p in user.project_experts.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('کارشناس پروژه')
        # پروژه‌های قابل دسترسی دستی
        for p in user.accessible_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('دسترسی دستی')
        # ساخت لیست پروژه‌ها با نقش‌ها
        all_user_projects = []
        for p in projects:
            all_user_projects.append({
                'project': p,
                'roles': project_roles.get(p.id, [])
            })
        context['all_user_projects'] = all_user_projects
        context['accessible_projects'] = user.accessible_projects.all()
        context['user_info'] = {
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'national_id': user.national_id,
        }
        return context

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = models.User
    template_name = "core/admin/user_list.html"
    context_object_name = "users"
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return super().get_queryset().select_related().prefetch_related('roles')

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = models.User
    form_class = forms.AdminUserForm
    template_name = "core/admin/user_form.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "کاربر جدید با موفقیت ایجاد شد.")
        return response

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = models.User
    form_class = forms.AdminUserForm
    template_name = "core/admin/user_form.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('password1', None)
        kwargs.pop('password2', None)
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "اطلاعات کاربر با موفقیت به‌روزرسانی شد.")
        return response

@method_decorator(role_required(['ادمین']), name='dispatch')
class AdminUserDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = models.User
    template_name = "core/admin/user_confirm_delete.html"
    success_url = reverse_lazy("admin-user-list")
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "کاربر با موفقیت حذف شد.")
        return response

class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = "core/dashboard.html"

    # تعریف دسترسی‌ها بر اساس نقش و url nameهای درست (سراسری)
    ROLE_ACCESS = {
        'ادمین': [
            {'name': 'مدیریت کاربران', 'url_name': 'admin-user-list'},
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'ایجاد پروژه', 'url_name': 'create-project'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
            {'name': 'ثبت درخواست آزمایش', 'url_name': 'experiment:experiment_request_create'},
            {'name': 'انواع آزمایشات', 'url_name': 'experiment:experiment_type_list'},
            {'name': 'اعلان‌ها', 'url_name': 'experiment:notification_list'},
        ],
        'مدیر عامل موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
            {'name': 'اعلان‌ها', 'url_name': 'experiment:notification_list'},
        ],
        'مدیر فنی موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر کنترل کیفی موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'کارشناس موسسه': [
            {'name': 'پروفایل', 'url_name': 'profile'},
            {'name': 'لیست پروژه‌ها', 'url_name': 'project-list'},
        ],
        # سایر نقش‌ها را به همین صورت اضافه کن...
    }

    # دسترسی‌های هر نقش در هر پروژه (بر اساس داکیومنت)
    PROJECT_ROLE_ACCESS = {
        'مدیر پروژه': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'ویرایش پروژه', 'url_name': 'project-update'},
            {'name': 'لایه‌های پروژه', 'url_name': 'project-layer-list'},
            {'name': 'ابنیه‌های پروژه', 'url_name': 'project-structure-list'},
            {'name': 'درخواست آزمایش', 'url_name': 'experiment:experiment_request_create'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر فنی': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لایه‌های پروژه', 'url_name': 'project-layer-list'},
            {'name': 'ابنیه‌های پروژه', 'url_name': 'project-structure-list'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'مدیر کنترل کیفیت': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'کارشناس پروژه': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
            {'name': 'لیست آزمایشات', 'url_name': 'experiment:experiment_request_list'},
        ],
        'دسترسی دستی': [
            {'name': 'داشبورد پروژه', 'url_name': 'dashboard'},
        ],
    }

    def get_context_data(self, **kwargs):
        from project.models import Project, ProjectLayer
        from experiment.models import ExperimentRequest, Notification, ExperimentApproval
        from django.utils import timezone
        from datetime import timedelta
        context = super().get_context_data(**kwargs)
        user = self.request.user
        roles = user.roles.values_list('name', flat=True)
        context['roles'] = list(roles)
        # --- Global Access (by role) ---
        access_set = set()
        access_list = []
        from django.urls import reverse, NoReverseMatch
        for role in roles:
            for item in self.ROLE_ACCESS.get(role, []):
                key = (item['name'], item['url_name'])
                if key not in access_set:
                    try:
                        url = reverse(item['url_name'])
                    except NoReverseMatch:
                        url = "#"
                    access_list.append({'name': item['name'], 'url': url})
                    access_set.add(key)
        context['access'] = access_list
        context['user_info'] = {
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'national_id': user.national_id,
        }
        # --- User Projects & Roles ---
        projects = set()
        project_roles = {}
        for p in user.managed_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر پروژه')
        for p in user.technical_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر فنی')
        for p in user.qc_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('مدیر کنترل کیفیت')
        for p in user.project_experts.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('کارشناس پروژه')
        for p in user.accessible_projects.all():
            projects.add(p)
            project_roles.setdefault(p.id, []).append('دسترسی دستی')
        user_projects = []
        for p in projects:
            roles_in_project = project_roles.get(p.id, [])
            accesses = []
            for role in roles_in_project:
                for item in self.PROJECT_ROLE_ACCESS.get(role, []):
                    try:
                        url = reverse(item['url_name'], kwargs={'pk': p.id})
                    except Exception:
                        try:
                            url = reverse(item['url_name'])
                        except Exception:
                            url = "#"
                    accesses.append({'name': item['name'], 'url': url})
            seen = set()
            unique_accesses = []
            for a in accesses:
                if a['name'] not in seen:
                    unique_accesses.append(a)
                    seen.add(a['name'])
            # --- Calculate project progress ---
            total_layers = ProjectLayer.objects.filter(project=p).count()
            completed_layers = ProjectLayer.objects.filter(project=p, status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            user_projects.append({
                'id': p.id,
                'name': p.name,
                'roles': roles_in_project,
                'accesses': unique_accesses,
                'status': 'active' if not p.end_date else 'completed',
                'progress': progress,
            })
        context['user_projects'] = user_projects
        # --- KPI: Project Status ---
        all_projects = Project.objects.all()
        total_projects = all_projects.count()
        active_projects = all_projects.filter(end_date__isnull=True).count()
        completed_projects = all_projects.filter(end_date__isnull=False).count()
        stopped_projects = total_projects - active_projects - completed_projects
        context['project_status_kpi'] = {
            'active': round((active_projects / total_projects) * 100) if total_projects > 0 else 0,
            'completed': round((completed_projects / total_projects) * 100) if total_projects > 0 else 0,
            'stopped': round((stopped_projects / total_projects) * 100) if total_projects > 0 else 0
        }
        # --- KPI: Project Progress (average of all) ---
        all_progress = []
        for p in all_projects:
            total_layers = ProjectLayer.objects.filter(project=p).count()
            completed_layers = ProjectLayer.objects.filter(project=p, status=ProjectLayer.COMPLETED).count()
            progress = round((completed_layers / total_layers) * 100) if total_layers > 0 else 0
            all_progress.append(progress)
        context['project_progress_kpi'] = round(sum(all_progress) / len(all_progress)) if all_progress else 0
        # Add remaining for chart
        context['project_progress_kpi_remaining'] = 100 - context['project_progress_kpi']
        # --- KPI: Financial (dummy, can be replaced with real) ---
        total_budget = sum([p.budget or 0 for p in all_projects])
        context['financial_kpi'] = {
            'spent': 60 if total_budget else 0,
            'remaining': 35 if total_budget else 0,
            'unexpected': 5 if total_budget else 0
        }
        # --- KPI: Experiment Quality (last 6 months) ---
        six_months_ago = timezone.now() - timedelta(days=180)
        experiment_quality = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (i + 1))
            month_end = timezone.now() - timedelta(days=30 * i)
            month_approved = ExperimentApproval.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status=ExperimentApproval.APPROVED
            ).count()
            month_total = ExperimentRequest.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            approval_rate = round((month_approved / month_total) * 100) if month_total > 0 else 0
            experiment_quality.append({
                'month': month_start.strftime('%Y-%m'),
                'approved_count': month_approved,
                'total_count': month_total,
                'approval_rate': approval_rate
            })
        context['experiment_quality_kpi'] = experiment_quality
        # Add last month approval rate and remaining for chart
        if experiment_quality:
            last = experiment_quality[-1]
            context['experiment_quality_last_approval_rate'] = last.get('approval_rate', 0)
            context['experiment_quality_last_remaining'] = 100 - last.get('approval_rate', 0)
        else:
            context['experiment_quality_last_approval_rate'] = 0
            context['experiment_quality_last_remaining'] = 100
        # --- User's Latest Projects (limit 5, with progress) ---
        latest_projects = sorted(user_projects, key=lambda x: x['progress'], reverse=True)[:5]
        context['latest_projects'] = latest_projects
        # --- User's Latest Experiment Requests (limit 5) ---
        user_experiment_requests = ExperimentRequest.objects.filter(user=user).order_by('-created_at')[:5]
        context['latest_experiments'] = [
            {
                'project': er.project.name,
                'order': er.order,
                'type': er.experiment_type.name,
                'status': er.get_status_display(),
                'created_at': er.created_at,
                'request_file': er.request_file.url if er.request_file else None
            }
            for er in user_experiment_requests
        ]
        # --- User's Unread Notifications (limit 5) ---
        user_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
        context['notifications'] = [
            {
                'message': n.message,
                'created_at': n.created_at,
                'experiment': n.experiment_request.project.name if n.experiment_request else None
            }
            for n in user_notifications
        ]
        return context

