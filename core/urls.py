from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from . import views
from .auth_views import CustomLogoutView, CustomLoginView, custom_login_required

def staff_required(view_func=None, redirect_field_name=None, login_url='home'):
    """
    Decorator for views that checks that the user is logged in and is a staff member,
    redirecting to the home page if necessary.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(login_url)
            if not request.user.is_staff:
                return redirect(login_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func is None:
        return decorator
    return decorator(view_func)

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('chat/', views.chat_api, name='chat_api'),
    
    # Authentication URLs
    path('accounts/login/', CustomLoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        extra_context={'title': 'Login'}
    ), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='admin_logout'),
    path('about/', views.about, name='about'),
    # Authentication
    path('accounts/signup/', views.signup, name='signup'),
    path('mobile-development/', views.mobile_development, name='mobile_development'),
    path('services/', views.services_pricing, name='services_pricing'),
    path('custom-software-development/', views.custom_software_development, name='custom_software_development'),
    path('web-development/', views.web_development, name='web_development'),
    path('github-readme/', views.github_readme, name='github_readme'),
    path('contact-us/', views.contact_us, name='contact_us'),
    # Admin Dashboard URLs (protected by staff_required)
    path('admin/', staff_required(views.AdminDashboardView.as_view()), name='admin_dashboard'),
    
    # Project Management URLs (protected by staff_required)
    path('admin/projects/', staff_required(views.ProjectListView.as_view()), name='project_list'),
    path('admin/projects/create/', staff_required(views.ProjectCreateView.as_view()), name='project_create'),
    path('admin/projects/quick-add/', staff_required(views.project_quick_create), name='project_quick_create'),
    path('admin/projects/<int:pk>/', staff_required(views.ProjectDetailView.as_view()), name='project_detail'),
    path('admin/projects/<int:pk>/update/', staff_required(views.ProjectUpdateView.as_view()), name='project_update'),
    path('admin/projects/<int:pk>/delete/', staff_required(views.ProjectDeleteView.as_view()), name='project_delete'),
    path('admin/projects/<int:pk>/update-status/', staff_required(views.ProjectStatusUpdateView.as_view()), 
         name='project_update_status'),
    
    # Comment Management URLs (protected by staff_required)
    path('admin/comments/', staff_required(views.CommentListView.as_view()), name='comment_list'),
    path('admin/comments/<int:pk>/approve/', staff_required(views.CommentApproveView.as_view()), name='comment_approve'),
    path('admin/comments/<int:pk>/delete/', staff_required(views.CommentDeleteView.as_view()), name='comment_delete'),
    
    # AJAX/API Endpoints
    path('admin/api/project-stats/', staff_required(views.ProjectStatsAPIView.as_view()), name='api_project_stats'),
    path('admin/api/recent-projects/', staff_required(views.RecentProjectsAPIView.as_view()), name='api_recent_projects'),

    # LMS Admin Management
    path('admin/lms/', include('lms.admin_urls')),
    
    # Public Article URLs
    path('blog/', views.public_article_list, name='article_list'),
    path('blog/<slug:slug>/', views.article_detail, name='article_detail_by_slug'),
    path('blog/id/<int:pk>/', views.article_detail, name='article_detail'),
    
    # Article Management URLs (protected by staff_required)
    path('admin/articles/', staff_required(views.admin_article_list), name='admin_article_list'),
    path('admin/articles/create/', staff_required(views.article_create), name='article_create'),
    path('admin/articles/quick-add/', staff_required(views.article_quick_create), name='article_quick_create'),
    path('admin/articles/<int:pk>/', staff_required(views.admin_article_detail), name='admin_article_detail'),
    path('admin/articles/<int:pk>/update/', staff_required(views.article_update), name='admin_article_update'),
    path('admin/articles/<int:pk>/delete/', staff_required(views.article_delete), name='admin_article_delete'),
    path('admin/articles/<int:pk>/add-comment/', staff_required(views.add_comment), name='add_comment'),
    # Learning resources
    path('learning-resources/', views.learning_resource_list, name='learning_resource_list'),
    path('learning-resources/<slug:slug>/', views.learning_resource_detail, name='learning_resource_detail'),
    path('bizflow_pos/docs/', views.bizflow_pos_docs, name='bizflow_pos_docs'),
]
