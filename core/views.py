from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q, Count, Case, When, Value, IntegerField, F, Sum
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.urls import reverse
import google.genai as genai
import os
import json
from datetime import timedelta
from .models import Contact, Project, Article, LearningResource, Comment
from coding_challenges.models import Challenge as CodeChallenge
from lms.models import Course
from .forms import ProjectForm, ProjectFilterForm, ArticleForm, CommentForm, ArticleQuickForm, ProjectQuickForm, ContactForm
from django.core.mail import mail_admins
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_gemini_chat():
    try:
        if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
            print("GEMINI_API_KEY not found in settings")
            return None
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])
        
        CHAT_INSTRUCTIONS = """
        You are OnPoint Software's AI assistant. You help users with information about OnPoint Software's services.
        
        About OnPoint Software:
        - Custom software development
        - Website design & development
        - Mobile app development
        - GitHub README writing & editing
        - 7+ years of experience
        
        Company Information:
        - Email: onpointinfo635@gmail.com
        - Phone: +254 702 502 952
        Products:
          -we came up with point of sale system called biz flow 
          refer to this link to get more details https://onpointsoft.pythonanywhere.com/bizflow_pos/docs/
          -templates for websites
          refer to this link to get more details https://onpointsoft.pythonanywhere.com/templates/
        Be helpful, professional, and concise in your responses.
        If you don't know an answer, say you'll have someone from the team contact them.
        """
        
        # Initialize chat with instructions
        chat.send_message(CHAT_INSTRUCTIONS)
        return chat
        
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        return None

def home(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Save to database
        contact = Contact(name=name, email=email, message=message)
        contact.save()
        
        # Send email
        try:
            send_mail(
                f'New Contact Form Submission from {name}',
                f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
        except Exception as e:
            print(f"Error sending email: {e}")
            messages.error(request, 'There was an error sending your message. Please try again later.')
        
        return redirect('home')
    
    # Get featured projects for portfolio section
    featured_projects = Project.objects.filter(status__in=['completed', 'launched']).order_by('-created_at')[:6]
    
    # Get all completed/launched projects for stats
    all_projects = Project.objects.filter(status__in=['completed', 'launched'])
    
    # Get the 3 most recent articles for blog section
    latest_articles = Article.objects.filter(status='published').order_by('-created_at')[:3]

    # Get sample coding challenges (latest 3)
    sample_challenges = CodeChallenge.objects.all().order_by('-created_at')[:3]

    # Get sample LMS courses (published, latest 3)
    sample_courses = Course.objects.filter(published=True).order_by('-created_at')[:3]
    
    # Calculate dynamic stats
    stats = {
        'years_experience': 5,  # You can make this dynamic based on your start date
        'projects_delivered': all_projects.count(),
        'client_satisfaction': 98,  # You can calculate this from testimonials/ratings
        'team_members': 8,  # Update based on your actual team size
    }
    
    context = {
        'projects': featured_projects,
        'stats': stats,
        'latest_articles': latest_articles,
        'sample_challenges': sample_challenges,
        'sample_courses': sample_courses,
    }
    for project in featured_projects:
        print(project)
    return render(request, 'core/home.html', context)
def about(request):
    return render(request, 'core/about-us.html')

def signup(request):
    """User registration view using Django's UserCreationForm."""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form, 'title': 'Create Account'})
def mobile_development(request):
    return render(request, 'core/mobile-development.html')

def services_pricing(request):
    return render(request, 'core/services-pricing.html')
def custom_software_development(request):
    return render(request, 'core/custom-software-development.html')
def web_development(request):
    return render(request, 'core/web-development.html')
def github_readme(request):
    return render(request, 'core/github-readme.html')
