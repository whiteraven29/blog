import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Category, Tag, Post
from django.utils import timezone

username = os.environ.get('BLOG_ADMIN_USERNAME')
password = os.environ.get('BLOG_ADMIN_PASSWORD')
email = os.environ.get('BLOG_ADMIN_EMAIL', '')

if not username or not password:
    raise RuntimeError(
        'Set BLOG_ADMIN_USERNAME and BLOG_ADMIN_PASSWORD before running seed_posts.py.'
    )

u, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email, 'is_staff': True, 'is_superuser': True},
)
if created:
    u.set_password(password)
    u.save()
    print(f'Created admin user: {username}')

cats = {c.name: c for c in Category.objects.all()}

posts_data = [
    {
        'title': 'SQL Injection: From Basics to Blind',
        'category': 'Offensive Security',
        'tags': ['sqli', 'burpsuite', 'python'],
        'difficulty': 'intermediate',
        'status': 'published',
        'is_featured': True,
        'read_time': 12,
        'excerpt': 'A deep dive into SQL injection attacks — union-based, error-based, blind boolean, and time-based techniques with real-world examples.',
        'content': '## SQL Injection: From Basics to Blind\n\nSQL injection remains one of the most critical vulnerabilities in web applications.\n\n### Union-Based SQLi\n\nWhen error messages are visible, union-based injection extracts data directly. The attacker appends UNION SELECT statements to retrieve data from other tables.\n\n### Blind Boolean SQLi\n\nWhen no output is visible, we infer data character by character using true/false conditions in the query.\n\n### Time-Based Blind SQLi\n\nWhen nothing is returned at all, we use time delays via WAITFOR DELAY or SLEEP functions to determine true/false conditions.\n\n### Automation\n\nTools like sqlmap automate detection and exploitation across all injection types.',
    },
    {
        'title': 'HTB Machine Walkthrough: SSTI to RCE',
        'category': 'CTF Writeups',
        'tags': ['ctf', 'web', 'python'],
        'difficulty': 'advanced',
        'status': 'published',
        'is_featured': True,
        'read_time': 18,
        'excerpt': 'Walkthrough of a HackTheBox machine exploiting a Server-Side Template Injection vulnerability to achieve Remote Code Execution.',
        'content': '## HTB Machine Walkthrough: SSTI to RCE\n\n### Reconnaissance\n\nStarting with an nmap scan to discover open ports and services. Found a Flask application on port 80.\n\n### Identifying SSTI\n\nThe application reflected user input directly. Testing with template syntax like multiplication expression returned computed value — confirming Jinja2 SSTI.\n\n### Exploiting SSTI for RCE\n\nUsing Python class traversal through MRO to reach the os module and execute system commands.\n\n### Privilege Escalation\n\nFound credentials in a config file, pivoted to root via sudo misconfiguration with NOPASSWD on a writable script.',
    },
    {
        'title': 'Building REST APIs with Django DRF',
        'category': 'Web Development',
        'tags': ['django', 'python', 'api'],
        'difficulty': 'intermediate',
        'status': 'published',
        'is_featured': False,
        'read_time': 10,
        'excerpt': 'Step-by-step guide to building a production-ready REST API with Django REST Framework including JWT auth, filtering, and pagination.',
        'content': '## Building REST APIs with Django DRF\n\n### Setup\n\nInstall django, djangorestframework, and djangorestframework-simplejwt via pip.\n\n### Models\n\nDefine your data models with Django ORM — relationships, validators, and custom save logic.\n\n### Serializers\n\nSerializers convert model instances to JSON and validate incoming data. Use ModelSerializer for rapid development.\n\n### Views and Routers\n\nGenericAPIView subclasses provide list, create, retrieve, update, and destroy out of the box. Routers auto-generate URL patterns.\n\n### JWT Authentication\n\nSimpleJWT provides secure stateless authentication with access and refresh token rotation.',
    },
    {
        'title': 'XSS to Account Takeover: A Full Chain',
        'category': 'Offensive Security',
        'tags': ['xss', 'burpsuite', 'javascript'],
        'difficulty': 'intermediate',
        'status': 'published',
        'is_featured': True,
        'read_time': 8,
        'excerpt': 'How a reflected XSS vulnerability can be chained into a full account takeover via cookie theft and CSRF bypass.',
        'content': '## XSS to Account Takeover\n\nCross-site scripting is often underestimated. Here is how a simple XSS can compromise an entire account.\n\n### Cookie Theft\n\nBy injecting script that sends document.cookie to an attacker-controlled server, session tokens can be stolen when HttpOnly is not set.\n\n### Bypassing HttpOnly\n\nWhen HttpOnly is set, target session tokens via XHR requests or WebSocket hijacking to perform actions on behalf of the victim.\n\n### Full Exploitation Chain\n\nFind reflected XSS in a search parameter, steal CSRF token via XHR, then submit a password change request with the stolen token — fully taking over the account.',
    },
    {
        'title': 'React Hooks: A Complete Deep Dive',
        'category': 'Web Development',
        'tags': ['react', 'javascript', 'web'],
        'difficulty': 'intermediate',
        'status': 'published',
        'is_featured': False,
        'read_time': 14,
        'excerpt': 'Master useState, useEffect, useContext, useReducer, and custom hooks with real-world patterns and performance tips.',
        'content': '## React Hooks Deep Dive\n\n### useState\n\nManage local component state declaratively. State updates are batched in React 18 for better performance.\n\n### useEffect\n\nHandle side effects cleanly with a cleanup function. Dependencies array controls when the effect re-runs.\n\n### useContext\n\nShare state across the component tree without prop drilling. Combine with useReducer for a Redux-like pattern.\n\n### Custom Hooks\n\nExtract reusable stateful logic into custom hooks prefixed with "use". This enables clean, testable, and composable code.',
    },
    {
        'title': 'Rust for Systems Programmers',
        'category': 'Programming',
        'tags': ['rust', 'c', 'assembly'],
        'difficulty': 'advanced',
        'status': 'published',
        'is_featured': False,
        'read_time': 20,
        'excerpt': 'Why Rust matters for systems programming: memory safety without GC, zero-cost abstractions, and fearless concurrency.',
        'content': '## Rust for Systems Programmers\n\nRust eliminates memory safety bugs at compile time without sacrificing performance.\n\n### Ownership Model\n\nEvery value has a single owner. When ownership is transferred (moved), the original binding is invalidated — no use-after-free possible.\n\n### Borrowing and Lifetimes\n\nThe borrow checker enforces that references never outlive the data they point to. This eliminates dangling pointers at compile time.\n\n### Zero-Cost Abstractions\n\nRust iterators, closures, and async/await compile down to machine code as efficient as hand-written C.\n\n### Unsafe Rust\n\nFor low-level operations like raw pointer manipulation or FFI, Rust provides an unsafe escape hatch while keeping safe code auditable.',
    },
    {
        'title': 'Nmap: Advanced Network Scanning',
        'category': 'Networking',
        'tags': ['nmap', 'linux'],
        'difficulty': 'beginner',
        'status': 'published',
        'is_featured': False,
        'read_time': 7,
        'excerpt': 'From basic host discovery to advanced OS detection and NSE scripts — a comprehensive nmap reference for penetration testers.',
        'content': '## Nmap: Advanced Network Scanning\n\n### Host Discovery\n\nPing sweeps identify live hosts before port scanning. Use -sn for a no-port-scan discovery phase.\n\n### Port Scanning Techniques\n\nSYN scan (-sS) is fast and stealthy. TCP connect (-sT) works without root. UDP scan (-sU) finds UDP services.\n\n### Service and Version Detection\n\nThe -sV flag probes open ports to determine service versions. Combine with -sC for default NSE scripts.\n\n### NSE Scripting Engine\n\nOver 600 built-in scripts for vulnerability detection, brute forcing, and enumeration. Custom scripts are written in Lua.',
    },
    {
        'title': 'Binary Exploitation: Buffer Overflows 101',
        'category': 'Reverse Engineering',
        'tags': ['c', 'assembly', 'linux'],
        'difficulty': 'advanced',
        'status': 'published',
        'is_featured': True,
        'read_time': 22,
        'excerpt': 'Understand stack-based buffer overflows, control flow hijacking, ret2libc, and ROP chains from the ground up.',
        'content': '## Binary Exploitation: Buffer Overflows 101\n\n### Stack Memory Layout\n\nUnderstanding the stack is fundamental. Local variables, saved registers, and return addresses are laid out predictably.\n\n### Overwriting the Return Address\n\nWhen a buffer lacks bounds checking, writing past its end overwrites the return address, redirecting execution.\n\n### Bypassing Stack Canaries\n\nStack canaries detect overflows at runtime. Bypass techniques include format string leaks and brute force on forked processes.\n\n### ROP Chains\n\nReturn Oriented Programming chains existing code gadgets to achieve arbitrary execution without injecting shellcode — bypassing NX/DEP.',
    },
]

for p in posts_data:
    tag_names = p.pop('tags')
    cat_name = p.pop('category')
    obj, created = Post.objects.get_or_create(
        title=p['title'],
        defaults={**p, 'author': u, 'category': cats[cat_name], 'published_at': timezone.now()}
    )
    if created:
        obj.tags.set([Tag.objects.get(name=t) for t in tag_names if Tag.objects.filter(name=t).exists()])
        print(f'Created: {obj.title}')
    else:
        print(f'Exists: {obj.title}')

print(f'\nTotal posts: {Post.objects.count()}')