def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save to database
                contact = form.save()
                
                # Send notification email to admin
                subject = f'New Contact Form Submission from {contact.name}'
                admin_message = f"""
New contact form submission received:

Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone or 'Not provided'}
Message: {contact.message}

Please respond promptly.
                """
                
                send_mail(
                    subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                
                # Send confirmation email to user
                user_subject = 'Thank you for contacting OnPoint Software Solutions'
                user_message = f"""
Dear {contact.name},

Thank you for reaching out to OnPoint Software Solutions. We have received your message and will get back to you within 24 hours.

Your message:
{contact.message}

Best regards,
OnPoint Software Solutions Team
Email: onpointinfo635@gmail.com
Phone: +254 702 502 952
                """
                
                send_mail(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [contact.email],
                    fail_silently=True,  # Don't fail if user email fails
                )
                
                messages.success(request, 'Thank you for your message! We\'ll get back to you within 24 hours.')
                return redirect('contact_us')
                
            except Exception as e:
                logger.error(f"Contact form error: {str(e)}")
                messages.error(request, 'Sorry, there was an error sending your message. Please try again or contact us directly.')
        else:
            # Form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = ContactForm()
    
    return render(request, 'core/contact-us.html', {'form': form})
from django.views.decorators.csrf import ensure_csrf_cookie

@require_http_methods(["POST"])
@ensure_csrf_cookie
def chat_api(request):
    if not request.body:
        return JsonResponse({'error': 'No data provided'}, status=400)
    
    try:
        # Get the message from the request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
        else:
            user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)
        
        # Get or create chat session
        chat = get_gemini_chat()
        if not chat:
            return JsonResponse({
                'response': 'Chat service is currently unavailable. Please contact us directly at onpointinfo635@gmail.com',
                'error': 'Gemini not initialized',
                'status': 'error'
            }, status=503)
        
        # Get response from Gemini
        response = chat.send_message(user_message)
        
        # Create response with new CSRF token if needed
        response_data = {
            'response': response.text,
            'status': 'success',
        }
        
        # Get new CSRF token if this is a new session
        from django.middleware.csrf import get_token
        response_data['csrf_token'] = get_token(request) if request.user.is_anonymous else ''
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        error_message = str(e)
        print(f"Error in chat_api: {error_message}")
        
        # Handle specific Gemini API errors
        if "quota" in error_message.lower():
            return JsonResponse({
                'response': 'Our chat service is currently experiencing high demand. Please try again later or contact us directly at onpointinfo635@gmail.com',
                'error': 'API quota exceeded',
                'status': 'error'
            }, status=429)
            
        return JsonResponse({
            'response': 'Sorry, I encountered an error. Please try again later or contact us directly at onpointinfo635@gmail.com',
            'error': error_message,
            'status': 'error'
        }, status=500)


# Duplicate home function removed - using the first home function with projects


# Admin Views
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is staff member"""
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        return HttpResponseForbidden("You don't have permission to access this page.")


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    """Admin dashboard view showing project statistics and recent activities"""
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Project statistics
        projects = Project.objects.all()
        total_projects = projects.count()
        active_projects = projects.filter(status__in=['in_progress', 'on_hold']).count()
        completed_projects = projects.filter(status__in=['completed', 'launched']).count()
        planning_projects = projects.filter(status='planning').count()
        
        # Project status distribution with proper formatting
        status_stats = {}
        for status_code, status_label in Project.STATUS_CHOICES:
            count = projects.filter(status=status_code).count()
            percentage = (count * 100.0 / total_projects) if total_projects > 0 else 0
            status_stats[status_code] = {
                'count': count,
                'percentage': percentage,
                'label': status_label
            }
        
        # Article statistics
        articles = Article.objects.all()
        total_articles = articles.count()
        published_articles = articles.filter(status='published').count()
        draft_articles = articles.filter(status='draft').count()
        total_views = articles.aggregate(total_views=Sum('view_count'))['total_views'] or 0
        
        # Recent activities
        recent_projects = projects.order_by('-created_at')[:5]
        recent_articles = articles.order_by('-created_at')[:5]
        
        # Monthly statistics (last 30 days)
        from datetime import datetime, timedelta
        last_month = datetime.now() - timedelta(days=30)
        
        new_projects_month = projects.filter(created_at__gte=last_month).count()
        new_articles_month = articles.filter(created_at__gte=last_month).count()
        
        # Growth calculations
        projects_growth = 0
        articles_growth = 0
        if total_projects > 0:
            projects_growth = (new_projects_month * 100.0 / total_projects)
        if total_articles > 0:
            articles_growth = (new_articles_month * 100.0 / total_articles)
        
        context.update({
            # Project stats
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'planning_projects': planning_projects,
            'status_stats': status_stats,
            'recent_projects': recent_projects,
            
            # Article stats
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': draft_articles,
            'total_views': total_views,
            'recent_articles': recent_articles,
            
            # Growth stats
            'new_projects_month': new_projects_month,
            'new_articles_month': new_articles_month,
            'projects_growth': round(projects_growth, 1),
            'articles_growth': round(articles_growth, 1),
            
            'title': 'Dashboard',
        })
        
        return context


class ProjectListView(StaffRequiredMixin, ListView):
    """List all projects with filtering and pagination"""
    model = Project
    template_name = 'admin/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Project.objects.all().order_by('-created_at')
        
        # Apply filters
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        featured = self.request.GET.get('featured')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category=category)
        if featured == 'on':
            queryset = queryset.filter(featured=True)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(client__icontains=search) |
                Q(technologies__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ProjectFilterForm(self.request.GET or None)
        context['title'] = 'Projects'
        return context


class ProjectCreateView(StaffRequiredMixin, CreateView):
    """Create a new project"""
    model = Project
    form_class = ProjectForm
    template_name = 'admin/project_form.html'
    success_url = reverse_lazy('project_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Project'
        return context
    
    def form_valid(self, form):
        # Auto-generate slug if not provided or empty
        if not form.instance.slug or form.instance.slug.strip() == '':
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(form.instance.title)
            # Ensure uniqueness by checking existing slugs
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            form.instance.slug = slug
        
        messages.success(self.request, 'Project created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class ProjectDetailView(StaffRequiredMixin, DetailView):
    """View project details"""
    model = Project
    template_name = 'admin/project_detail.html'
    context_object_name = 'project'
    slug_field = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        return context


class ProjectUpdateView(StaffRequiredMixin, UpdateView):
    """Update an existing project"""
    model = Project
    form_class = ProjectForm
    template_name = 'admin/project_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.title}'
        context['project'] = self.object
        return context
    
    def get_success_url(self):
        messages.success(self.request, 'Project updated successfully!')
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Debug: Check featured field
        print(f"DEBUG UPDATE: Featured field in form.cleaned_data: {form.cleaned_data.get('featured')}")
        print(f"DEBUG UPDATE: Featured field in form.instance: {form.instance.featured}")
        print(f"DEBUG UPDATE: Featured field in POST data: {self.request.POST.get('featured')}")
        
        # Note: Project model doesn't have updated_by field, using updated_at auto field
        result = super().form_valid(form)
        
        # Debug: Check if it was saved
        print(f"DEBUG UPDATE: Featured field after save: {self.object.featured}")
        return result


class ProjectDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a project"""
    model = Project
    template_name = 'admin/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Project deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ProjectStatusUpdateView(StaffRequiredMixin, View):
    """Update project status via AJAX"""
    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return JsonResponse({'error': 'Invalid request'}, status=400)
            
        project = get_object_or_404(Project, pk=kwargs['pk'])
        new_status = request.POST.get('status')
        
        if new_status in dict(Project.STATUS_CHOICES).keys():
            project.status = new_status
            project.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Status updated to {project.get_status_display()}',
                'status_display': project.get_status_display(),
                'status_class': project.status
            })
        
        return JsonResponse({'error': 'Invalid status'}, status=400)


# Comment Management Views
class CommentListView(StaffRequiredMixin, ListView):
    """
    View for listing all comments with filtering and moderation options.
    """
    model = Comment
    template_name = 'admin/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status', '')
        
        if status == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
            
        return queryset.select_related('article', 'user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', 'all')
        context['pending_count'] = Comment.objects.filter(is_approved=False).count()
        return context


class CommentApproveView(StaffRequiredMixin, View):
    """
    View for approving a comment.
    """
    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        comment.is_approved = True
        comment.save(update_fields=['is_approved', 'updated_at'])
        
        messages.success(request, 'Comment has been approved and published.')
        return redirect('comment_list')


class CommentDeleteView(StaffRequiredMixin, DeleteView):
    """
    View for deleting a comment.
    """
    model = Comment
    template_name = 'admin/comment_confirm_delete.html'
    success_url = reverse_lazy('comment_list')
    
    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        messages.success(request, 'Comment has been deleted successfully.')
        return redirect(self.success_url)


# API Views
class ProjectStatsAPIView(StaffRequiredMixin, View):
    """API endpoint for project statistics"""
    def get(self, request, *args, **kwargs):
        # Get counts for different statuses
        status_counts = Project.objects.aggregate(
            total=Count('id'),
            completed=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
            in_progress=Count(Case(When(status='in_progress', then=1), output_field=IntegerField())),
            on_hold=Count(Case(When(status='on_hold', then=1), output_field=IntegerField())),
            cancelled=Count(Case(When(status='cancelled', then=1), output_field=IntegerField())),
        )
        
        # Get monthly project counts for the last 6 months
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_counts = Project.objects.filter(
            created_at__gte=six_months_ago
        ).extra({
            'month': "date_trunc('month', created_at)"
        }).values('month').annotate(count=Count('id')).order_by('month')
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'status_counts': status_counts,
                'monthly_counts': list(monthly_counts)
            }
        })


class RecentProjectsAPIView(StaffRequiredMixin, ListView):
    """API endpoint for recent projects"""
    model = Project
    context_object_name = 'projects'
    template_name = 'admin/includes/recent_projects.html'
    
    def get_queryset(self):
        return Project.objects.order_by('-created_at')[:5]
    
    def render_to_response(self, context, **response_kwargs):
        projects = []
        for project in context['projects']:
            projects.append({
                'id': project.id,
                'title': project.title,
                'status': project.status,
                'status_display': project.get_status_display(),
                'created_at': project.created_at.strftime('%b %d, %Y'),
                'url': reverse_lazy('project_detail', kwargs={'pk': project.pk})
            })
        
        return JsonResponse({
            'status': 'success',
            'data': projects
        })
def public_article_list(request):
    """
    Public view for displaying published articles with pagination and featured article.
    """
    # Get all published articles, ordered by creation date (newest first)
    articles_list = Article.objects.filter(status='published').order_by('-created_at')
    
    # Get the featured article (most recent published article)
    featured_article = articles_list.first()
    
    # If we have a featured article, exclude it from the main articles list
    if featured_article:
        articles_list = articles_list.exclude(pk=featured_article.pk)
    
    # Pagination - 9 articles per page
    page = request.GET.get('page', 1)
    paginator = Paginator(articles_list, 9)
    
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)
    
    return render(request, 'core/article_list.html', {
        'featured_article': featured_article,
        'articles': articles,
        'page_obj': articles,  # For pagination controls
        'is_admin': False
    })

def admin_article_list(request):
    """
    Admin view for managing all articles (both published and unpublished).
    """
    # Get all articles, ordered by creation date (newest first)
    articles = Article.objects.all().order_by('-created_at')
    
    # Calculate statistics
    total_articles = articles.count()
    published_articles = articles.filter(status='published').count()
    draft_articles = articles.filter(status='draft').count()
    total_views = articles.aggregate(total_views=Sum('view_count'))['total_views'] or 0
    
    return render(request, 'admin/article_list_modern.html', {
        'articles': articles,
        'is_admin': True,
        # Individual statistics for template
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'total_views': total_views,
        # Also keep stats dict for potential future use
        'stats': {
            'total': total_articles,
            'published': published_articles,
            'drafts': draft_articles,
            'total_views': total_views,
        }
    })
def admin_article_detail(request, pk):
    """
    Admin view for displaying article details with admin controls.
    """
    article = get_object_or_404(Article, pk=pk)
    
    # Get related articles (excluding current article)
    related_articles = Article.objects.filter(
        status='published'
    ).exclude(pk=article.pk).order_by('-created_at')[:3]
    
    # Get next and previous articles for navigation
    next_article = Article.objects.filter(
        created_at__gt=article.created_at
    ).order_by('created_at').first()
    
    prev_article = Article.objects.filter(
        created_at__lt=article.created_at
    ).order_by('-created_at').first()
    
    # Get comments for the article
    comments = article.comments.all().order_by('created_at')
    
    # Increment view count
    article.view_count = F('view_count') + 1
    article.save(update_fields=['view_count'])
    article.refresh_from_db()
    
    return render(request, 'admin/article_detail.html', {
        'article': article,
        'related_articles': related_articles,
        'next_article': next_article,
        'prev_article': prev_article,
        'comments': comments,
        'is_admin': True
    })

def article_detail(request, slug=None, pk=None):
    """
    Public view for displaying a single article. Can be accessed by either slug or primary key.
    If both are provided, slug takes precedence.
    """
    article = None
    
    # Try to get article by slug first (preferred method for public URLs)
    if slug is not None:
        article = get_object_or_404(Article, slug=slug, status='published')
    # Fall back to primary key if slug is not provided
    elif pk is not None:
        article = get_object_or_404(Article, pk=pk, status='published')
    else:
        raise Http404("Article not found")
        
    # If the article was found by slug but the URL used a primary key,
    # redirect to the canonical slug URL for SEO
    if pk is not None and slug is None and article.slug:
        from django.shortcuts import redirect
        return redirect('article_detail_by_slug', slug=article.slug, permanent=True)
    
    # For admin views, check permissions
    is_admin_view = request.path.startswith('/admin/')
    if is_admin_view and not request.user.is_staff:
        raise PermissionDenied
    
    # Track article view
    article.increment_view_count()
    
    # Get related articles (excluding current article)
    related_articles = Article.objects.filter(
        status='published'
    ).exclude(pk=article.pk).order_by('-published_at')[:3]
    
    # Get comments for the article (active only for non-staff)
    comments = article.comments.all()
    if not request.user.is_staff:
        comments = comments.filter(is_active=True)
    
    # Get comment form
    comment_form = get_comment_form(request)
    
    # Determine the template to use
    template = 'core/article_detail.html'
    if request.path.startswith('/admin/'):
        template = 'admin/article_detail.html'
    
    # Prepare context
    context = {
        'article': article,
        'related_articles': related_articles,
        'comments': comments,
        'comment_form': comment_form,
        'is_admin': request.path.startswith('/admin/'),
    }
    
    # Add Open Graph and Twitter Card meta tags
    if article.title:
        context['og_title'] = article.title
        context['twitter_title'] = article.title
    else:
        context['og_title'] = f"{article.title} | OnPoint Software Solutions"
        context['twitter_title'] = article.title
    
    if article.short_description:
        context['og_description'] = article.short_description
        context['twitter_description'] = article.short_description
    elif article.short_description:
        context['og_description'] = article.short_description
        context['twitter_description'] = article.short_description
    
    # Add article image if available
    if hasattr(article, 'image') and article.image:
        context.update({
            'og_image': request.build_absolute_uri(article.image.url),
            'twitter_image': request.build_absolute_uri(article.image.url),
        })
    
    return render(request, template, context)
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            if not article.author:
                article.author = request.user
            article.save()
            messages.success(request, 'Article created successfully!')
            return redirect('admin_article_detail', pk=article.pk)
    else:
        form = ArticleForm()
    
    return render(request, 'admin/article_form.html', {
        'form': form,
        'title': 'Create New Article',
        'article': None,
    })

def article_quick_create(request):
    """
    Minimal quick-add view for creating an Article with only essential fields.
    Uses ArticleQuickForm and redirects to full edit view after creation.
    """
    if request.method == 'POST':
        form = ArticleQuickForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            # Default author to current user if available
            if not getattr(article, 'author', None):
                article.author = request.user
            # Ensure a slug exists and is unique
            if not getattr(article, 'slug', None) or (article.slug or '').strip() == '':
                from django.utils.text import slugify
                base_slug = slugify(article.title)
                slug = base_slug
                counter = 1
                while Article.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                article.slug = slug
            # Default status to draft for quick adds
            if not getattr(article, 'status', None):
                article.status = 'draft'
            article.save()
            messages.success(request, 'Article created successfully! You can now add more details.')
            return redirect('admin_article_update', pk=article.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ArticleQuickForm()
    return render(request, 'admin/article_quick_form.html', {
        'form': form,
        'title': 'Quick Add Article',
    })

def project_quick_create(request):
    """
    Minimal quick-add view for creating a Project with only essential fields.
    Uses ProjectQuickForm and redirects to full edit view after creation.
    """
    if request.method == 'POST':
        form = ProjectQuickForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            # Auto-generate slug if missing
            if not getattr(project, 'slug', None) or (project.slug or '').strip() == '':
                from django.utils.text import slugify
                base_slug = slugify(project.title)
                slug = base_slug
                counter = 1
                while Project.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                project.slug = slug
            # Provide sensible defaults
            if not getattr(project, 'status', None):
                project.status = 'planning'
            project.save()
            messages.success(request, 'Project created successfully! You can now add more details.')
            return redirect('project_update', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectQuickForm()
    return render(request, 'admin/project_quick_form.html', {
        'form': form,
        'title': 'Quick Add Project',
    })
def article_update(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            article = form.save()
            messages.success(request, 'Article updated successfully!')
            return redirect('admin_article_detail', pk=article.pk)
    else:
        form = ArticleForm(instance=article)
    
    return render(request, 'admin/article_form.html', {
        'form': form,
        'title': f'Edit Article: {article.title}',
        'article': article
    })
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        try:
            article_title = article.title
            article.delete()
            messages.success(request, f'Article "{article_title}" was deleted successfully.')
            return redirect('admin_article_list')
        except Exception as e:
            messages.error(request, f'Error deleting article: {str(e)}')
            return redirect('admin_article_detail', pk=article.pk)
    
    # For GET requests, render a confirmation page
    return render(request, 'core/article_confirm_delete.html', {
        'article': article,
    })


def add_comment(request, pk):
    """
    View for adding a new comment to an article.
    Handles both authenticated and anonymous users.
    """
    article = get_object_or_404(Article, pk=pk)
    
    # Check if comments are closed
    if hasattr(article, 'comments_closed') and article.comments_closed and not request.user.is_staff:
        messages.error(request, 'Comments are closed for this article.')
        return redirect('article_detail', pk=article.pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, request=request)
        if form.is_valid():
            # Save the comment with the article and author
            comment = form.save(commit=False)
            comment.article = article
            
            # Set the author if user is authenticated
            if request.user.is_authenticated:
                comment.author = request.user
            
            # Save the comment (this will handle is_active based on form and user permissions)
            comment.save()
            
            # Send notification to admin for new comments that need moderation
            if not comment.is_active and hasattr(settings, 'ADMINS') and settings.ADMINS:
                try:
                    mail_admins(
                        f'New Comment Awaiting Moderation: {article.title}',
                        f'A new comment has been posted on "{article.title}" and is awaiting moderation.\n\n'
                        f'Comment by: {comment.author.username if comment.author else "Anonymous"}\n'
                        f'Comment: {comment.text[:200]}{"..." if len(comment.text) > 200 else ""}\n\n'
                        f'Approve: {request.build_absolute_uri(reverse("admin:core_comment_changelist") + "?is_active__exact=0")}',
                        fail_silently=True,
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Error sending comment notification email: {e}')
            
            messages.success(
                request, 
                'Your comment has been submitted.' + 
                (' It will be visible after moderation.' if not comment.is_active else '')
            )
            
            # Redirect to the article's comment section
            return redirect(f"{reverse('article_detail', kwargs={'pk': article.pk})}#comment-{comment.id}")
        else:
            # If form is invalid, save the form data in session to repopulate on redirect
            request.session['comment_form_data'] = request.POST
            request.session['comment_form_errors'] = form.errors.get_json_data()
            messages.error(request, 'There was an error with your submission. Please correct the errors below.')
    
    # Redirect back to the article (handles both GET and invalid POST)
    return redirect(f"{reverse('article_detail', kwargs={'pk': article.pk})}#comment-form")


def get_comment_form(request, article_id=None):
    """Helper function to get a comment form with proper initial data"""
    initial = {}
    
    # Set initial data for authenticated users
    if request.user.is_authenticated:
        initial.update({
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })
    
    # Get any saved form data from session (for repopulating after validation errors)
    form_data = request.session.pop('comment_form_data', None)
    
    if form_data:
        form = CommentForm(form_data, request=request)
        # Manually set errors from session
        if 'comment_form_errors' in request.session:
            form._errors = request.session.pop('comment_form_errors')
    else:
        form = CommentForm(initial=initial, request=request)
    
    return form


def learning_resource_list(request):
    """
    View for displaying a paginated list of published learning resources.
    Supports filtering by resource type and search functionality.
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from .models import LearningResource
    
    # Get filter parameters from request
    resource_type = request.GET.get('type', '').lower()
    search_query = request.GET.get('q', '').strip()
    
    # Start with base queryset of published resources
    resources = LearningResource.objects.filter(status='published')
    
    # Apply filters
    if resource_type and resource_type in dict(LearningResource.RESOURCE_TYPE_CHOICES):
        resources = resources.filter(resource_type=resource_type)
    
    # Apply search
    if search_query:
        resources = resources.filter(
            Q(title__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Order by most recently published first
    resources = resources.order_by('-published_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(resources, 10)  # 10 items per page
    
    try:
        resources = paginator.page(page)
    except PageNotAnInteger:
        resources = paginator.page(1)
    except EmptyPage:
        resources = paginator.page(paginator.num_pages)
    
    # Get resource type counts for filter sidebar
    type_counts = LearningResource.objects.filter(status='published')\
        .values('resource_type')\
        .annotate(count=models.Count('resource_type'))
    
    # Convert to a dictionary for easier template access
    type_counts_dict = {item['resource_type']: item['count'] for item in type_counts}
    
    context = {
        'learning_resources': resources,  # Changed from 'resources' to match template
        'search_query': search_query,
        'selected_type': resource_type,
        'type_counts': type_counts_dict,
        'resource_types': dict(LearningResource.RESOURCE_TYPE_CHOICES),
        'is_paginated': resources.has_other_pages(),
        'page_obj': resources,
    }
    
    return render(request, 'core/learning_resource_list.html', context)


def learning_resource_detail(request, slug):
    """View for displaying a single learning resource."""
    resource = get_object_or_404(LearningResource, slug=slug, status='published')
    
    # Increment view count
    resource.increment_view_count()
    
    # Get related resources (excluding current resource)
    related_resources = LearningResource.objects.filter(
        status='published'
    ).exclude(id=resource.id).order_by('?')[:3]  # Get 3 random related resources
    
    context = {
        'resource': resource,
        'related_resources': related_resources,
    }
    
    return render(request, 'core/learning_resource_detail.html', context)

def bizflow_pos_docs(request):
    return render(request, 'core/bizflow_pos_docs.html')